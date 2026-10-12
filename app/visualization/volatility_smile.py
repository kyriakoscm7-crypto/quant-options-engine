import plotly.graph_objects as go

from app.market_data.yahoo_client import fetch_option_chain


def create_volatility_smile(
    ticker_symbol: str = "SPY",
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    minimum_days_to_expiry: int = 7
):
    """
    Create an interactive implied volatility chart.

    The chart plots implied volatility against strike price
    for one selected options expiration.
    """

    # Retrieve option quotes and calculated implied volatilities.
    df = fetch_option_chain(
        ticker_symbol=ticker_symbol,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        minimum_days_to_expiry=minimum_days_to_expiry
    )

    # Stop if no valid option quotes were returned.
    if df.empty:
        raise RuntimeError(
            "No valid option quotes available for visualization."
        )

    # Sort strikes from lowest to highest.
    df = df.sort_values("Strike").copy()

    # Retrieve the underlying stock price from our market-data results.
    stock_price = float(df["UnderlyingPrice"].iloc[0])  

    # Store additional information for interactive tooltips.
    custom_data = df[
        ["Bid", "Ask", "Expiration"]
    ].to_numpy()

    # Create the interactive Plotly figure.
    fig = go.Figure()

    # Plot implied volatility against strike price.
    fig.add_trace(
        go.Scatter(
            x=df["Strike"],
            y=df["ImpliedVolatility"],
            mode="lines+markers",
            name="Call Implied Volatility",
            customdata=custom_data,
            hovertemplate=(
                "<b>Strike:</b> $%{x:.2f}<br>"
                "<b>Implied Volatility:</b> %{y:.2f}%<br>"
                "<b>Bid:</b> $%{customdata[0]:.2f}<br>"
                "<b>Ask:</b> $%{customdata[1]:.2f}<br>"
                "<b>Expiration:</b> %{customdata[2]}"
                "<extra></extra>"
            )
        )
    )

    # Draw a vertical reference line at the current stock price.
    fig.add_vline(
        x=stock_price,
        line=dict(color="red", dash="dash"),
        annotation_text=f"Stock Price: ${stock_price:.2f}",
        annotation_position="top right"
    )



    # Configure the chart's appearance.
    fig.update_layout(
        title=(
            f"{ticker_symbol.upper()} — "
            f"Implied Volatility by Strike"
        ),
        xaxis_title="Strike Price ($)",
        yaxis_title="Implied Volatility (%)",
        template="plotly_dark",
        hovermode="closest",
        height=650
    )

    return fig


if __name__ == "__main__":

    # Generate the SPY volatility chart.
    figure = create_volatility_smile(
        ticker_symbol="SPY",
        risk_free_rate=0.045,
        dividend_yield=0.0,
        minimum_days_to_expiry=7
    )

    # Save an interactive HTML chart in the project directory.
    output_file = "volatility_smile.html"

    figure.write_html(output_file)

    print(f"\nInteractive chart saved to: {output_file}")