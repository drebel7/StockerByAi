-- ============================================
-- SYSTEM ANALIZY GIEŁDOWEJ - SCHEMA SQL
-- ============================================

-- Create Database
CREATE DATABASE IF NOT EXISTS `stock_analysis_db`;
USE `stock_analysis_db`;

-- =============================================
-- TABELA: EXCHANGES (Giełdy)
-- =============================================
DROP TABLE IF EXISTS exchanges;
CREATE TABLE exchanges (
    exchange_id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(10) UNIQUE NOT NULL COMMENT 'GPW, NASDAQ, NYSE, AMEX',
    name VARCHAR(255) NOT NULL,
    country VARCHAR(50),
    currency_code CHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================
-- TABELA: TICKERS (Spółki i Indeksy)
-- =============================================
DROP TABLE IF EXISTS tickers;
CREATE TABLE tickers (
    ticker_id INT PRIMARY KEY AUTO_INCREMENT,
    exchange_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL COMMENT 'np. GEW, ADR, QQQ',
    full_name VARCHAR(500),
    is_index BOOLEAN DEFAULT FALSE COMMENT '1 = indeks (WIG20, SPX)',
    sector_code VARCHAR(20) COMMENT 'Sektor bazowy',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id)
);

-- =============================================
-- TABELA: CLASSIFICATIONS (Klasyfikacje tematyczne)
-- IBD-inspired categories
-- =============================================
DROP TABLE IF EXISTS classifications;
CREATE TABLE classifications (
    classification_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    ibd_equivalent VARCHAR(50) COMMENT 'Odniesienie do IBD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- TABELA: TICKER_CLASSIFICATIONS (Przypisanie kategorii)
-- =============================================
DROP TABLE IF EXISTS ticker_classifications;
CREATE TABLE ticker_classifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    classification_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id),
    FOREIGN KEY (classification_id) REFERENCES classifications(classification_id)
);

-- =============================================
-- TABELA: RAW_PRICE_DATA (Surowe dane giełdowe)
-- =============================================
DROP TABLE IF EXISTS raw_price_data;
CREATE TABLE raw_price_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    exchange_code VARCHAR(10) NOT NULL COMMENT 'Dla spółek z wielu giełd',
    date DATE NOT NULL COMMENT 'Data zamknięcia',
    open DECIMAL(20,6) NOT NULL,
    high DECIMAL(20,6) NOT NULL,
    low DECIMAL(20,6) NOT NULL,
    close DECIMAL(20,6) NOT NULL,
    volume BIGINT DEFAULT 0,
    ticker VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker_id, exchange_code, date),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);

-- =============================================
-- TABELA: TECHNICAL_INDICATORS (Wskaźniki techniczne)
-- =============================================
DROP TABLE IF EXISTS technical_indicators;
CREATE TABLE technical_indicators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    exchange_code VARCHAR(10),
    date DATE NOT NULL COMMENT 'Data zamknięcia',
    -- SMA
    sma_10 DECIMAL(20,6) DEFAULT NULL,
    sma_20 DECIMAL(20,6) DEFAULT NULL,
    sma_50 DECIMAL(20,6) DEFAULT NULL,
    sma_200 DECIMAL(20,6) DEFAULT NULL,
    -- OBV
    obv_100 DECIMAL(20,6) DEFAULT NULL,
    -- ADR (Average Daily Return)
    adr_30 DECIMAL(20,6) DEFAULT NULL,
    -- ATR (Average True Range)
    atr_30 DECIMAL(20,6) DEFAULT NULL,
    -- RS (Relative Strength) - odniesienie do indeksu/sektora
    rs_index DECIMAL(20,4) DEFAULT NULL COMMENT 'RS vs WIG20',
    rs_sector DECIMAL(20,4) DEFAULT NULL COMMENT 'RS vs sektor',
    -- Average Volume
    avg_volume_50 BIGINT DEFAULT NULL,
    avg_turnover_50 DECIMAL(20,6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker_id, exchange_code, date),
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);

-- =============================================
-- TABELA: SIGNALS (Wygenerowane sygnały)
-- =============================================
DROP TABLE IF EXISTS signals;
CREATE TABLE signals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    exchange_code VARCHAR(10),
    signal_date DATE NOT NULL COMMENT 'Data wystąpienia sygnału',
    signal_value SMALLINT NOT NULL COMMENT '1 = pozytywny, -1 = negatywny',
    signal_type ENUM('VOLUME_SPIKE', 'BREAKOUT', 'BREAKDOWN', 
                     'CROSSOVER_BULLISH', 'CROSSOVER_BEARISH', 
                     'PATTERN_BULLISH', 'PATTERN_BEARISH') NOT NULL,
    description TEXT COMMENT 'Opis warunków sygnału',
    open_price DECIMAL(20,6),
    close_price DECIMAL(20,6),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);

-- =============================================
-- TABELA: SIGNAL_EFFECTIVENESS (Skuteczność sygnałów)
-- =============================================
DROP TABLE IF EXISTS signal_effectiveness;
CREATE TABLE signal_effectiveness (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    exchange_code VARCHAR(10),
    signal_date DATE NOT NULL COMMENT 'Data sygnału',
    min_price DECIMAL(20,6) NOT NULL COMMENT 'Minimum z dnia sygnału (dla bullish)',
    max_price DECIMAL(20,6) NOT NULL COMMENT 'Maksimum z dnia sygnału (dla bearish)',
    result_10d DECIMAL(20,4) DEFAULT NULL COMMENT 'Zwrot po 10 dniach',
    result_20d DECIMAL(20,4) DEFAULT NULL COMMENT 'Zwrot po 20 dniach',
    result_50d DECIMAL(20,4) DEFAULT NULL COMMENT 'Zwrot po 50 dniach',
    valid BOOLEAN DEFAULT TRUE,
    invalid_reason VARCHAR(255) COMMENT 'Dlaczego sygnał jest nieudany',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(ticker_id)
);

-- =============================================
-- TABELA: SIGNAL_STATISTICS (Statystyki sygnałów)
-- =============================================
DROP TABLE IF EXISTS signal_statistics;
CREATE TABLE signal_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    exchange_code VARCHAR(10),
    year INT NOT NULL COMMENT 'Rok kalendarzowy',
    signal_type ENUM('VOLUME_SPIKE', 'BREAKOUT', 'BREAKDOWN', 
                     'CROSSOVER_BULLISH', 'CROSSOVER_BEARISH', 
                     'PATTERN_BULLISH', 'PATTERN_BEARISH') NOT NULL,
    total_count INT DEFAULT 0 COMMENT 'Liczba sygnałów',
    positive_signals INT DEFAULT 0 COMMENT 'Pozytywne (1)',
    negative_signals INT DEFAULT 0 COMMENT 'Negatywne (-1)',
    success_count INT DEFAULT 0 COMMENT 'Udane sygnały',
    failed_count INT DEFAULT 0 COMMENT 'Nieudane sygnały',
    success_rate DECIMAL(5,2) DEFAULT NULL COMMENT 'Skuteczność %',
    avg_return_10d DECIMAL(20,4) DEFAULT NULL,
    avg_return_20d DECIMAL(20,4) DEFAULT NULL,
    avg_return_50d DECIMAL(20,4) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_year_type (ticker_id, year, signal_type)
);

-- =============================================
-- TABELA: DATA_COLLECTION_LOG (Log zbierania danych)
-- =============================================
DROP TABLE IF EXISTS data_collection_log;
CREATE TABLE data_collection_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL UNIQUE,
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    exchanges_count INT DEFAULT 0 COMMENT 'Liczba przetworzonych giełd',
    tickers_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    FOREIGN KEY (date) REFERENCES raw_price_data(date)
);

-- =============================================
-- TABELA: SYSTEM_CONFIG (Konfiguracja systemu)
-- =============================================
DROP TABLE IF EXISTS system_config;
CREATE TABLE system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================
-- WIZARD: Initial Data Load
-- =============================================

INSERT INTO exchanges (code, name, country) VALUES
('GPW', 'Giełda Papierów Wartościowych w Warszawie', 'Poland'),
('GC', 'Giełda Capital Market / NewConnect', 'Poland'),
('NASDAQ', 'NASDAQ Global Select', 'USA'),
('NYSE', 'New York Stock Exchange', 'USA'),
('AMEX', 'NYSE American (AMEX)', 'USA');

INSERT INTO classifications (category_name, description, ibd_equivalent) VALUES
('AI', 'Sztuczna inteligencja i machine learning', 'Technology - AI'),
('Drones', 'Producentów dronów i systemów bezzałogowych', 'Aerospace & Defense'),
('Silver Mining', 'Wydobycie srebra', 'Basic Materials'),
('Gold Mining', 'Wydobycie złota', 'Precious Metals'),
('SMR', 'Small Modular Reactors - energia jądrowa', 'Utilities'),
('Memory RAM', 'Produkcja pamięci RAM i półprzewodników', 'Semiconductors'),
('Space Industry', 'Przemysł kosmiczny', 'Aerospace & Defense'),
('Biotech', 'Technologia biologiczna', 'Healthcare'),
('Renewable Energy', 'Odnawialna energia', 'Utilities - Renewable'),
('Fintech', 'Finanse technologiczne', 'Financial Services');

INSERT INTO system_config (config_key, config_value) VALUES
('DATA_START_DATE', '2020-01-01'),
('UPDATE_FREQUENCY', 'DAILY'),
('BULLISH_BREAK_THRESHOLD', 1.7),
('SIGNAL_HOLD_PERIOD_1', 10),
('SIGNAL_HOLD_PERIOD_2', 20),
('SIGNAL_HOLD_PERIOD_3', 50);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================
CREATE INDEX idx_rpd_date ON raw_price_data(date);
CREATE INDEX idx_rpd_ticker ON raw_price_data(ticker_id);
CREATE INDEX idx_ti_date ON technical_indicators(date);
CREATE INDEX idx_signals_date ON signals(signal_date);
CREATE INDEX idx_effectiveness_signal ON signal_effectiveness(signal_date, ticker_id);

-- =============================================
-- VIEWS FOR ANALYSIS
-- =============================================

DROP VIEW IF EXISTS vw_ticker_daily_summary;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER
VIEW vw_ticker_daily_summary AS 
SELECT 
    rp.date,
    t.ticker_id,
    t.symbol,
    t.full_name,
    e.code as exchange_code,
    rp.open,
    rp.high,
    rp.low,
    rp.close,
    rp.volume,
    ti.sma_10,
    ti.sma_20,
    ti.sma_50,
    ti.sma_200,
    ti.avg_volume_50,
    ti.atr_30
FROM raw_price_data rp
JOIN tickers t ON rp.ticker_id = t.ticker_id
LEFT JOIN exchanges e ON e.code = rp.exchange_code
LEFT JOIN technical_indicators ti ON ti.ticker_id = rp.ticker_id 
    AND ti.date = rp.date
    AND ti.exchange_code = rp.exchange_code;

-- =============================================
-- STORED PROCEDURE: Calculate Technical Indicators
-- =============================================

DELIMITER //

CREATE PROCEDURE sp_calculate_indicators(
    IN p_ticker_id INT,
    IN p_exchange_code VARCHAR(10),
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    DECLARE v_current_close DECIMAL(20,6);
    DECLARE v_prev_close DECIMAL(20,6);  -- dla ATR
    
    SELECT close INTO v_current_close
    FROM raw_price_data 
    WHERE ticker_id = p_ticker_id AND exchange_code = p_exchange_code
    ORDER BY date DESC LIMIT 1;

    UPDATE technical_indicators
    SET sma_10 = NULL, sma_20 = NULL, sma_50 = NULL, sma_200 = NULL,
        obv_100 = NULL, adr_30 = NULL, atr_30 = NULL,
        avg_volume_50 = NULL, avg_turnover_50 = NULL
    WHERE ticker_id = p_ticker_id AND exchange_code = p_exchange_code;

END //

DELIMITER ;
