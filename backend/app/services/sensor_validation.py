from typing import Optional, List, Tuple
from dataclasses import dataclass

STUCK_CONSECUTIVE_THRESHOLD = 5
MAX_PLAUSIBLE_TEMP_C = 80.0
MIN_PLAUSIBLE_TEMP_C = -210.0
MAX_PHYSICAL_TICK_DELTA_C = 35.0

@dataclass
class ValidationResult:
    quality_status: str  # 'valid', 'stuck', 'disconnected', 'implausible', 'stale'
    is_valid_for_excursion: bool
    diagnostic_reason: Optional[str] = None

def validate_sensor_reading(
    current_temp_c: Optional[float],
    recent_readings_c: List[Optional[float]],
    is_explicitly_disconnected: bool = False,
) -> ValidationResult:
    """
    Validates a raw temperature observation against health, physical plausibility,
    and stuck sensor rules.
    Only returns quality_status == 'valid' when the observation is deemed trustworthy.
    """
    if is_explicitly_disconnected or current_temp_c is None:
        return ValidationResult(
            quality_status="disconnected",
            is_valid_for_excursion=False,
            diagnostic_reason="Sensor telemetry feed dropped or signal interrupted.",
        )

    # Check absolute physical plausibility
    if current_temp_c < MIN_PLAUSIBLE_TEMP_C or current_temp_c > MAX_PLAUSIBLE_TEMP_C:
        return ValidationResult(
            quality_status="implausible",
            is_valid_for_excursion=False,
            diagnostic_reason=f"Implausible temperature reading ({current_temp_c:.1f}°C) exceeds physical operating limits.",
        )

    # Check unphysical instantaneous jump
    if recent_readings_c:
        last_temp = recent_readings_c[-1]
        if last_temp is not None and abs(current_temp_c - last_temp) > MAX_PHYSICAL_TICK_DELTA_C:
            return ValidationResult(
                quality_status="implausible",
                is_valid_for_excursion=False,
                diagnostic_reason=f"Unphysical temperature discontinuity: jumped {abs(current_temp_c - last_temp):.1f}°C in one tick.",
            )

    # Check stuck sensor rule (identical float value for >= STUCK_CONSECUTIVE_THRESHOLD samples)
    if len(recent_readings_c) >= STUCK_CONSECUTIVE_THRESHOLD - 1:
        tail = recent_readings_c[-(STUCK_CONSECUTIVE_THRESHOLD - 1):]
        if all(t is not None and abs(t - current_temp_c) < 1e-4 for t in tail):
            return ValidationResult(
                quality_status="stuck",
                is_valid_for_excursion=False,
                diagnostic_reason=f"Sensor telemetry frozen: identical value ({current_temp_c:.2f}°C) for {STUCK_CONSECUTIVE_THRESHOLD} consecutive cycles.",
            )

    return ValidationResult(
        quality_status="valid",
        is_valid_for_excursion=True,
        diagnostic_reason=None,
    )
