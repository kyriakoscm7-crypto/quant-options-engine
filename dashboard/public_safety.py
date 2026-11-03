"""Public data-rights guard and fictional showcase routing.

Public research defaults to an interactive *offline synthetic demo*, not
a blank page. Activating live feeds requires the operator to verify
all licensing and other applicable permissions. A flag is not a licence.
"""

import os

MARKET_DATA_ROUTES = frozenset({
    "🔎 Stock Explorer",
    "💎 Quant Discovery",
    "🔍 Market Scanner",
    "💼 Portfolio Manager",
    "🧠 Forecast Intelligence",
})


def market_data_rights_confirmed() -> bool:
    """True only when an operator explicitly opts in after rights review."""
    return os.environ.get("QI_MARKET_DATA_RIGHTS_CONFIRMED", "").strip().lower() == "true"


def public_market_data_route_blocked(route: str) -> bool:
    return route in MARKET_DATA_ROUTES and not market_data_rights_confirmed()
