CREATE TABLE IF NOT EXISTS exchanges (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL,
    country     VARCHAR(10)  NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS companies (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(20)  NOT NULL,
    exchange_id INTEGER      NOT NULL REFERENCES exchanges(id),
    full_name   VARCHAR(255) NOT NULL,
    sector      VARCHAR(100),
    industry    VARCHAR(100),
    UNIQUE (ticker, exchange_id)
);

CREATE TABLE IF NOT EXISTS company_categories (
    company_id  INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (company_id, category_id)
);

CREATE TABLE IF NOT EXISTS daily_quotes (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER   NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    date        DATE      NOT NULL,
    open        NUMERIC(12, 4),
    high        NUMERIC(12, 4),
    low         NUMERIC(12, 4),
    close       NUMERIC(12, 4),
    volume      BIGINT,
    UNIQUE (company_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_quotes_date_company
    ON daily_quotes (date, company_id);

CREATE TABLE IF NOT EXISTS indicators (
    id              SERIAL PRIMARY KEY,
    company_id      INTEGER       NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    date            DATE          NOT NULL,
    sma_10d         NUMERIC(12, 4),
    sma_20d         NUMERIC(12, 4),
    sma_50d         NUMERIC(12, 4),
    sma_200d        NUMERIC(12, 4),
    obv_100d        NUMERIC(20, 4),
    adr_30d         NUMERIC(12, 4),
    atr_30d         NUMERIC(12, 4),
    rs_value        NUMERIC(12, 4),
    avg_volume_50d  NUMERIC(20, 2),
    avg_turnover_50d NUMERIC(30, 2),
    UNIQUE (company_id, date)
);

CREATE TABLE IF NOT EXISTS signals (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER      NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    date        DATE         NOT NULL,
    signal_type VARCHAR(100) NOT NULL,
    value       SMALLINT     NOT NULL CHECK (value IN (1, -1)),
    UNIQUE (company_id, date, signal_type)
);

CREATE TABLE IF NOT EXISTS signal_effectiveness (
    id                SERIAL PRIMARY KEY,
    signal_id         INTEGER       NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    close_at_signal   NUMERIC(12, 4) NOT NULL,
    return_10d        NUMERIC(10, 4),
    return_20d        NUMERIC(10, 4),
    return_50d        NUMERIC(10, 4),
    drawdown_failed   BOOLEAN DEFAULT FALSE,
    low_10d           NUMERIC(12, 4),
    high_10d          NUMERIC(12, 4)
);

CREATE TABLE IF NOT EXISTS signal_statistics (
    id            SERIAL PRIMARY KEY,
    signal_type   VARCHAR(100) NOT NULL,
    company_id    INTEGER      REFERENCES companies(id) ON DELETE CASCADE,
    exchange_id   INTEGER      REFERENCES exchanges(id) ON DELETE CASCADE,
    year          SMALLINT     NOT NULL,
    occurrences   INTEGER      NOT NULL DEFAULT 0,
    positive_count INTEGER     NOT NULL DEFAULT 0,
    success_rate  NUMERIC(6, 4),
    avg_return    NUMERIC(10, 4),
    UNIQUE (signal_type, company_id, exchange_id, year)
);
