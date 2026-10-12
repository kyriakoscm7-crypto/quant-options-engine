"""
Interactive 3D Implied Volatility Visualization

Collects SPY option observations across multiple expirations
and displays their implied volatility in three dimensions.

X-axis: Moneyness (strike / underlying price)
Y-axis: Days to expiration
Z-axis: Implied volatility (%)

This is a 3D scatter plot of observed option quotes,
not an interpolated mathematical surface.
"""

import math

import pandas as pd
import plotly.graph_objects as go

from app.market_data.multi_expiration import (
    fetch_multiple_expirations,
)

# ============================================================
# PREPARE VOLATILITY DATA
# ============================================================

def prepare_surface_data(
    df: pd.DataFrame,
    minimum_moneyness: float = 0.95,
    maximum_moneyness: float = 1.05,
) -> pd.DataFrame:
    """
    Prepare option observations for 3D visualization.

    Keeps options within the specified moneyness range.

    Adds DaysToExpiration, calculated from the existing
    TimeToExpiration column.

    Does not change the original DataFrame.
    """

    if not (
        math.isfinite(minimum_moneyness)
        and math.isfinite(maximum_moneyness)
    ):
        raise ValueError(
            "Moneyness limits must be finite."
        )

    if minimum_moneyness <= 0:
        raise ValueError(
            "Minimum moneyness must be positive."
        )

    if maximum_moneyness <= minimum_moneyness:
        raise ValueError(
            "Maximum moneyness must exceed minimum moneyness."
        )

    required_columns = [
        "Moneyness",
        "TimeToExpiration",
        "ImpliedVolatility",
        "Strike",
        "Expiration",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Create a copy to preserve the original dataset.
    prepared = df.copy()

    # Convert numerical columns into numeric values.
    numeric_columns = [
        "Moneyness",
        "TimeToExpiration",
        "ImpliedVolatility",
        "Strike",
    ]

    for column in numeric_columns:
        prepared[column] = pd.to_numeric(
            prepared[column],
            errors="coerce",
        )

    # Remove rows with missing numerical values.
    prepared = prepared.dropna(
        subset=numeric_columns
    )

    # Remove infinite values.
    for column in numeric_columns:
        prepared = prepared[
            prepared[column].map(math.isfinite)
        ]

    # Filter to the selected moneyness range.
    prepared = prepared[
        prepared["Moneyness"].between(
            minimum_moneyness,
            maximum_moneyness,
        )
    ].copy()

    # Reject invalid maturity and volatility values.
    prepared = prepared[
        (prepared["TimeToExpiration"] > 0)
        & (prepared["ImpliedVolatility"] > 0)
    ].copy()

    # Convert maturity from years into calendar days.
    prepared["DaysToExpiration"] = (
        prepared["TimeToExpiration"] * 365.0
    )

    # Sort observations for consistent presentation.
    prepared = prepared.sort_values(
        by=["DaysToExpiration", "Moneyness"]
    ).reset_index(drop=True)

    return prepared


# ============================================================
# BUILD INTERACTIVE 3D CHART
# ============================================================

def create_volatility_surface_chart(
    df: pd.DataFrame,
    ticker_symbol: str = "SPY",
    output_file: str = "volatility_surface_3d.html",
):
    """
    Create an interactive Plotly 3D volatility scatter plot.

    Each marker represents an option observation.

    No interpolation or smoothing is applied.
    """

    if df.empty:
        raise ValueError(
            "Cannot create a volatility chart from empty data."
        )

    # Prepare hover information for each option.
    hover_text = [
        (
            f"Expiration: {row.Expiration}<br>"
            f"Strike: ${row.Strike:.2f}<br>"
            f"Moneyness: {row.Moneyness:.4f}<br>"
            f"Days to Expiration: {row.DaysToExpiration:.2f}<br>"
            f"Implied Volatility: {row.ImpliedVolatility:.2f}%"
        )
        for row in df.itertuples()
    ]

    # Create the interactive 3D scatter plot.
    figure = go.Figure(
        data=[
            go.Scatter3d(
                x=df["Moneyness"],
                y=df["DaysToExpiration"],
                z=df["ImpliedVolatility"],
                mode="markers",
                marker=dict(
                    size=4,
                    color=df["ImpliedVolatility"],
                    colorscale="Viridis",
                    opacity=0.85,
                    colorbar=dict(
                        title="IV (%)"
                    ),
                ),
                text=hover_text,
                hovertemplate="%{text}<extra></extra>",
                name="Option observations",
            )
        ]
    )

    # Configure the chart's appearance.
    figure.update_layout(
        title=(
            f"{ticker_symbol} — "
            "3D Implied Volatility Observations"
        ),
        template="plotly_dark",
        scene=dict(
            xaxis_title="Moneyness (Strike / Stock Price)",
            yaxis_title="Days to Expiration",
            zaxis_title="Implied Volatility (%)",
        ),
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=60,
        ),
        height=800,
    )

    # Save as a standalone interactive HTML file.
    figure.write_html(
        output_file,
        include_plotlyjs=True,
    )

    print(
        f"\nInteractive 3D chart saved to: {output_file}"
    )

    return figure


# ============================================================
# RUN MODULE DIRECTLY
# ============================================================

if __name__ == "__main__":

    # Retrieve options across six expiration dates.
    data = fetch_multiple_expirations(
        ticker_symbol="SPY",
        risk_free_rate=0.045,
        dividend_yield=0.0,
        minimum_days_to_expiry=7,
        maximum_expirations=6,
        maximum_relative_spread=0.30,
    )

    print(
        f"\nTotal observations collected: {len(data)}"
    )

    # Restrict the visualization to near-the-money options.
    surface_data = prepare_surface_data(
        data,
        minimum_moneyness=0.95,
        maximum_moneyness=1.05,
    )

    print(
        f"Observations included in 3D chart: {len(surface_data)}"
    )

    print(
        "Expiration dates represented: "
        f"{surface_data['Expiration'].nunique()}"
    )

    # Generate the interactive visualization.
    create_volatility_surface_chart(
        df=surface_data,
        ticker_symbol="SPY",
        output_file="volatility_surface_3d.html",
    )