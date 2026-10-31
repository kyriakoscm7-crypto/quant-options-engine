"""Educational ETF exposure and overlap calculations.

All example fund holdings are fictional and do not represent real ETFs.
Weights are expressed as percentages of each fund.
"""

from math import isfinite

EXAMPLE_FUNDS = {
    "Broad Market": {
        "Company A": 25.0,
        "Company B": 20.0,
        "Company C": 20.0,
        "Company D": 20.0,
        "Company E": 15.0,
    },
    "Technology Focus": {
        "Company A": 45.0,
        "Company B": 35.0,
        "Company F": 20.0,
    },
    "Balanced Mix": {
        "Company C": 20.0,
        "Company D": 15.0,
        "Company E": 15.0,
        "Bond Holdings": 50.0,
    },
}


def validate_weights(weights: dict[str, float]) -> None:
    if not weights:
        raise ValueError("At least one holding is required.")
    if any(
        not isinstance(name, str) or not name.strip()
        for name in weights
    ):
        raise ValueError("Holding names must be nonempty.")
    if any(
        not isinstance(v, (int, float))
        or not isfinite(v)
        or v < 0
        for v in weights.values()
    ):
        raise ValueError("Weights must be finite and nonnegative.")
    if abs(sum(weights.values()) - 100) > 1e-6:
        raise ValueError("Holding weights must total 100%.")


def fund_overlap(
    fund_a: dict[str, float],
    fund_b: dict[str, float],
) -> float:
    """Shared exposure: sum of the lesser weights for each holding.

    Returns 0 to 100. This is not return correlation.
    """
    validate_weights(fund_a)
    validate_weights(fund_b)
    return sum(
        min(fund_a.get(name, 0), fund_b.get(name, 0))
        for name in fund_a.keys() | fund_b.keys()
    )


def portfolio_exposure(
    funds: dict[str, dict[str, float]],
    allocations: dict[str, float],
) -> dict[str, float]:
    """Combine underlying holdings using fund allocations in percent."""
    validate_weights(allocations)
    if set(allocations) != set(funds):
        raise ValueError("Allocations must match provided fund names.")

    exposure: dict[str, float] = {}
    for fund_name, allocation in allocations.items():
        holdings = funds[fund_name]
        validate_weights(holdings)
        for holding, weight in holdings.items():
            exposure[holding] = (
                exposure.get(holding, 0)
                + allocation * weight / 100
            )
    return dict(
        sorted(exposure.items(), key=lambda item: (-item[1], item[0]))
    )


def concentration_index(exposure: dict[str, float]) -> float:
    """Sum of squared fractional weights: 0 to 1.

    This describes concentration, not portfolio risk or volatility.
    """
    validate_weights(exposure)
    return sum((weight / 100) ** 2 for weight in exposure.values())


def annual_fee_cost(
    portfolio_value: float,
    annual_fee_pct: float,
) -> float:
    """Illustrative one-year fee using a constant balance."""
    if not all(isfinite(v) for v in (portfolio_value, annual_fee_pct)):
        raise ValueError("Inputs must be finite.")
    if portfolio_value < 0 or not 0 <= annual_fee_pct <= 100:
        raise ValueError("Invalid portfolio value or annual fee.")
    return portfolio_value * annual_fee_pct / 100
