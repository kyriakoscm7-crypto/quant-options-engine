"""Guard legacy public feeds until a separately licensed provider is integrated.

Stock Explorer is intercepted by the main router for a display-only widget.
Discovery/Scanner use official screeners, Simulation Lab has independent models,
and remaining demos stay offline, independent of legacy flags.
"""

import os

MARKET_DATA_ROUTES = frozenset({
    "🔎 Stock Explorer",
    "🧪 Simulation Lab",
    "💎 Quant Discovery",
    "🔍 Market Scanner",
    "💼 Portfolio Manager",
    "🧠 Forecast Intelligence",
})


def market_data_rights_confirmed() -> bool:
    """Legacy attestation only; it cannot enable public custom analytics.

    Kept for compatibility with operator tooling. Provider approval requires
    a separately reviewed integration, not an environment switch.
    """
    return os.environ.get("QI_MARKET_DATA_RIGHTS_CONFIRMED", "").strip().lower() == "true"


def public_market_data_route_blocked(route: str) -> bool:
    return route in MARKET_DATA_ROUTES
