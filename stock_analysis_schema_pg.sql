-- PostgreSQL schema for Stock Analysis System
-- Replaces MySQL schema with PostgreSQL‑compatible definitions
-- Version: 1.0 (PostgreSQL)

-- Enable extension for JSONB if not already available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================================
-- Exchanges table
-- ==========================================================
CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(50) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'USD',
    active_since DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_exchanges_code ON exchanges(code);

-- ==========================================================
-- Classifications (IBD‑style categories)
-- ==========================================================
CREATE TABLE IF NOT EXISTS classifications (
    classification_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    ibd_equivalent VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticker_classifications (
    id SERIAL PRIMARY KEY,
    ticker_id INT NOT NULL,
    classification_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id),
    FOREIGN KEY (classification_id) REFERENCES classifications(classification_id)
);

-- ==========================================================
-- Tickers table
-- ==========================================================
CREATE TABLE IF NOT EXISTS tickers (
    ticker_id SERIAL PRIMARY KEY,
    exchange_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    full_name VARCHAR(500),
    is_index BOOLEAN DEFAULT FALSE,
    sector VARCHAR(100),
    industry VARCHAR(100),
    base_category VARCHAR(100),
    sub_categories JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exchange_id, symbol),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id)
);

-- ==========================================================
-- Raw price data (one row per day per ticker)
-- ==========================================================
CREATE TABLE IF NOT EXISTS raw_price_data (
    id BIGSERIAL PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(20,6) NOT NULL CHECK (open >= 0),
    high NUMERIC(20,6) NOT NULL CHECK (high >= 0),
    low  NUMERIC(20,6) NOT NULL CHECK (low  >= 0),
    close NUMERIC(20,6) NOT NULL CHECK (close >= 0),
    volume BIGINT DEFAULT 0,
    adjusted_close NUMERIC(20,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, exchange_id, date)
);
CREATE INDEX IF NOT EXISTS idx_raw_price_date_ticker ON raw_price_data(date);

-- ==========================================================
-- Technical indicators
-- ==========================================================
CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    date DATE NOT NULL,
    sma_10 NUMERIC(20,6),
    sma_20 NUMERIC(20,6),
    sma_50 NUMERIC(20,6),
    sma_200 NUMERIC(20,6),
    obv_100 NUMERIC(20,6),
    adr_30 NUMERIC(20,6),
    atr_30 NUMERIC(20,6),
    avg_volume_50 BIGINT,
    avg_turnover_50 NUMERIC(20,6),
    relative_strength NUMERIC(20,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, exchange_id, date)
);
CREATE INDEX IF NOT EXISTS idx_indicator_date_ticker ON technical_indicators(date);

-- ==========================================================
-- Signals
-- ==========================================================
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    exchange_id INT NOT NULL,
    ticker_id INT NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    direction SMALLINT CHECK (direction IN (-1,0,1)) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    trigger_value FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exchange_id, ticker_id, signal_date, signal_type),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);
CREATE INDEX IF NOT EXISTS idx_signals_date_type ON signals(signal_date, signal_type);

-- ==========================================================
-- Signal effectiveness
-- ==========================================================
CREATE TABLE IF NOT EXISTS signal_effectiveness (
    id BIGSERIAL PRIMARY KEY,
    exchange_id INT NOT NULL,
    ticker_id INT NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    direction SMALLINT CHECK (direction IN (-1,1)) NOT NULL,
    return_10d NUMERIC(20,6),
    return_20d NUMERIC(20,6),
    return_50d NUMERIC(20,6),
    drawdown_triggered BOOLEAN DEFAULT FALSE,
    success_flag BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);
CREATE INDEX IF NOT EXISTS idx_effectiveness ON signal_effectiveness(signal_date, ticker_id);

-- ==========================================================
-- Signal statistics
-- ==========================================================
CREATE TABLE IF NOT EXISTS signal_statistics (
    id BIGSERIAL PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    calendar_year INT NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    total_signals INT DEFAULT 0,
    positive_signals INT DEFAULT 0,
    negative_signals INT DEFAULT 0,
    success_rate NUMERIC(5,2),
    avg_return_10d NUMERIC(20,6),
    avg_return_20d NUMERIC(20,6),
    avg_return_50d NUMERIC(20,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, exchange_id, calendar_year, signal_type)
);

-- ==========================================================
-- Data collection log
-- ==========================================================
CREATE TABLE IF NOT EXISTS data_collection_log (
    id BIGSERIAL PRIMARY KEY,
    collection_date DATE NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING','IN_PROGRESS','COMPLETED','FAILED')),
    exchanges_processed INT DEFAULT 0,
    tickers_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- System configuration
-- ==========================================================
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- Seed data
-- ==========================================================
INSERT INTO exchanges (code, name, country, currency_code, active_since) VALUES
    ('GPW','Warsaw Stock Exchange','Poland','PLN','2009-11-05'),
    ('GC','NewConnect (Capital Market)','Poland','PLN','2004-06-30'),
    ('NASDAQ','NASDAQ Stock Market','USA','USD','1971-02-05'),
    ('NYSE','New York Stock Exchange','USA','USD','1792-03-20'),
    ('AMEX','American Stock Exchange (NYSE American)','USA','USD','1943-08-06')
    ON CONFLICT (code) DO NOTHING;

INSERT INTO classifications (category_name, description, ibd_equivalent) VALUES
    ('AI','Sztuczna inteligencja i machine learning','Technology - AI'),
    ('Drones','Producenci dronów i systemów bezzałogowych','Aerospace & Defense'),
    ('Silver Mining','Wydobycie srebra','Basic Materials'),
    ('Gold Mining','Wydobycie złota','Precious Metals'),
    ('SMR','Small Modular Reactors – energia jądrowa','Utilities'),
    ('Memory RAM','Produkcja pamięci RAM i półprzewodników','Semiconductors'),
    ('Space Industry','Przemysł kosmiczny','Aerospace & Defense'),
    ('Biotech','Technologia biologiczna','Healthcare'),
    ('Renewable Energy','Odnawialna energia','Utilities - Renewable'),
    ('Fintech','Finanse technologiczne','Financial Services')
    ON CONFLICT (category_name) DO NOTHING;

INSERT INTO system_config (config_key, config_value, description) VALUES
    ('DATA_START_DATE','2020-01-01','Earliest date for data collection'),
    ('UPDATE_FREQUENCY','DAILY','How often to pull new market data'),
    ('BULLISH_BREAK_THRESHOLD','1.7','Percent change threshold for bullish break'),
    ('SIGNAL_HOLD_PERIOD_1','10','Days to hold after signal for return calc'),
    ('SIGNAL_HOLD_PERIOD_2','20','Days to hold after signal for return calc'),
    ('SIGNAL_HOLD_PERIOD_3','50','Days to hold after signal for return calc')
    ON CONFLICT (config_key) DO NOTHING;

-- ==========================================================
-- Views for convenient lookup
-- ==========================================================
CREATE OR REPLACE VIEW v_quote_lookup AS
SELECT
    rp.date AS quote_date,
    e.code AS exchange_code,
    t.symbol AS ticker_symbol,
    t.full_name,
    rp.open, rp.high, rp.low, rp.close, rp.volume
FROM raw_price_data rp
JOIN exchanges e ON rp.exchange_id = e.exchange_id
JOIN tickers t ON rp.ticker_id = t.ticker_id;

CREATE OR REPLACE VIEW vw_ticker_daily_summary AS
SELECT
    rp.date,
    t.ticker_id,
    t.symbol,
    t.full_name,
    e.code AS exchange_code,
    rp.open, rp.high, rp.low, rp.close, rp.volume,
    ti.sma_10, ti.sma_20, ti.sma_50, ti.sma_200,
    ti.avg_volume_50,
    ti.atr_30
FROM raw_price_data rp
JOIN tickers t ON rp.ticker_id = t.ticker_id
JOIN exchanges e ON rp.exchange_id = e.exchange_id
LEFT JOIN technical_indicators ti ON ti.ticker_id = t.ticker_id AND ti.exchange_id = e.exchange_id AND ti.date = rp.date;
