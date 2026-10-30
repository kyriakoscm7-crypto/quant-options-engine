"""Transparent, descriptive market activity screening rules."""

import math

GAP_Z_THRESHOLD = 2.0
RELATIVE_VOLUME_THRESHOLD = 2.0


def _finite_number(value: float | None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    return number if math.isfinite(number) else None


def classify_activity(
    gap_z_score: float | None,
    relative_volume: float | None,
) -> tuple[str, ...]:
    """Return observed activity flags, not return predictions."""

    gap = _finite_number(gap_z_score)
    volume = _finite_number(relative_volume)

    reasons = []

    if gap is not None and abs(gap) >= GAP_Z_THRESHOLD:
        reasons.append("unusual standardized gap")

    if (
        volume is not None
        and volume >= RELATIVE_VOLUME_THRESHOLD
    ):
        reasons.append("elevated trading volume")

    return tuple(reasons)
