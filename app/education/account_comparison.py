"""Illustrative TFSA versus RRSP comparison using equal after-tax budgets."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class AccountComparison:
    tfsa_contribution: float
    rrsp_contribution: float
    rrsp_deduction_value: float
    tfsa_future_value: float
    rrsp_future_value: float
    rrsp_after_tax_value: float
    difference: float


def compare_accounts(
    after_tax_budget: float,
    tax_rate_now_pct: float,
    tax_rate_later_pct: float,
    annual_return_pct: float,
    years: int,
) -> AccountComparison:
    """Compare equal after-tax saving costs with full RRSP deduction use.

    The RRSP deduction's tax benefit is assumed fully realized and
    used to finance the larger gross RRSP contribution.

    Tax rates are simplified marginal rates, not computed CRA taxes.
    The withdrawal is assumed to face one constant illustrative rate.
    Fees, benefit clawbacks, inflation and contribution limits excluded.
    """
    values = (
        after_tax_budget, tax_rate_now_pct,
        tax_rate_later_pct, annual_return_pct,
    )
    if not all(isfinite(v) for v in values):
        raise ValueError("Financial inputs must be finite.")

    if after_tax_budget < 0:
        raise ValueError("Savings budget cannot be negative.")
    if not 0 <= tax_rate_now_pct < 100:
        raise ValueError("Current tax rate must be between 0% and 100%.")
    if not 0 <= tax_rate_later_pct < 100:
        raise ValueError("Future tax rate must be between 0% and 100%.")
    if annual_return_pct <= -100 or annual_return_pct > 100:
        raise ValueError("Return assumption is outside the supported range.")
    if type(years) is not int or not 0 <= years <= 80:
        raise ValueError("Years must be an integer between 0 and 80.")

    now = tax_rate_now_pct / 100
    later = tax_rate_later_pct / 100
    factor = (1 + annual_return_pct / 100) ** years

    tfsa = after_tax_budget
    rrsp = after_tax_budget / (1 - now)
    deduction = rrsp * now

    tfsa_future = tfsa * factor
    rrsp_future = rrsp * factor
    rrsp_after_tax = rrsp_future * (1 - later)

    if not all(isfinite(v) for v in (tfsa_future, rrsp_future)):
        raise ValueError("Projected value exceeds numeric limits.")

    return AccountComparison(
        tfsa_contribution=tfsa,
        rrsp_contribution=rrsp,
        rrsp_deduction_value=deduction,
        tfsa_future_value=tfsa_future,
        rrsp_future_value=rrsp_future,
        rrsp_after_tax_value=rrsp_after_tax,
        difference=rrsp_after_tax - tfsa_future,
    )
