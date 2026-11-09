"""Host-wide SEC request budget shared by current SEC HTTP entry points.

At most one request start per second across processes under the same OS user.
Multi-host deployments must route through one gateway; this cannot coordinate
other machines or unrelated applications using the same operator identity.
"""
import fcntl
import json
import math
import os
import stat
import tempfile
import threading
import time

import requests

from app.intelligence.news_reliability import retry_after_seconds

_LOCK = threading.Lock()
BUDGET_PATH = os.path.join(tempfile.gettempdir(), f"qi-sec-budget-{os.getuid()}.json")


def sec_get(url, **kwargs):
    """Reserve host budget before HTTP; persist 403/429 cooldown across processes."""
    path = BUDGET_PATH
    with _LOCK:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "r+") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise RuntimeError("Unsafe SEC budget file")
            fcntl.flock(handle, fcntl.LOCK_EX)
            raw = handle.read(2048)
            try:
                state = json.loads(raw) if raw else {}
            except ValueError:
                # Corrupt shared state is not permission to reset provider waits.
                raise RuntimeError("SEC budget state requires operator review") from None
            if not isinstance(state, dict) or any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0
                for value in state.values()
            ):
                raise RuntimeError("SEC budget state requires operator review")
            now = time.time()
            if now < state.get("blocked_until", 0):
                raise RuntimeError("SEC fair-access cooldown; try later")
            delay = max(0, state.get("next_at", 0) - now)
            if delay > 2:
                raise RuntimeError("SEC budget clock changed; try later")
            time.sleep(delay)
            state["next_at"] = time.time() + 1

            def save():
                handle.seek(0)
                json.dump(state, handle)
                handle.truncate()
                handle.flush()

            save()
            kwargs["allow_redirects"] = False
            kwargs.pop("timeout", None)
            response = requests.get(url, timeout=(5, 20), **kwargs)
            if getattr(response, "status_code", None) in {403, 429}:
                state["blocked_until"] = time.time() + max(600, retry_after_seconds(response))
                save()
            return response
