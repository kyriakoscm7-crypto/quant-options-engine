"""Independent diagnostics for simulated portfolio concentration."""

import ast

import pandas as pd


def _position_values(value: object) -> dict[str, float]:
    """Read the position-value dictionary stored by the simulator."""
    if isinstance(value, dict):
        positions = value
    elif isinstance(value, str):
        positions = ast.literal_eval(value)
    else:
        raise ValueError("Position Values must be a dictionary.")

    if not isinstance(positions, dict):
        raise ValueError("Position Values must contain a dictionary.")

    result = {}

    for ticker, amount in positions.items():
        amount = float(amount)

        if not pd.notna(amount) or amount < 0:
            raise ValueError(f"Invalid position value for {ticker}")

        result[str(ticker)] = amount

    return result


def analyze_concentration(results: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily portfolio concentration and accounting diagnostics."""
    required = {"Date", "Portfolio Value", "Cash", "Position Values"}

    if not required.issubset(results.columns):
        missing = sorted(required - set(results.columns))
        raise ValueError(f"Missing required columns: {missing}")

    records = []

    for record in results.to_dict(orient="records"):
        date = pd.Timestamp(record["Date"])
        portfolio_value = float(record["Portfolio Value"])
        cash = float(record["Cash"])
        positions = _position_values(record["Position Values"])

        if not pd.notna(portfolio_value) or portfolio_value <= 0:
            raise ValueError(f"Invalid portfolio value on {date}")

        if not pd.notna(cash) or cash < -1e-7:
            raise ValueError(f"Invalid cash balance on {date}")

        invested_value = sum(positions.values())
        reconstructed_value = invested_value + cash
        accounting_error = reconstructed_value - portfolio_value

        weights = {
            ticker: value / portfolio_value
            for ticker, value in positions.items()
        }

        ranked = sorted(
            weights.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        largest_ticker = ranked[0][0] if ranked else None
        largest_weight = ranked[0][1] if ranked else 0.0

        records.append(
            {
                "Date": date,
                "Portfolio Value": portfolio_value,
                "Number of Holdings": len(positions),
                "Largest Holding": largest_ticker,
                "Largest Weight (%)": largest_weight * 100,
                "Top 3 Weight (%)": (
                    sum(weight for _, weight in ranked[:3]) * 100
                ),
                "Cash Weight (%)": cash / portfolio_value * 100,
                "Concentration HHI": sum(
                    weight**2 for weight in weights.values()
                ),
                "Accounting Error ($)": accounting_error,
            }
        )

    if not records:
        return pd.DataFrame()

    audit = pd.DataFrame(records).sort_values("Date")

    if audit["Date"].duplicated().any():
        raise ValueError("Duplicate dates in portfolio results.")

    return audit.reset_index(drop=True)
