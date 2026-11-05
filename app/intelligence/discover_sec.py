"""Bounded SEC JSON gateway for Discover; never accepts arbitrary URLs.

One gateway process per operator/egress is required. Multiple replicas must use
an operator-managed shared limiter before activation (see Discover release notes).
"""
import copy
import json
import re
import threading
import time
from collections import OrderedDict
from datetime import UTC, datetime

from app.intelligence.news_reliability import retry_after_seconds
from app.intelligence.sec_access import sec_get
from app.intelligence.sec_filings import validate_user_agent


class SecGateway:
    """Serialize all Discover requests, cache bounded results, fail closed.

    No automatic retries, redirects, stale fallback or filing-text downloads.
    403/429 pauses the entire gateway for at least ten minutes.
    """

    def __init__(self, agent, *, get=None, clock=time.monotonic, sleep=time.sleep):
        self.agent = validate_user_agent(agent)
        self.get = get or sec_get
        self.clock, self.sleep = clock, sleep
        self.lock = threading.Lock()
        self.cache = OrderedDict()
        self.next_at = 0.0
        self.blocked_until = 0.0

    def fetch(self, resource, cik=None):
        if resource == "directory" and cik is None:
            url = "https://www.sec.gov/files/company_tickers.json"
        elif resource in {"submissions", "companyfacts"} and re.fullmatch(r"[0-9]{10}", str(cik)) and int(cik) > 0:
            path = "submissions" if resource == "submissions" else "api/xbrl/companyfacts"
            url = f"https://data.sec.gov/{path}/CIK{cik}.json"
        else:
            raise ValueError("Unsupported SEC resource or CIK")
        with self.lock:
            now = self.clock()
            cached = self.cache.get(url)
            ttl = 86400 if resource == "directory" else 3600
            if cached and now - cached[0] < ttl:
                self.cache.move_to_end(url)
                return copy.deepcopy(cached[1])
            if now < self.blocked_until:
                raise RuntimeError("SEC fair-access cooldown; try later")
            self.sleep(max(0, self.next_at - now))
            self.next_at = self.clock() + 1.0
            response = self.get(url, headers={"User-Agent": self.agent, "Accept": "application/json"},
                                timeout=(5, 20), stream=True, allow_redirects=False)
            try:
                if response.status_code in {403, 429}:
                    self.blocked_until = self.clock() + max(600, retry_after_seconds(response))
                if response.status_code != 200:
                    raise RuntimeError("SEC data unavailable")
                chunks, total = [], 0
                for chunk in response.iter_content(chunk_size=65536):
                    total += len(chunk)
                    if total > 25_000_000:
                        raise ValueError("SEC response exceeds size limit")
                    chunks.append(chunk)
                data = json.loads(b"".join(chunks))
                if not isinstance(data, dict):
                    raise ValueError("Unexpected SEC JSON")
                result = {"data": data, "url": url, "retrieved_at": datetime.now(UTC).isoformat()}
                self.cache[url] = (self.clock(), result, total)
                self.cache.move_to_end(url)
                while len(self.cache) > 24 or sum(item[2] for item in self.cache.values()) > 50_000_000:
                    self.cache.popitem(last=False)
                return copy.deepcopy(result)
            finally:
                response.close()
