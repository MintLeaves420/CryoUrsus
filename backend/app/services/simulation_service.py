import asyncio
import json
import logging
import math
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List
from backend.app.config import SIMULATION_TICK_INTERVAL_SECONDS
from backend.app.models.database import get_connection
from backend.app.services.sensor_validation import validate_sensor_reading
from backend.app.services.excursion_engine import process_reading_for_excursions
from backend.app.services.alert_service import create_or_update_alert
from backend.app.services.shipment_service import get_shipment_by_id, update_shipment_status
from backend.app.api.websocket import ws_manager

logger = logging.getLogger("cryoursus.simulation")

class SimulationService:
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        # Tracks recent readings per sensor to detect stuck values: sensor_id -> List[Optional[float]]
        self._sensor_history: Dict[str, List[Optional[float]]] = {}
        # Step counter for scenario animation per shipment
        self._step_counters: Dict[str, int] = {}

    def is_running(self, shipment_id: str) -> bool:
        task = self._tasks.get(shipment_id)
        return task is not None and not task.done()

    async def start_simulation(self, shipment_id: str) -> bool:
        if self.is_running(shipment_id):
            logger.info("Simulation for %s is already running.", shipment_id)
            return True

        update_shipment_status(shipment_id, "running")
        task = asyncio.create_task(self._run_simulation_loop(shipment_id))
        self._tasks[shipment_id] = task
        logger.info("Started simulation loop for shipment %s", shipment_id)
        return True

    async def pause_simulation(self, shipment_id: str) -> bool:
        if shipment_id in self._tasks:
            task = self._tasks.pop(shipment_id)
            if not task.done():
                task.cancel()
        update_shipment_status(shipment_id, "paused")
        await ws_manager.broadcast(shipment_id, {
            "type": "shipment.status_changed",
            "version": 1,
            "shipment_id": shipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"status": "paused"},
        })
        logger.info("Paused simulation loop for shipment %s", shipment_id)
        return True

    async def resume_simulation(self, shipment_id: str) -> bool:
        shp = get_shipment_by_id(shipment_id)
        if not shp or shp.status == "completed":
            raise ValueError("Completed shipment cannot be resumed.")
        return await self.start_simulation(shipment_id)

    async def end_simulation(self, shipment_id: str) -> bool:
        if shipment_id in self._tasks:
            task = self._tasks.pop(shipment_id)
            if not task.done():
                task.cancel()
        update_shipment_status(shipment_id, "completed")
        await ws_manager.broadcast(shipment_id, {
            "type": "shipment.status_changed",
            "version": 1,
            "shipment_id": shipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"status": "completed"},
        })
        logger.info("Ended simulation for shipment %s", shipment_id)
        return True

    async def _run_simulation_loop(self, shipment_id: str):
        try:
            while True:
                shp = get_shipment_by_id(shipment_id)
                if not shp or shp.status != "running":
                    break

                step = self._step_counters.get(shipment_id, 0)
                self._step_counters[shipment_id] = step + 1

                await self._process_tick(shp, step)
                await asyncio.sleep(SIMULATION_TICK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled for %s", shipment_id)
        except Exception as e:
            logger.error("Error in simulation loop for %s: %s", shipment_id, str(e), exc_info=True)
        finally:
            if shipment_id in self._tasks:
                del self._tasks[shipment_id]

    async def _process_tick(self, shp, step: int):
        profile = shp.profile
        if not profile:
            return

        scenario = shp.scenario
        lower_limit = profile.lower_limit_c
        upper_limit = profile.upper_limit_c
        mid_temp = (lower_limit + upper_limit) / 2.0
        range_span = upper_limit - lower_limit

        params = {}
        if profile.demo_parameters_json:
            try:
                params = json.loads(profile.demo_parameters_json)
            except Exception:
                pass
        baseline_temp = params.get("baseline_temp_c", mid_temp)
        noise_std = params.get("noise_std", 0.15)

        now_iso = datetime.now(timezone.utc).isoformat()

        for idx, sensor in enumerate(shp.sensors):
            sensor_id = sensor.id
            history = self._sensor_history.setdefault(sensor_id, [])

            # Compute simulated raw temperature based on scenario and sensor position
            is_disconnected = False
            raw_temp = None

            # Base variation with slight sensor positional offset
            sensor_offset = (idx - len(shp.sensors) / 2.0) * 0.1
            noise = random.gauss(0, noise_std)

            if scenario == "normal":
                raw_temp = round(baseline_temp + sensor_offset + noise, 2)

            elif scenario == "gradual_warming":
                # Ramps upward from baseline to across upper limit over 8 steps (~12s)
                ramp = (step / 8.0) * (range_span * 1.2)
                raw_temp = round(baseline_temp + ramp + sensor_offset + noise, 2)

            elif scenario == "gradual_cooling":
                # Ramps downward from baseline to across lower limit over 8 steps (~12s)
                ramp = (step / 8.0) * (range_span * 1.2)
                raw_temp = round(baseline_temp - ramp + sensor_offset + noise, 2)

            elif scenario == "sudden_spike":
                # Jumps directly 4.5°C above upper limit
                if step >= 1:
                    raw_temp = round(upper_limit + 4.5 + sensor_offset + noise, 2)
                else:
                    raw_temp = round(baseline_temp + noise, 2)

            elif scenario == "sudden_drop":
                # Drops 4.5°C below lower limit
                if step >= 1:
                    raw_temp = round(lower_limit - 4.5 + sensor_offset + noise, 2)
                else:
                    raw_temp = round(baseline_temp + noise, 2)

            elif scenario == "repeated_fluctuations":
                # Sinusoidal wave crossing upper and lower limits
                oscillation = math.sin(step * 0.4) * (range_span * 0.8)
                raw_temp = round(mid_temp + oscillation + sensor_offset + noise, 2)

            elif scenario == "stuck":
                # Sensor 1 freezes at exactly the same float value
                if idx == 0 and step >= 2:
                    raw_temp = 5.25  # Frozen identical value
                else:
                    raw_temp = round(baseline_temp + sensor_offset + noise, 2)

            elif scenario == "disconnected":
                # Sensor 1 telemetry feed cuts out after step 2
                if idx == 0 and step >= 2:
                    is_disconnected = True
                    raw_temp = None
                else:
                    raw_temp = round(baseline_temp + sensor_offset + noise, 2)

            elif scenario == "implausible":
                # Sensor 1 outputs unphysical 150°C telemetry
                if idx == 0 and step >= 2:
                    raw_temp = 148.5
                else:
                    raw_temp = round(baseline_temp + sensor_offset + noise, 2)

            else:
                raw_temp = round(baseline_temp + sensor_offset + noise, 2)

            # Validate reading
            validation = validate_sensor_reading(
                current_temp_c=raw_temp,
                recent_readings_c=history,
                is_explicitly_disconnected=is_disconnected,
            )

            # Update in-memory history (keep last 10)
            history.append(raw_temp)
            if len(history) > 10:
                history.pop(0)

            # Persist reading and update sensor state in DB
            with get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO readings (
                        shipment_id, sensor_id, timestamp, temperature_c,
                        quality_status, source, scenario, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'simulated', ?, ?)
                    """,
                    (
                        shp.id,
                        sensor_id,
                        now_iso,
                        raw_temp,
                        validation.quality_status,
                        scenario,
                        now_iso,
                    ),
                )
                reading_id = cursor.lastrowid

                # Update sensor health and last valid temperature
                last_valid = raw_temp if validation.is_valid_for_excursion else sensor.last_valid_temperature_c
                conn.execute(
                    """
                    UPDATE sensors
                    SET health_status = ?, last_valid_temperature_c = ?, last_reading_at = ?
                    WHERE id = ?
                    """,
                    (validation.quality_status, last_valid, now_iso, sensor_id),
                )

            # Handle sensor fault alerts if non-healthy
            if not validation.is_valid_for_excursion:
                create_or_update_alert(
                    shipment_id=shp.id,
                    alert_type="sensor_fault",
                    severity="warning",
                    title=f"Sensor Fault on {sensor.label}",
                    message=validation.diagnostic_reason or f"Sensor {sensor_id} entered fault state: {validation.quality_status}.",
                    sensor_id=sensor_id,
                )
            else:
                # If reading is valid, evaluate temperature excursion
                process_reading_for_excursions(
                    shipment_id=shp.id,
                    sensor_id=sensor_id,
                    temperature_c=raw_temp,
                    lower_limit_c=lower_limit,
                    upper_limit_c=upper_limit,
                    timestamp_iso=now_iso,
                    tick_duration_seconds=SIMULATION_TICK_INTERVAL_SECONDS,
                )

            # Broadcast reading created event over WebSocket
            await ws_manager.broadcast(shp.id, {
                "type": "reading.created",
                "version": 1,
                "shipment_id": shp.id,
                "timestamp": now_iso,
                "data": {
                    "id": reading_id,
                    "sensor_id": sensor_id,
                    "sensor_label": sensor.label,
                    "temperature_c": raw_temp,
                    "quality_status": validation.quality_status,
                    "is_valid": validation.is_valid_for_excursion,
                },
            })

simulation_service = SimulationService()
