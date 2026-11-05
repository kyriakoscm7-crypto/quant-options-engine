"""Source-linked SEC EDGAR filings for historical event research."""

import re
from datetime import date

import requests

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

ACCESSION_PATTERN = re.compile(r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
DOCUMENT_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def validate_user_agent(user_agent: str) -> str:
    """Require a declared application identity and contact address."""
    value = str(user_agent or "").strip()

    if (
        len(value) < 12
        or not EMAIL_PATTERN.search(value)
        or "example.com" in value.lower()
    ):
        raise ValueError(
            "SEC_USER_AGENT must identify the application and "
            "provide a real contact email address."
        )

    return value


def resolve_company(ticker: str, directory: dict) -> tuple[int, str] | None:
    """Map an exact ticker to its SEC CIK and registered company name."""
    symbol = str(ticker).strip().upper()

    if not symbol or not isinstance(directory, dict):
        return None

    for company in directory.values():
        if not isinstance(company, dict):
            continue

        if str(company.get("ticker", "")).strip().upper() != symbol:
            continue

        try:
            cik = int(company["cik_str"])
        except (KeyError, TypeError, ValueError):
            continue

        if cik > 0:
            return cik, str(company.get("title") or symbol)

    return None


def filings_near_event(
    submissions: dict,
    cik: int,
    event_date: date | str,
    before_days: int = 7,
    after_days: int = 2,
    limit: int = 15,
) -> list[dict]:
    """Find filings by official filing date, not unverified time of day."""
    day = date.fromisoformat(str(event_date)[:10])

    if before_days < 0 or after_days < 0:
        raise ValueError("Event windows cannot be negative.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    recent = submissions.get("filings", {}).get("recent", {})

    if not isinstance(recent, dict):
        return []

    accessions = recent.get("accessionNumber", [])
    filed_dates = recent.get("filingDate", [])
    forms = recent.get("form", [])
    documents = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])
    if not isinstance(descriptions, list):
        descriptions = []

    if not all(
        isinstance(values, list)
        for values in (accessions, filed_dates, forms, documents)
    ):
        return []

    matches = []

    for index, accession in enumerate(accessions):
        if index >= min(len(filed_dates), len(forms), len(documents)):
            break

        accession = str(accession)
        document = str(documents[index])

        if not ACCESSION_PATTERN.fullmatch(accession):
            continue

        if (
            not DOCUMENT_PATTERN.fullmatch(document)
            or document in (".", "..")
        ):
            continue

        try:
            filing_day = date.fromisoformat(str(filed_dates[index]))
        except ValueError:
            continue

        days_from_event = (filing_day - day).days

        if not -before_days <= days_from_event <= after_days:
            continue

        if days_from_event < 0:
            relationship = "Filed before event date"
        elif days_from_event == 0:
            relationship = "Same-day filing; timing unverified"
        else:
            relationship = "Filed after event date"

        description = (
            str(descriptions[index])
            if index < len(descriptions)
            else ""
        )

        url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession.replace('-', '')}/{document}"
        )

        matches.append({
            "form": str(forms[index]),
            "filing_date": filing_day.isoformat(),
            "relationship": relationship,
            "accession": accession,
            "description": description,
            "url": url,
        })

    matches.sort(
        key=lambda item: (item["filing_date"], item["accession"]),
        reverse=True,
    )

    return matches[:limit]


def fetch_sec_filings(
    ticker: str,
    event_date: date | str,
    user_agent: str,
) -> tuple[str, list[dict]]:
    """Retrieve SEC submissions with declared, low-volume HTTP requests."""
    agent = validate_user_agent(user_agent)
    headers = {
        "User-Agent": agent,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json",
    }

    ticker_response = requests.get(
        TICKERS_URL,
        headers=headers,
        timeout=15,
    )
    ticker_response.raise_for_status()

    company = resolve_company(ticker, ticker_response.json())

    if company is None:
        raise LookupError(
            f"No matching SEC company identifier found for {ticker}."
        )

    cik, company_name = company

    submissions_response = requests.get(
        SUBMISSIONS_URL.format(cik=cik),
        headers=headers,
        timeout=15,
    )
    submissions_response.raise_for_status()

    filings = filings_near_event(
        submissions_response.json(),
        cik,
        event_date,
    )

    return company_name, filings
