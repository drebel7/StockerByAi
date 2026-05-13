# Task description (system / application developmen)

Create a System based on a relational database + application layer for stock market data and technical analysis, implementing the following tasks:
• Downloading at least once daily updated data: open, close, low, high, volume, ticker, exchange for various stock exchanges.
• Collecting data for both companies and major indices (e.g. WIG20, SPX, Dow Jones, NASDAQ) and sectoral indices (e.g. WIG_BANKI, WIG_GRY, WIG_UKRAINA) for each required exchange.
• Support for at least: Polish GPW and NewConnect, US: NASDAQ, NYSE, AMEX (no OTC).
• Saving quotes to the database – 1 record per day per company with exchange information.
• For fast searching and grouping: index on date + company.
• Additional table storing 1 record per company per exchange: exchange, full company name, sector, industry, and several smaller classification categories (e.g. drones, AI, silver mining, gold, SMR, RAM memory, space industry, etc.). Each company can have multiple categories. Initial one-time classification with periodic refresh. Goal: sector and thematic grouping to identify cross-company thematic trends. Use IBD (Investors Business Daily) categories for inspiration if possible.
• Initial data backfill: from 2020 (or 2010 if storage allows).
1st computation layer: Technical indicators
After loading raw data, calculate and store basic technical indicators in separate table(s) – 1 record per day per company. Initially: SMA (10D, 20D, 50D, 200D), OBV 100D, ADR 30D, ATR 30D, RS (Relative Strength) vs. selected index/sector, average volume 50D, average turnover (volume * price) 50D.
Indicators updated after every raw data update. More indicators to be added later.
2nd computation layer: Conditions and signals
Based on raw data and indicators, mark various signals for a given day/company.
Example: at least 3 days within 2 weeks where volume > average + volume > previous day + 1D change > 1.7%.
Each signal: positive (1), negative (-1), none (0).
Records created only for positive or negative signals.
3rd computation layer: Signal effectiveness check
For each generated signal (1 or -1): check return from signal day close to close after 10/20/50 days, considering drawdown rule (for bullish: if price drops below signal day low → failed; for bearish: above high → failed).
4th computation layer: Signal statistics
For each signal type per company: number of occurrences, positive signals, success rate, average return.
Aggregates: per company, exchange, calendar year.
All computation layers should be wrapped in functions/methods for modularity. Can be SQL-based or higher-level language. Functions must be parameterized (e.g. SMA period).
Mechanisms must be efficient (batch SQL for simple tasks, higher-level code for complex ones).