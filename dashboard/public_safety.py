"""Public deployment guard for externally sourced market data.

The feature flag is deliberately OFF by default. Turning it on does not
grant any data rights: the operator must independently verify licensing
for every data source and applicable redistribution/use conditions.
"""

import os

MARKET_DATA_ROUTES = frozenset({
    "🔎 Stock Explorer",
    "💎 Quant Discovery",
    "🔍 Market Scanner",
    "💼 Portfolio Manager",
})


def market_data_rights_confirmed() -> bool:
    """True only when an operator explicitly opts in after rights review."""
    return os.environ.get("QI_MARKET_DATA_RIGHTS_CONFIRMED", "").strip().lower() == "true"


def public_market_data_route_blocked(route: str) -> bool:
    return route in MARKET_DATA_ROUTES and not market_data_rights_confirmed()
