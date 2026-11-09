-- Run once against the private, persistent PostgreSQL database before enabling
-- the EarningsAPI calendar. Use one shared database for every app replica.
-- Restrict CREATE/ALTER permissions after initial provisioning.
CREATE TABLE IF NOT EXISTS earnings_budget (
    month TEXT PRIMARY KEY,
    calls INTEGER NOT NULL DEFAULT 0 CHECK (calls >= 0 AND calls <= 250)
);
CREATE TABLE IF NOT EXISTS earnings_weeks (
    week TEXT PRIMARY KEY,
    next_attempt DOUBLE PRECISION NOT NULL,
    payload TEXT,
    fetched DOUBLE PRECISION
);
-- Keep historical budget rows for auditability. Do not truncate between deploys.
