-- Private EODHD personal-use price snapshots; provision manually in Neon.
-- Separate from EarningsAPI's independent seven-call weekly ledger.
CREATE TABLE IF NOT EXISTS eodhd_daily_budget (
    utc_day DATE PRIMARY KEY,
    calls INTEGER NOT NULL DEFAULT 0 CHECK (calls BETWEEN 0 AND 18)
);
CREATE TABLE IF NOT EXISTS eodhd_prices_cache (
    symbol TEXT PRIMARY KEY,
    adjusted_payload JSONB,
    fetched_at TIMESTAMPTZ,
    next_attempt TIMESTAMPTZ NOT NULL,
    CHECK (symbol ~ '^[A-Z0-9.-]{1,32}$')
);
-- Runtime app role needs SELECT/INSERT/UPDATE on these two tables only.
-- Avoid setting search_path or granting access to unrelated app tables.
