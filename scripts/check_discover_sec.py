"""Bounded, operator-initiated SEC smoke check; never prints contact configuration."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.intelligence.discover_sec import SecGateway  # noqa: E402
from app.intelligence.discover_service import company_deep_dive  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", default="AAPL")
    args = parser.parse_args()
    agent = os.environ.get("QI_SEC_USER_AGENT", "")
    if not agent:
        print("BLOCKED: QI_SEC_USER_AGENT is unset. Supply a genuine operator contact; no requests sent.")
        return 1
    try:
        report = company_deep_dive(SecGateway(agent), args.ticker)
    except (ValueError, LookupError, RuntimeError, OSError) as exc:
        # Network exception strings may contain configuration; only classify them.
        print(f"BLOCKED: SEC retrieval failed ({type(exc).__name__}). Check contact configuration, network access and SEC cooldown; no fallback data used.")
        return 1
    print(json.dumps({"ticker": report["company"].ticker,
                      "cik": report["company"].cik,
                      "health": report["health"],
                      "sources": report["sources"],
                      "filings_count": len(report["filings"]),
                      "issues": report["issues"],
                      "earnings": report["earnings"]["status"],
                      "analysts": report["analysts"]["status"]}, indent=2))
    return 0 if report["health"] and report["health"]["observations"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
