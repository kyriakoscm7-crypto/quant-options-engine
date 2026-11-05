"""Thread-safe news caching, cooldowns and explicit freshness states."""

import copy
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


class NewsRateLimited(RuntimeError):
    """A provider has explicitly rejected the request due to rate limiting."""

    def __init__(self, message, retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after


def retry_after_seconds(response):
    """Honor both HTTP Retry-After formats without shortening provider waits."""
    value = getattr(response, "headers", {}).get("Retry-After", "")
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return 0


@dataclass(frozen=True)
class NewsResult:
    articles: list[dict]
    status: str
    age_seconds: int | None
    message: str


@dataclass
class _CacheEntry:
    articles: list[dict]
    stored_at: float


class NewsReliability:
    """Bounded process-local cache with provider cooldowns.

    Cache identity must include every parameter that changes the news
    response, including company identity, date window and result limit.
    """

    def __init__(
        self,
        fresh_seconds: int = 900,
        stale_seconds: int = 86400,
        cooldown_seconds: int = 300,
        max_entries: int = 2048,
        clock: Callable[[], float] = time.monotonic,
    ):
        if not 0 < fresh_seconds < stale_seconds:
            raise ValueError("Fresh TTL must be below stale TTL.")
        if cooldown_seconds <= 0 or max_entries <= 0:
            raise ValueError("Cooldown and cache capacity must be positive.")

        self.fresh_seconds = fresh_seconds
        self.stale_seconds = stale_seconds
        self.cooldown_seconds = cooldown_seconds
        self.max_entries = max_entries
        self.clock = clock

        self._entries = OrderedDict()
        self._cooldowns = {}
        self._lock = threading.RLock()

        # Fixed lock stripes bound memory use while deduplicating requests.
        self._request_locks = [threading.Lock() for _ in range(64)]

    def _entry(self, key, now):
        """Return a valid cache entry and discard expired entries."""
        entry = self._entries.get(key)
        if entry is None:
            return None

        age = max(0, now - entry.stored_at)

        if age >= self.stale_seconds:
            del self._entries[key]
            return None

        self._entries.move_to_end(key)
        return entry

    def fetch(self, provider: str, cache_key: str, loader):
        """Fetch news without hiding stale data or retrying rate limits."""
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("Provider name is required.")
        if not isinstance(cache_key, str) or not cache_key.strip():
            raise ValueError("Cache key is required.")

        provider = provider.strip().lower()
        key = (provider, cache_key.strip())

        # Serialize each provider so concurrent queries observe its cooldown.
        lock_index = hash(provider) % len(self._request_locks)

        with self._request_locks[lock_index]:
            with self._lock:
                now = self.clock()
                entry = self._entry(key, now)

                if entry is not None:
                    age = max(0, now - entry.stored_at)
                    if age < self.fresh_seconds:
                        return NewsResult(
                            copy.deepcopy(entry.articles),
                            "cached",
                            int(age),
                            "Showing recently cached news.",
                        )

                cooldown_until = self._cooldowns.get(provider, 0)
                blocked = now < cooldown_until

            if blocked:
                if entry is not None:
                    return NewsResult(
                        copy.deepcopy(entry.articles),
                        "stale",
                        int(max(0, now - entry.stored_at)),
                        "Provider rate-limited; showing older cached news.",
                    )

                return NewsResult(
                    [], "unavailable", None,
                    "News provider is temporarily rate-limited.",
                )

            try:
                articles = loader()
                if not isinstance(articles, list):
                    raise ValueError("News provider returned invalid data.")
                if not all(isinstance(row, dict) for row in articles):
                    raise ValueError("News provider returned invalid articles.")

            except NewsRateLimited as error:
                with self._lock:
                    now = self.clock()
                    self._cooldowns[provider] = max(
                        self._cooldowns.get(provider, 0),
                        now + max(self.cooldown_seconds, error.retry_after),
                    )

                return self._fallback(
                    key, "Provider rate-limited; cached news may be older."
                )

            except Exception:
                # The public UI must not expose network error internals.
                return self._fallback(
                    key, "News provider unavailable; cached news may be older."
                )

            with self._lock:
                now = self.clock()
                self._entries[key] = _CacheEntry(
                    copy.deepcopy(articles), now
                )
                self._entries.move_to_end(key)

                while len(self._entries) > self.max_entries:
                    self._entries.popitem(last=False)

            return NewsResult(
                copy.deepcopy(articles),
                "live",
                0,
                "New results retrieved from the provider.",
            )

    def _fallback(self, key, message):
        with self._lock:
            now = self.clock()
            entry = self._entry(key, now)

            if entry is None:
                return NewsResult([], "unavailable", None, message)

            return NewsResult(
                copy.deepcopy(entry.articles),
                "stale",
                int(max(0, now - entry.stored_at)),
                message,
            )
