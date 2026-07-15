DROP TABLE IF EXISTS pipeline_runs CASCADE;
DROP TABLE IF EXISTS signal_statistics CASCADE;
DROP TABLE IF EXISTS signal_effectiveness CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS indicators CASCADE;
DROP TABLE IF EXISTS indicators_old CASCADE;
DROP TABLE IF EXISTS daily_quotes CASCADE;
DROP TABLE IF EXISTS instrument_categories CASCADE;
DROP TABLE IF EXISTS instruments CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS exchanges CASCADE;

CREATE TABLE exchanges (
    id      SERIAL PRIMARY KEY,
    code    VARCHAR(20)  NOT NULL UNIQUE,
    name    VARCHAR(255) NOT NULL,
    country VARCHAR(10)  NOT NULL,
    active  BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE data_sources (
    id   SERIAL PRIMARY KEY,
    code VARCHAR(50)  NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE categories (
    id   SERIAL PRIMARY KEY,
    name   VARCHAR(100) NOT NULL UNIQUE,
    source VARCHAR(20)
);

CREATE TABLE instruments (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(20)  NOT NULL,
    exchange_id     INTEGER      NOT NULL REFERENCES exchanges(id),
    full_name       VARCHAR(255) NOT NULL,
    instrument_type VARCHAR(10)  NOT NULL CHECK (instrument_type IN ('stock', 'index', 'etf')),
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    valid           BOOLEAN      NOT NULL DEFAULT TRUE,
    dt_from         DATE,
    dt_to           DATE,
    market_cap      REAL,
    UNIQUE (ticker, exchange_id)
);

CREATE TABLE instrument_categories (
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (instrument_id, category_id)
);

CREATE TABLE daily_quotes (
    instrument_id  INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    dt             DATE    NOT NULL,
    open_price     REAL,
    high_price     REAL,
    low_price      REAL,
    close_price    REAL,
    volume         BIGINT,
    data_source_id INTEGER NOT NULL REFERENCES data_sources(id),
    UNIQUE (instrument_id, dt)
) PARTITION BY RANGE (dt);

CREATE TABLE indicators_old (
    id              SERIAL PRIMARY KEY,
    instrument_id   INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date            DATE    NOT NULL,
    indicator_name  VARCHAR(50) NOT NULL,
    value           REAL,
    parameters      VARCHAR(255),
    UNIQUE (instrument_id, date, indicator_name, parameters)
);

CREATE TABLE indicators (
    instrument_id  INTEGER NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    dt             DATE    NOT NULL,
    sma_10         REAL,
    sma_20         REAL,
    sma_50         REAL,
    sma_200        REAL,
    obv_100        REAL,
    adr_30         REAL,
    atr_30         REAL,
    rs             REAL,
    avg_volume_30  REAL,
    avg_volume_50  REAL,
    avg_turnover_50 REAL,
    ichimoku_tenkan_sen_9    REAL,
    ichimoku_kijun_sen_26    REAL,
    ichimoku_senkou_span_a_26 REAL,
    ichimoku_senkou_span_b_26 REAL,
    UNIQUE (instrument_id, dt)
);

CREATE TABLE signals (
    id             SERIAL PRIMARY KEY,
    instrument_id  INTEGER      NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date           DATE         NOT NULL,
    signal_type    VARCHAR(100) NOT NULL,
    value          SMALLINT     NOT NULL CHECK (value IN (1, -1)),
    UNIQUE (instrument_id, date, signal_type)
);

CREATE TABLE signal_effectiveness (
    id              SERIAL PRIMARY KEY,
    signal_id       INTEGER       NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    close_at_signal REAL          NOT NULL,
    return_10d      REAL,
    return_20d      REAL,
    return_50d      REAL,
    return_100d     REAL,
    drawdown_failed BOOLEAN DEFAULT FALSE,
    low_10d         REAL,
    high_10d        REAL
);

CREATE TABLE pipeline_runs (
    id           SERIAL PRIMARY KEY,
    step         VARCHAR(50)  NOT NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'running',
    started_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    finished_at  TIMESTAMP,
    rows_affected INTEGER
);

CREATE TABLE signal_statistics (
    id             SERIAL PRIMARY KEY,
    signal_type    VARCHAR(100) NOT NULL,
    instrument_id  INTEGER      REFERENCES instruments(id) ON DELETE CASCADE,
    exchange_id    INTEGER      REFERENCES exchanges(id) ON DELETE CASCADE,
    year           SMALLINT     NOT NULL,
    occurrences    INTEGER      NOT NULL DEFAULT 0,
    positive_count INTEGER      NOT NULL DEFAULT 0,
    success_rate   REAL,
    avg_return     REAL,
    UNIQUE (signal_type, instrument_id, exchange_id, year)
);

CREATE OR REPLACE VIEW v_daily_quotes AS
SELECT e.code, i.ticker, i.full_name
     , i.industry, i.sector
     , dq.dt, dq.open_price, dq.high_price, dq.low_price, dq.close_price, dq.volume
     , round(dq.close_price * dq.volume) turnover
FROM daily_quotes dq
         JOIN instruments i ON i.id = dq.instrument_id
         JOIN exchanges e ON e.id = i.exchange_id;

create or replace view v_instrument_dates as
select i.id, e.code exchange, i.full_name, min(dq.dt) min_dt, max(dq.dt) max_dt, count(dq.instrument_id) quotes_count
from instruments i
         join exchanges e on e.id = i.exchange_id
         left join daily_quotes dq on dq.instrument_id = i.id
group by i.id, e.code, i.full_name;

create or replace view v_instrument_categories as
select e.code  , i.ticker, i.full_name, c."name"
from instruments i
         join exchanges e on e.id = i.exchange_id
         join instrument_categories ic on ic.instrument_id = i.id
         join categories c on c.id = ic.category_id;
