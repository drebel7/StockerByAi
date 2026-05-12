-- Stock Market Data System - Database Schema
-- Version 1.0

-- ============================================
-- EXCHANGE CATALOG
-- ============================================
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,           -- GPW, NASDAQ, NYSE, AMEX
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    active_since DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exchanges_code ON exchanges(code);

-- ============================================
-- TICKER REGISTRY (companies + indices)
-- ============================================
CREATE TABLE IF NOT EXISTS tickers (
    id INTEGER PRIMARY KEY,
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    ticker_symbol TEXT UNIQUE NOT NULL,  -- e.g., WIG20, AAPL
    is_index BOOLEAN DEFAULT FALSE,
    full_name TEXT,
    sector TEXT,
    industry TEXT,
    base_category TEXT,
    sub_categories TEXT,                   -- JSON array of tags (drones, AI, etc.)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE UNIQUE INDEX idx_tickers_exchange_symbol 
    ON tickers(exchange_id, ticker_symbol);

-- ============================================
-- DAILY QUOTES (1 record per day per company)
-- ============================================
CREATE TABLE IF NOT EXISTS daily_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_date DATE NOT NULL,
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    open REAL NOT NULL CHECK(open >= 0),
    high REAL NOT NULL CHECK(high >= 0),
    low REAL NOT NULL CHECK(low >= 0),
    close REAL NOT NULL CHECK(close >= 0),
    volume INTEGER DEFAULT 0,
    adjusted_close REAL,                   -- For splits/dividends
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Fast search index: date + ticker
CREATE UNIQUE INDEX idx_quotes_date_ticker 
    ON daily_quotes(quote_date, exchange_id, ticker_id);

-- ============================================
-- TECHNICAL INDICATORS (1 record per day per company)
-- ============================================
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_date DATE NOT NULL,
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    sma_10 REAL,
    sma_20 REAL,
    sma_50 REAL,
    sma_200 REAL,
    obv_100 REAL,                          -- On Balance Volume
    adr_30 REAL,                           -- Average Daily Range
    atr_30 REAL,                           -- Average True Range
    avg_volume_50 REAL,
    avg_turnover_50 REAL,
    relative_strength REAL,                -- vs index/sector
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE UNIQUE INDEX idx_indicators_date_ticker 
    ON indicators(quote_date, exchange_id, ticker_id);

-- ============================================
-- SIGNALS (positive/negative signals only)
-- ============================================
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_date DATE NOT NULL,
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    signal_type TEXT NOT NULL,             -- e.g., 'volume_spike', 'rsi_oversold'
    direction INTEGER NOT NULL CHECK(direction IN (-1, 0, 1)),
    confidence REAL DEFAULT 1.0,
    trigger_value REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_date_type 
    ON signals(signal_date, exchange_id, ticker_id, signal_type);

-- ============================================
-- SIGNAL EFFECTIVENESS (for backtesting)
-- ============================================
CREATE TABLE IF NOT EXISTS signal_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_date DATE NOT NULL,
    exchange_id INTEGER NOT NULL REFERENCES exchanges(id),
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    signal_type TEXT NOT NULL,
    direction INTEGER NOT NULL,
    return_10d REAL,                       -- Return after 10 days
    return_20d REAL,
    return_50d REAL,
    drawdown_triggered BOOLEAN DEFAULT FALSE,
    success_flag BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SIGNAL STATISTICS (aggregates)
-- ============================================
CREATE TABLE IF NOT EXISTS signal_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id),
    exchange_code TEXT NOT NULL,
    calendar_year INTEGER NOT NULL,
    signal_type TEXT NOT NULL,
    total_signals INTEGER DEFAULT 0,
    positive_signals INTEGER DEFAULT 0,
    negative_signals INTEGER DEFAULT 0,
    success_rate REAL,
    avg_return_10d REAL,
    avg_return_20d REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker_id, exchange_code, calendar_year, signal_type)
);

-- ============================================
-- INITIALIZATION DATA
-- ============================================
INSERT OR IGNORE INTO exchanges (code, name, country, base_currency, active_since) VALUES
('GPW', 'Warsaw Stock Exchange', 'Poland', 'PLN', DATE('2009-11-05')),
('NEWCON', 'NewConnect', 'Poland', 'PLN', DATE('2004-06-30')),
('NASDAQ', 'NASDAQ Stock Market', 'USA', 'USD', DATE('1971-02-05')),
('NYSE', 'New York Stock Exchange', 'USA', 'USD', DATE('1792-03-20')),
('AMEX', 'American Stock Exchange', 'USA', 'USD', DATE('1943-08-06'));

-- ============================================
-- TRIGGER FOR AUTO-UPDATED TIMESTAMPS
-- ============================================
CREATE TRIGGER IF NOT EXISTS tickers_updated_before 
    BEFORE UPDATE ON tickers
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'updated_at will be set automatically');
END;

-- ============================================
-- VIEW FOR FAST QUOTE LOOKUP
-- ============================================
CREATE VIEW IF NOT EXISTS v_quote_lookup AS
SELECT 
    dq.quote_date,
    e.code as exchange,
    t.ticker_symbol,
    t.full_name,
    dq.open, dq.high, dq.low, dq.close, dq.volume
FROM daily_quotes dq
JOIN exchanges e ON dq.exchange_id = e.id
JOIN tickers t ON dq.ticker_id = t.id;
