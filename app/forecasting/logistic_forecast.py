"""Leakage-aware logistic regression probability forecasting.

Research-only model. Predicts after the latest available daily close.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.forecasting.market_features import (
    FEATURE_COLUMNS,
    build_forward_labels,
    build_market_features,
)


@dataclass(frozen=True)
class LogisticForecast:
    horizon_days: int
    probability_up: float
    training_samples: int
    training_start_index: int
    training_end_index: int
    forecast_index: int


def logistic_probability_forecast(
    close_prices: pd.Series,
    forecast_index: int,
    horizon_days: int = 20,
    training_window: int = 756,
    minimum_samples: int = 120,
    regularization_c: float = 0.1,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
) -> LogisticForecast:
    """Predict direction using only information known at forecast_index.

    A training example originating at index i is eligible only when
    i + horizon_days <= forecast_index.

    The scaler and classifier are fitted exclusively on eligible
    historical examples.
    """

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if (
        isinstance(forecast_index, bool)
        or not isinstance(forecast_index, int)
        or forecast_index < 0
        or forecast_index >= len(close_prices)
    ):
        raise ValueError("Invalid forecast_index.")

    if (
        isinstance(horizon_days, bool)
        or not isinstance(horizon_days, int)
        or horizon_days < 1
    ):
        raise ValueError("horizon_days must be a positive integer.")

    if (
        isinstance(training_window, bool)
        or not isinstance(training_window, int)
        or training_window < 1
    ):
        raise ValueError("training_window must be a positive integer.")

    if (
        isinstance(minimum_samples, bool)
        or not isinstance(minimum_samples, int)
        or minimum_samples < 30
    ):
        raise ValueError("minimum_samples must be an integer >= 30.")

    if (
        isinstance(regularization_c, bool)
        or not np.isfinite(regularization_c)
        or regularization_c <= 0
    ):
        raise ValueError("regularization_c must be positive and finite.")

    history = close_prices.iloc[: forecast_index + 1]

    if (
        not isinstance(feature_columns, tuple)
        or not feature_columns
        or any(
            not isinstance(feature, str)
            for feature in feature_columns
        )
        or len(set(feature_columns)) != len(feature_columns)
        or not set(feature_columns).issubset(FEATURE_COLUMNS)
    ):
        raise ValueError(
            "feature_columns must be a nonempty tuple of unique valid features."
        )

    features = build_market_features(history)
    labels = build_forward_labels(history, horizon_days)

    current_features = features.iloc[[forecast_index]][
        list(feature_columns)
    ]

    if not np.isfinite(current_features.to_numpy()).all():
        raise ValueError(
            "Insufficient valid features at forecast_index."
        )

    latest_matured_index = forecast_index - horizon_days

    if latest_matured_index < 0:
        raise ValueError("No matured training outcomes available.")

    earliest_index = max(
        0,
        latest_matured_index - training_window + 1,
    )

    training_features = features.iloc[
        earliest_index : latest_matured_index + 1
    ][list(feature_columns)]

    training_labels = labels.iloc[
        earliest_index : latest_matured_index + 1
    ]

    valid_rows = (
        np.isfinite(training_features.to_numpy()).all(axis=1)
        & training_labels.notna().to_numpy()
    )

    x_train = training_features.iloc[
        np.flatnonzero(valid_rows)
    ]

    y_train = training_labels.iloc[
        np.flatnonzero(valid_rows)
    ].astype(int)

    if len(x_train) < minimum_samples:
        raise ValueError(
            "Insufficient matured, valid training examples."
        )

    if y_train.nunique() < 2:
        raise ValueError(
            "Training outcomes contain only one class."
        )

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=float(regularization_c),
                    l1_ratio=0,
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(x_train, y_train)

    probability_up = float(
        model.predict_proba(current_features)[0, 1]
    )

    valid_indices = np.flatnonzero(valid_rows)

    return LogisticForecast(
        horizon_days=horizon_days,
        probability_up=probability_up,
        training_samples=len(x_train),
        training_start_index=earliest_index + int(valid_indices[0]),
        training_end_index=earliest_index + int(valid_indices[-1]),
        forecast_index=forecast_index,
    )
