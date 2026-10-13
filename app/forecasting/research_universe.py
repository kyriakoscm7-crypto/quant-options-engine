"""Diversified stock universe for quantitative forecasting research.

This is a fixed contemporary research universe, not a historical
point-in-time index membership dataset.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchStock:
    ticker: str
    sector: str


RESEARCH_UNIVERSE = (
    ResearchStock("AAPL", "Technology"),
    ResearchStock("MSFT", "Technology"),
    ResearchStock("NVDA", "Technology"),
    ResearchStock("ADBE", "Technology"),

    ResearchStock("JPM", "Financials"),
    ResearchStock("BAC", "Financials"),
    ResearchStock("GS", "Financials"),
    ResearchStock("MS", "Financials"),

    ResearchStock("JNJ", "Healthcare"),
    ResearchStock("UNH", "Healthcare"),
    ResearchStock("ABBV", "Healthcare"),
    ResearchStock("MRK", "Healthcare"),

    ResearchStock("XOM", "Energy"),
    ResearchStock("CVX", "Energy"),
    ResearchStock("COP", "Energy"),
    ResearchStock("SLB", "Energy"),

    ResearchStock("PG", "Consumer Staples"),
    ResearchStock("KO", "Consumer Staples"),
    ResearchStock("PEP", "Consumer Staples"),
    ResearchStock("WMT", "Consumer Staples"),

    ResearchStock("AMZN", "Consumer Discretionary"),
    ResearchStock("HD", "Consumer Discretionary"),
    ResearchStock("MCD", "Consumer Discretionary"),
    ResearchStock("NKE", "Consumer Discretionary"),

    ResearchStock("CAT", "Industrials"),
    ResearchStock("DE", "Industrials"),
    ResearchStock("HON", "Industrials"),
    ResearchStock("UPS", "Industrials"),

    ResearchStock("NEE", "Utilities"),
    ResearchStock("DUK", "Utilities"),
    ResearchStock("SO", "Utilities"),
    ResearchStock("AEP", "Utilities"),

    ResearchStock("PLD", "Real Estate"),
    ResearchStock("AMT", "Real Estate"),
    ResearchStock("EQIX", "Real Estate"),
    ResearchStock("O", "Real Estate"),

    ResearchStock("LIN", "Materials"),
    ResearchStock("APD", "Materials"),
    ResearchStock("SHW", "Materials"),
    ResearchStock("NEM", "Materials"),
)


def get_research_universe() -> tuple[ResearchStock, ...]:
    """Return the fixed research universe."""

    return RESEARCH_UNIVERSE


def get_sector_tickers(sector: str) -> tuple[str, ...]:
    """Return tickers belonging to a selected sector."""

    return tuple(
        stock.ticker
        for stock in RESEARCH_UNIVERSE
        if stock.sector == sector
    )


def validate_research_universe() -> bool:
    """Validate ticker uniqueness and sector diversification."""

    tickers = [stock.ticker for stock in RESEARCH_UNIVERSE]
    sectors = {stock.sector for stock in RESEARCH_UNIVERSE}

    if len(tickers) != len(set(tickers)):
        raise ValueError("Research universe contains duplicate tickers.")

    if len(RESEARCH_UNIVERSE) != 40:
        raise ValueError("Research universe must contain 40 stocks.")

    if len(sectors) != 10:
        raise ValueError("Research universe must contain 10 sectors.")

    if any(not stock.ticker or not stock.sector for stock in RESEARCH_UNIVERSE):
        raise ValueError("Research universe contains invalid entries.")

    return True
