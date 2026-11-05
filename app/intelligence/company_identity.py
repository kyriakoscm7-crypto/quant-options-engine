"""Resolve US filing entities without guessing company identities."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyIdentity:
    ticker: str
    name: str
    cik: str
    source: str = "SEC ticker mapping"


def normalize_ticker(symbol: str) -> str:
    """Normalize ticker syntax without assuming its exchange."""
    ticker = symbol.strip().upper()
    if ":" in ticker:
        _, ticker = ticker.rsplit(":", 1)

    ticker = ticker.replace(".", "-")

    if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{0,15}", ticker):
        raise ValueError("Invalid ticker format.")

    return ticker


def resolve_sec_company(
    symbol: str,
    company_records: dict,
) -> CompanyIdentity | None:
    """Resolve an SEC-listed ticker; refuse ambiguous matches."""
    requested = normalize_ticker(symbol)
    matches = []

    for record in company_records.values():
        if not isinstance(record, dict):
            continue

        raw_ticker = str(record.get("ticker") or "")

        try:
            candidate = normalize_ticker(raw_ticker)
        except ValueError:
            continue

        if candidate != requested:
            continue

        cik = record.get("cik_str")
        name = str(record.get("title") or "").strip()

        if not name or not str(cik).isdigit() or not 0 < int(cik) < 10**10:
            continue

        matches.append(
            CompanyIdentity(
                ticker=candidate,
                name=name,
                cik=str(int(cik)).zfill(10),
            )
        )

    unique = list(dict.fromkeys(matches))

    if len(unique) > 1:
        raise ValueError(
            "Ambiguous SEC ticker identity; manual review required."
        )

    return unique[0] if unique else None
