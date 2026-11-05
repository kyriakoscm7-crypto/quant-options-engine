"""Cached SEC directory access with explicit data freshness."""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.sec_company_directory import fetch_sec_company_directory


@dataclass(frozen=True)
class DirectorySnapshot:
    registry: CompanyRegistry | None
    status: str
    age_seconds: int | None


class CompanyDirectoryService:
    """Process-local SEC directory cache with bounded stale fallback."""

    def __init__(
        self,
        ttl_seconds: int = 86400,
        max_stale_seconds: int = 604800,
        fetcher: Callable | None = None,
        clock: Callable = time.monotonic,
    ):
        if not 0 < ttl_seconds < max_stale_seconds:
            raise ValueError("Invalid directory cache lifetimes.")

        self.ttl = ttl_seconds
        self.max_stale = max_stale_seconds
        self.fetcher = fetcher or fetch_sec_company_directory
        self.clock = clock
        self._lock = threading.RLock()
        self._registry = None
        self._loaded_at = None

    def get(self) -> DirectorySnapshot:
        """Return live, cached, stale or unavailable directory data."""
        with self._lock:
            now = self.clock()

            if self._registry is not None:
                age = max(0, now - self._loaded_at)
                if age < self.ttl:
                    return DirectorySnapshot(
                        self._registry, "cached", int(age)
                    )

            try:
                records = self.fetcher()
                registry = CompanyRegistry(records)

                if not registry.companies:
                    raise ValueError("SEC company directory is empty.")

            except Exception:
                if self._registry is not None:
                    age = max(0, self.clock() - self._loaded_at)
                    if age < self.max_stale:
                        return DirectorySnapshot(
                            self._registry, "stale", int(age)
                        )

                return DirectorySnapshot(None, "unavailable", None)

            self._registry = registry
            self._loaded_at = self.clock()

            return DirectorySnapshot(self._registry, "live", 0)

    def search(self, query: str, limit: int = 20):
        """Search only when a usable directory is available."""
        snapshot = self.get()

        if snapshot.registry is None:
            return snapshot, []

        return snapshot, snapshot.registry.search(query, limit=limit)
