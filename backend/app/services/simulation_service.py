import asyncio
import json
import logging
import math
import random
from datetime import datetime, timezone
from typing import Dict, Optional, List
from backend.app.config import SIMULATION_TICK_INTERVAL_SECONDS
from backend.app.models.database import get_connection
from backend.app.services.sensor_validation import (
    validate_sensor_reading,
    MIN_PLAUSIBLE_TEMP_C,
    MAX_PLAUSIBLE_TEMP_C,
)
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
        # Tracks underlying smooth physical temperature per sensor: sensor_id -> float
        self._current_temps: Dict[str, float] = {}

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

            # Retrieve or initialize underlying core physical temperature
            current_core = self._current_temps.get(sensor_id)
            if current_core is None or not (MIN_PLAUSIBLE_TEMP_C <= current_core <= MAX_PLAUSIBLE_TEMP_C):
                if sensor.last_valid_temperature_c is not None and (
                    MIN_PLAUSIBLE_TEMP_C <= sensor.last_valid_temperature_c <= MAX_PLAUSIBLE_TEMP_C
                ):
                    current_core = float(sensor.last_valid_temperature_c)
                else:
                    current_core = baseline_temp + sensor_offset

            # Fault injection scenarios
            if scenario == "disconnected":
                if idx == 0 and step >= 2:
                    is_disconnected = True
                    raw_temp = None
                else:
                    target_temp = baseline_temp + sensor_offset
                    max_step = max(2.2, min(8.0, range_span * 0.38))
                    diff = target_temp - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    raw_temp = round(current_core + noise, 2)
                    self._current_temps[sensor_id] = current_core

            elif scenario == "implausible":
                # Explicit hardware fault injection: sensor 0 outputs unphysical reading
                if idx == 0 and step >= 2:
                    raw_temp = 148.5
                    # Do not contaminate current_core so sensor can smoothly resume when scenario changes
                else:
                    target_temp = baseline_temp + sensor_offset
                    max_step = max(2.2, min(8.0, range_span * 0.38))
                    diff = target_temp - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    raw_temp = round(current_core + noise, 2)
                    self._current_temps[sensor_id] = current_core

            elif scenario == "stuck":
                # Sensor 0 freezes at exact telemetry value
                if idx == 0 and step >= 2:
                    raw_temp = round(current_core, 2)
                else:
                    target_temp = baseline_temp + sensor_offset
                    max_step = max(2.2, min(8.0, range_span * 0.38))
                    diff = target_temp - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    raw_temp = round(current_core + noise, 2)
                    self._current_temps[sensor_id] = current_core

            else:
                # Continuous, demo-optimized smooth thermal progression
                if scenario == "gradual_warming":
                    # Continuously climbs without an artificial ceiling at 10°C,
                    # advancing steadily each tick while bounded safely below physical limits (80°C).
                    step_increment = max(1.8, min(4.5, range_span * 0.3))
                    current_core = current_core + step_increment
                    current_core = min(MAX_PLAUSIBLE_TEMP_C - 5.0, current_core)

                elif scenario == "gradual_cooling":
                    # Continuously drops downwards without an artificial ceiling,
                    # dropping steadily each tick while bounded safely above physical limits (-210°C).
                    step_increment = max(1.8, min(4.5, range_span * 0.3))
                    current_core = current_core - step_increment
                    current_core = max(MIN_PLAUSIBLE_TEMP_C + 5.0, current_core)

                elif scenario == "sudden_spike":
                    # Rapid heat surge into elevated ambient territory (e.g. 25°C-30°C for standard biologic)
                    spike_target = upper_limit + max(12.0, min(30.0, range_span * 2.0)) + sensor_offset
                    max_step = max(4.0, min(14.0, range_span * 0.65))
                    diff = spike_target - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    current_core = min(MAX_PLAUSIBLE_TEMP_C - 5.0, current_core)

                elif scenario == "sudden_drop":
                    # Rapid cooling drop into deep sub-zero territory
                    drop_target = lower_limit - max(12.0, min(30.0, range_span * 2.0)) + sensor_offset
                    max_step = max(4.0, min(14.0, range_span * 0.65))
                    diff = drop_target - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    current_core = max(MIN_PLAUSIBLE_TEMP_C + 5.0, current_core)

                elif scenario == "repeated_fluctuations":
                    # Demo-paced sinusoidal oscillation completing full wave in ~12-15s
                    oscillation = math.sin(step * 0.55) * (range_span * 0.8)
                    target_temp = mid_temp + oscillation + sensor_offset
                    max_step = max(2.5, min(8.0, range_span * 0.4))
                    diff = target_temp - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    current_core = max(MIN_PLAUSIBLE_TEMP_C + 5.0, min(MAX_PLAUSIBLE_TEMP_C - 5.0, current_core))

                else:  # "normal" or recovery mode: smoothly return to baseline in 2-3 ticks
                    target_temp = baseline_temp + sensor_offset
                    max_step = max(2.5, min(8.0, range_span * 0.4))
                    diff = target_temp - current_core
                    step_delta = max(-max_step, min(max_step, diff))
                    current_core = current_core + step_delta
                    current_core = max(MIN_PLAUSIBLE_TEMP_C + 5.0, min(MAX_PLAUSIBLE_TEMP_C - 5.0, current_core))

                self._current_temps[sensor_id] = current_core
                raw_temp = round(current_core + noise, 2)

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
