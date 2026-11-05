"""Loopback API smoke. Token passed in environment, never printed."""

import json
import os
import time
import urllib.error
import urllib.request
from http.client import RemoteDisconnected

base = os.environ.get("QI_SMOKE_URL", "http://127.0.0.1:8080")
token = os.environ["QI_SMOKE_TOKEN"]


def request(path, payload=None, authorized=True):
    headers = {"Content-Type": "application/json"}
    if authorized:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, None


for attempt in range(30):
    try:
        if request("/health", authorized=False)[0] == 200:
            break
    except (OSError, RemoteDisconnected, urllib.error.URLError):
        pass
    time.sleep(1)
else:
    raise RuntimeError("Local API did not become healthy")
option = dict(S=100, K=100, T=1, r=0.05, sigma=0.2)
assert request("/api/v1/options/price", option, False)[0] == 401
status, data = request("/api/v1/options/price", option)
assert status == 200 and abs(data["call_price"] - 10.4506) < 0.0001
# Inspect the actual disabled legacy route path from the API schema.
market = [path for path in request("/openapi.json")[1]["paths"] if "market" in path]
assert market
for path in market:
    assert (
        request(path.replace("{ticker}", "AAPL").replace("{symbol}", "AAPL"))[0] == 403
    )
print("API health, auth denial, calculation and legacy 403 passed")
