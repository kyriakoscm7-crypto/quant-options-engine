"""SEC company-directory retrieval for public-company research."""

import os
import re

import requests

from app.intelligence.company_identity import resolve_sec_company

SEC_DIRECTORY_URL = "https://www.sec.gov/files/company_tickers.json"
MAX_RESPONSE_BYTES = 3_000_000


def _declared_user_agent() -> str:
    """Require an identifiable contact for SEC fair-access compliance."""
    agent = os.environ.get("QI_SEC_USER_AGENT", "").strip()

    if not agent or not re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", agent):
        raise ValueError(
            "Set QI_SEC_USER_AGENT to an application name and "
            "a real administrative contact email before fetching SEC data."
        )

    return agent


def fetch_sec_company_directory() -> dict:
    """Download the SEC ticker directory with bounded resource usage."""
    response = requests.get(
        SEC_DIRECTORY_URL,
        headers={
            "User-Agent": _declared_user_agent(),
            "Accept": "application/json",
        },
        timeout=15,
        stream=True,
    )

    try:
        response.raise_for_status()
        chunks = []
        total = 0

        for chunk in response.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                raise ValueError("SEC directory response too large.")
            chunks.append(chunk)

        import json

        directory = json.loads(b"".join(chunks))

        if not isinstance(directory, dict):
            raise ValueError("Unexpected SEC directory format.")

        return directory
    finally:
        response.close()


def find_sec_company(symbol: str, records: dict):
    """Resolve a ticker against the downloaded SEC directory."""
    return resolve_sec_company(symbol, records)
