-- Stock Analysis System – Unified MySQL Schema
-- Replaces schema.sql and database_schema.sql
-- Version: 1.0
-- This script creates all tables, indexes, views, seed data, and a placeholder stored procedure.
-- Run with: mysql -u <user> -p < stock_analysis_schema.sql>

-- ==========================================================
-- Exchanges table (catalog of exchanges)
-- ==========================================================
CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL COMMENT 'GPW, NASDAQ, NYSE, AMEX, etc.',
    name VARCHAR(255) NOT NULL,
    country VARCHAR(50) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'USD',
    active_since DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE INDEX idx_exchanges_code ON exchanges(code);

-- ==========================================================
-- Classifications (IBD‑style thematic categories)
-- ==========================================================
CREATE TABLE IF NOT EXISTS classifications (
    classification_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    ibd_equivalent VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticker_classifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker_id INT NOT NULL,
    classification_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id),
    FOREIGN KEY (classification_id) REFERENCES classifications(classification_id)
);

-- ==========================================================
-- Tickers table (companies and indices)
-- ==========================================================
CREATE TABLE IF NOT EXISTS tickers (
    ticker_id INT AUTO_INCREMENT PRIMARY KEY,
    exchange_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    full_name VARCHAR(500),
    is_index BOOLEAN DEFAULT FALSE COMMENT '1 = index (e.g., WIG20, SPX)',
    sector VARCHAR(100),
    industry VARCHAR(100),
    base_category VARCHAR(100),
    sub_categories JSON,  -- array of tags such as ['AI','Drones']
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_exchange (exchange_id, symbol),
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id)
);

-- ==========================================================
-- Raw price data (one record per day per ticker)
-- ==========================================================
CREATE TABLE IF NOT EXISTS raw_price_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(20,6) NOT NULL CHECK (open >= 0),
    high DECIMAL(20,6) NOT NULL CHECK (high >= 0),
    low  DECIMAL(20,6) NOT NULL CHECK (low  >= 0),
    close DECIMAL(20,6) NOT NULL CHECK (close >= 0),
    volume BIGINT DEFAULT 0,
    adjusted_close DECIMAL(20,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker_id, exchange_id, date)
);
CREATE INDEX idx_raw_price_date_ticker ON raw_price_data(date);

-- ==========================================================
-- Technical indicators (one row per day per ticker)
-- ==========================================================
CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    date DATE NOT NULL,
    sma_10 DECIMAL(20,6),
    sma_20 DECIMAL(20,6),
    sma_50 DECIMAL(20,6),
    sma_200 DECIMAL(20,6),
    obv_100 DECIMAL(20,6),
    adr_30 DECIMAL(20,6),
    atr_30 DECIMAL(20,6),
    avg_volume_50 BIGINT,
    avg_turnover_50 DECIMAL(20,6),
    relative_strength DECIMAL(20,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_indicator (ticker_id, exchange_id, date)
);
CREATE INDEX idx_indicator_date_ticker ON technical_indicators(date);

-- ==========================================================
-- Signals (generated trading signals)
-- ==========================================================
CREATE TABLE IF NOT EXISTS signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    exchange_id INT NOT NULL,
    ticker_id INT NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    direction TINYINT NOT NULL CHECK (direction IN (-1,0,1)),
    confidence FLOAT DEFAULT 1.0,
    trigger_value FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id),
    UNIQUE KEY uq_signal (exchange_id, ticker_id, signal_date, signal_type)
);
CREATE INDEX idx_signals_date_type ON signals(signal_date, signal_type);

-- ==========================================================
-- Signal effectiveness (back‑testing results)
-- ==========================================================
CREATE TABLE IF NOT EXISTS signal_effectiveness (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    exchange_id INT NOT NULL,
    ticker_id INT NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    direction TINYINT NOT NULL CHECK (direction IN (-1,1)),
    return_10d DECIMAL(20,6),
    return_20d DECIMAL(20,6),
    return_50d DECIMAL(20,6),
    drawdown_triggered BOOLEAN DEFAULT FALSE,
    success_flag BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);
CREATE INDEX idx_effectiveness ON signal_effectiveness(signal_date, ticker_id);

-- ==========================================================
-- Signal statistics (aggregated per ticker/year)
-- ==========================================================
CREATE TABLE IF NOT EXISTS signal_statistics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker_id INT NOT NULL,
    exchange_id INT NOT NULL,
    calendar_year INT NOT NULL,
    signal_type VARCHAR(50) NOT NULL,
    total_signals INT DEFAULT 0,
    positive_signals INT DEFAULT 0,
    negative_signals INT DEFAULT 0,
    success_rate DECIMAL(5,2),
    avg_return_10d DECIMAL(20,6),
    avg_return_20d DECIMAL(20,6),
    avg_return_50d DECIMAL(20,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_stats (ticker_id, exchange_id, calendar_year, signal_type)
);

-- ==========================================================
-- Data collection log (monitoring ingestion jobs)
-- ==========================================================
CREATE TABLE IF NOT EXISTS data_collection_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    collection_date DATE NOT NULL UNIQUE,
    status ENUM('PENDING','IN_PROGRESS','COMPLETED','FAILED') DEFAULT 'PENDING',
    exchanges_processed INT DEFAULT 0,
    tickers_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================================
-- System configuration (key/value pairs)
-- ==========================================================
CREATE TABLE IF NOT EXISTS system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================================
-- Seed data – exchanges, classifications, system config
-- ==========================================================
INSERT IGNORE INTO exchanges (code, name, country, currency_code, active_since) VALUES
    ('GPW',    'Warsaw Stock Exchange',               'Poland', 'PLN', '2009-11-05'),
    ('GC',     'NewConnect (Capital Market)',         'Poland', 'PLN', '2004-06-30'),
    ('NASDAQ', 'NASDAQ Stock Market',                  'USA',    'USD', '1971-02-05'),
    ('NYSE',   'New York Stock Exchange',              'USA',    'USD', '1792-03-20'),
    ('AMEX',   'American Stock Exchange (NYSE American)','USA','USD', '1943-08-06');

INSERT IGNORE INTO classifications (category_name, description, ibd_equivalent) VALUES
    ('AI',               'Sztuczna inteligencja i machine learning',            'Technology - AI'),
    ('Drones',           'Producenci dronów i systemów bezzałogowych',         'Aerospace & Defense'),
    ('Silver Mining',    'Wydobycie srebra',                                   'Basic Materials'),
    ('Gold Mining',      'Wydobycie złota',                                     'Precious Metals'),
    ('SMR',              'Small Modular Reactors – energia jądrowa',           'Utilities'),
    ('Memory RAM',       'Produkcja pamięci RAM i półprzewodników',            'Semiconductors'),
    ('Space Industry',   'Przemysł kosmiczny',                                 'Aerospace & Defense'),
    ('Biotech',          'Technologia biologiczna',                             'Healthcare'),
    ('Renewable Energy', 'Odnawialna energia',                                 'Utilities - Renewable'),
    ('Fintech',          'Finanse technologiczne',                             'Financial Services');

INSERT IGNORE INTO system_config (config_key, config_value, description) VALUES
    ('DATA_START_DATE', '2020-01-01', 'Earliest date for data collection'),
    ('UPDATE_FREQUENCY','DAILY',     'How often to pull new market data'),
    ('BULLISH_BREAK_THRESHOLD','1.7','Percent change threshold for bullish break'),
    ('SIGNAL_HOLD_PERIOD_1','10','Days to hold after signal for return calc'),
    ('SIGNAL_HOLD_PERIOD_2','20','Days to hold after signal for return calc'),
    ('SIGNAL_HOLD_PERIOD_3','50','Days to hold after signal for return calc');

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

-- ==========================================================
-- Placeholder stored procedure for indicator calculation (logic in Python)
-- ==========================================================
DELIMITER //
CREATE PROCEDURE sp_calculate_indicators(
    IN p_ticker_id INT,
    IN p_exchange_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    -- Stub: currently does nothing. Real calculations are performed in Python.
    SELECT 'Placeholder procedure executed' AS msg;
END //
DELIMITER ;

-- End of unified schema
