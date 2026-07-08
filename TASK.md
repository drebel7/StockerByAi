# Task description (system / application development)

Create a System based on a relational database (PostgreSQL) + application layer for stock market data and technical analysis, implementing the following workflow. 
To support workflow usage of airflow should be considered.
For technical analysis and technical indicators computation TA-Lib should be considered.
There will be a lot of data here - a few tables with tens of millions records, so on every stage consider data types, sizes, end computation efficiency.

### ETL layer: Extract, Transform, Load
* Downloading at least once daily updated data: open, close, low, high, volume, ticker, exchange for various stock exchanges.
* Collecting data for both instruments of types: stocks and indices (e.g. WIG20, SPX, Dow Jones, NASDAQ) and sectoral indices (e.g. WIG_BANKI, WIG_GRY, WIG_UKRAINA) for each required exchange.
* Support for at least: Polish GPW and NewConnect, US: NASDAQ, NYSE, AMEX (no OTC). Consider also Canadian and Australian stock exchanges.
* estimated number of instruments being imported: 2-5k per day cumulative for all exchanges.
* data retention: 10-20 years, so cumulative data size of instrument history will be from 2000 instruments * 10 years * 253 trading days / year = 5 million records to 5000 instruments * 20 years * 253 trading days / year = 25 million records
* for that reason, main table storing raw data should not have any more columns than necessary (date, open, close, low, high, volume, instrument id, data source id). Partitioning by year is recommended.
* use datatypes that are as small as possible (e.g. float4 instead of float8, int4 instead of int8, etc.) to save storage space.
* index on date + instrument id for fast searching and grouping.
* Initial data backfill: from 2020 (or 2010 if data is available and storage allows).

### additional data 
* other tables: exchange (id, name, short name, country), instrument (id, ticker, exchange, full name, sector, industry  etc.), data sources (id, name e.g. yahoo finance or stooq).
* for each instrument in addition to sector and industry there should be also a theme categorization. Many possible values for each instrument e.g. AI, space industry, drones, SMR, RAM memory, quantum, gold, coal, uranium. Many companies are in a few themes at once e.g. gold mining + silver mining + copper mining. Those themes will be used for instrument selection and grouping, so the data model should be prepared for efficient usage in such scenarios. Goal: sector and thematic grouping to identify cross-company thematic trends. Use IBD (Investors Business Daily) categories for inspiration if possible.

### 1st computation layer / stage: Technical indicators 
* After loading raw data (ETL stage), calculate and store basic technical indicator values in separate table(s). Consider 2 models: 1 record per day per company and every indicator in its own column or a record per day + instrument + indicator + indicator parameters. Consider ease of addition of new indicators, table size, indexing for searching. 
* Initially: SMA (10D, 20D, 50D, 200D), OBV 100D, ADR 30D, ATR 30D, average volume 30D, average turnover (volume * price) 30D.
* Indicators updated after every raw data update. 
* More indicators to be added later.

### 2nd computation layer / stage: Conditions and signals
* Based on raw data and indicators values, mark various signals for a given day + instrument.
* Each signal: positive / bullish (1), negative / bearish (-1), none (0).
* Simple signal example: golden cross positive signal is when SMA50 goes above SMA200.
* Another signal positive signal example: at least 3 days within 2 weeks where volume > average + volume > previous day + 1D change > 1.7%.
* Each signal should have a definition consisting of conditions that should be met to trigger a signal. A series of conditions with 'AND', 'OR' logic should build a signal.
* Records in signal table should be created only for positive or negative signals. No signal - no record.

### 3rd computation layer / stage: Signal effectiveness check
* For each generated signal (1 or -1): check return from signal day close to close after 10/20/50/100 days, 
* considering drawdown rule (for bullish: if price drops below signal day low → failed; for bearish: above high → failed).

### 4th computation layer / stage: Signal type statistics
For each signal type per company: number of occurrences, positive signals, success rate, average return.
Aggregates: global across all instruments, per exchange, per company, calendar year.
All computation layers should be wrapped created in a modularity and efficiency (time and memory) in mind. Can be SQL-based or higher-level language. Functions must be parameterized (e.g. SMA period).
Mechanisms must be efficient (batch SQL for simple tasks, higher-level code for complex ones).
