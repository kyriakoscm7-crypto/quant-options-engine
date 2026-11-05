"""Search official company records without guessing identities."""

from collections import defaultdict

from app.intelligence.company_identity import (
    CompanyIdentity,
    normalize_ticker,
)


def _name_key(value: str) -> str:
    """Normalize company names for case-insensitive search."""
    text = value.casefold()
    return " ".join(
        "".join(c if c.isalnum() else " " for c in text).split()
    )


class CompanyRegistry:
    """Searchable snapshot of SEC company records.

    These records identify SEC filing entities, not independently
    verified exchange listings or international company coverage.
    """

    def __init__(self, records: dict):
        if not isinstance(records, dict):
            raise ValueError("Company records must be a dictionary.")

        entries = []
        seen = set()

        for record in records.values():
            if not isinstance(record, dict):
                continue

            try:
                ticker = normalize_ticker(str(record["ticker"]))
                name = str(record["title"]).strip()
                cik_raw = str(record["cik_str"])

                if not name or not cik_raw.isdigit() or not 0 < int(cik_raw) < 10**10:
                    continue

                cik = str(int(cik_raw)).zfill(10)
                identity = CompanyIdentity(
                    ticker=ticker,
                    name=name,
                    cik=cik,
                )
            except (KeyError, TypeError, ValueError):
                continue

            identity_key = (ticker, cik)
            if identity_key in seen:
                continue

            seen.add(identity_key)
            entries.append(identity)

        self.companies = tuple(
            sorted(entries, key=lambda c: (c.name.casefold(), c.ticker))
        )

        by_ticker = defaultdict(list)
        for company in self.companies:
            by_ticker[company.ticker].append(company)

        self._by_ticker = dict(by_ticker)

    def search(self, query: str, limit: int = 20):
        """Find companies by ticker or name, ranked by match quality."""
        if not isinstance(query, str):
            raise ValueError("Search query must be text.")

        query = query.strip()

        if not query or len(query) > 100:
            raise ValueError("Search query must contain 1-100 characters.")

        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("Invalid result limit.")

        if not 1 <= limit <= 100:
            raise ValueError("Result limit must be 1-100.")

        normalized_name = _name_key(query)
        if not normalized_name:
            raise ValueError("Search query contains no searchable text.")

        try:
            normalized_ticker = normalize_ticker(query)
        except ValueError:
            normalized_ticker = None

        ranked = []

        for company in self.companies:
            name = _name_key(company.name)

            if company.ticker == normalized_ticker:
                rank = 0
            elif name == normalized_name:
                rank = 1
            elif name.startswith(normalized_name):
                rank = 2
            elif any(
                word.startswith(normalized_name)
                for word in name.split()
            ):
                rank = 3
            elif normalized_name in name:
                rank = 4
            else:
                continue

            ranked.append((rank, company.name.casefold(), company))

        ranked.sort(key=lambda item: (item[0], item[1]))
        return [company for _, _, company in ranked[:limit]]

    def resolve_ticker(self, ticker: str):
        """Return one exact SEC ticker match; refuse collisions.

        Exchange-qualified symbols require verified exchange metadata
        and are not accepted by this SEC-only lookup.
        """
        if not isinstance(ticker, str) or ":" in ticker:
            raise ValueError("Use an unqualified SEC ticker.")

        normalized = normalize_ticker(ticker)
        matches = self._by_ticker.get(normalized, [])

        if len(matches) > 1:
            raise ValueError(
                "Ambiguous ticker: multiple SEC company identities."
            )

        return matches[0] if matches else None
