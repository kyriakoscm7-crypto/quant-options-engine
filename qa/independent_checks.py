import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient

from app.api.main import app
from app.pricing.black_scholes import BlackScholes
from app.pricing.implied_volatility import implied_volatility


def N(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def ref(S, K, T, r, v, q, kind="call"):
    if T == 0:
        return max((S - K) if kind == "call" else (K - S), 0)
    a, b = S * math.exp(-q * T), K * math.exp(-r * T)
    if v == 0:
        return max(a - b if kind == "call" else b - a, 0)
    d = (math.log(S) - math.log(K) + (r - q + v * v / 2) * T) / (v * math.sqrt(T))
    e = d - v * math.sqrt(T)
    return a * N(d) - b * N(e) if kind == "call" else b * N(-e) - a * N(-d)


rng = random.Random(734)
err = 0
parity = 0
greekerr = 0
iverr = 0
for i in range(500):
    S = rng.uniform(20, 500)
    K = S * rng.uniform(0.7, 1.3)
    T = rng.uniform(0.05, 3)
    r = rng.uniform(-0.03, 0.15)
    v = rng.uniform(0.1, 1.2)
    q = rng.uniform(0, 0.08)
    e = BlackScholes(S, K, T, r, v, q)
    c = e.call_price()
    p = e.put_price()
    g = e.greeks()
    err = max(
        err, abs(c - ref(S, K, T, r, v, q)), abs(p - ref(S, K, T, r, v, q, "put"))
    )
    parity = max(parity, abs(c - p - (S * math.exp(-q * T) - K * math.exp(-r * T))))
    h = 0.001
    dv = 0.00001
    dt = 0.00001
    delta = (ref(S + h, K, T, r, v, q) - ref(S - h, K, T, r, v, q)) / (2 * h)
    gamma = (
        ref(S + h, K, T, r, v, q)
        - 2 * ref(S, K, T, r, v, q)
        + ref(S - h, K, T, r, v, q)
    ) / h**2
    vega = (ref(S, K, T, r, v + dv, q) - ref(S, K, T, r, v - dv, q)) / (2 * dv) / 100
    theta = -(ref(S, K, T + dt, r, v, q) - ref(S, K, T - dt, r, v, q)) / (2 * dt) / 365
    rho = (ref(S, K, T, r + dv, v, q) - ref(S, K, T, r - dv, v, q)) / (2 * dv) / 100
    greekerr = max(
        greekerr,
        *[
            abs(g[k] - x)
            for k, x in [
                ("call_delta", delta),
                ("gamma", gamma),
                ("vega", vega),
                ("call_theta", theta),
                ("call_rho", rho),
            ]
        ],
    )
    if c > 1e-6 and c < S * math.exp(-q * T) - 1e-6:
        iverr = max(iverr, abs(implied_volatility(c, S, K, T, r, "call", q) - v))
result = {
    "cases": 500,
    "max_price_error": err,
    "max_parity_error": parity,
    "max_full_precision_greek_finite_difference_error": greekerr,
    "max_iv_error": iverr,
    "benchmark": BlackScholes(100, 100, 1, 0.05, 0.2).greeks(),
}
with TestClient(app, raise_server_exceptions=False) as client:
    result["api_health"] = client.get("/health").status_code
    result["legacy_market_route"] = client.get(
        "/api/v1/market/options/AAPL"
    ).status_code
    for label, data in [
        ("normal", dict(S=100, K=100, T=1, r=0.05, sigma=0.2)),
        ("overflow", dict(S=100, K=100, T=1000, r=-1000, sigma=0.2)),
        ("underflow_ratio", dict(S=1e-300, K=1e300, T=1, r=0.05, sigma=0.2)),
    ]:
        response = client.post("/api/v1/options/price", json=data)
        result[label] = {"status": response.status_code, "body": response.text[:500]}
for S, K in [(1e300, 1e-300), (1e-300, 1e300)]:
    try:
        result[f"extreme_{S}"] = {
            "call": BlackScholes(S, K, 1, 0.05, 0.2).call_price(),
            "put": BlackScholes(S, K, 1, 0.05, 0.2).put_price(),
        }
    except Exception as exc:
        result[f"extreme_{S}"] = {"exception": str(exc)}
print(json.dumps(result, indent=2))

assert result["max_price_error"] < 1e-10
assert result["max_parity_error"] < 1e-10
assert result["max_iv_error"] < 1e-7
assert result["max_full_precision_greek_finite_difference_error"] < 1e-6
assert result["normal"]["status"] == 200
assert result["overflow"]["status"] == 422
assert result["underflow_ratio"]["status"] == 200
