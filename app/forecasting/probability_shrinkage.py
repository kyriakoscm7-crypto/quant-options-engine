"""Conservative probability shrinkage for forecasting research."""

import numpy as np


def shrink_probabilities(
    model_probabilities,
    reference_probabilities,
    model_weight: float,
) -> np.ndarray:
    """Blend model probabilities with a reference forecast.

    model_weight=0 uses only the reference.
    model_weight=1 uses only the model.

    The weight must be selected without using future evaluation outcomes.
    """

    model = np.asarray(model_probabilities, dtype=float)
    reference = np.asarray(reference_probabilities, dtype=float)

    if model.ndim != 1 or reference.ndim != 1:
        raise ValueError("Probabilities must be one-dimensional.")

    if len(model) == 0 or len(model) != len(reference):
        raise ValueError("Probability arrays must be nonempty and equal length.")

    if not np.isfinite(model).all():
        raise ValueError("Model probabilities must be finite.")

    if not np.isfinite(reference).all():
        raise ValueError("Reference probabilities must be finite.")

    if np.any((model < 0) | (model > 1)):
        raise ValueError("Model probabilities must be between 0 and 1.")

    if np.any((reference < 0) | (reference > 1)):
        raise ValueError("Reference probabilities must be between 0 and 1.")

    if isinstance(model_weight, (bool, np.bool_)):
        raise ValueError("Model weight must be a number between 0 and 1.")

    if not np.isscalar(model_weight):
        raise ValueError("Model weight must be a scalar.")

    try:
        weight = float(model_weight)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Model weight must be numeric.") from exc

    if not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Model weight must be between 0 and 1.")

    return (1 - weight) * reference + weight * model
