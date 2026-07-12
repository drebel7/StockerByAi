# TODO
things to do:
* add active columns to: instruments, exchanges to enable/disable them for data collection and processing
* add valid, dt_from, dt_to (to indicate daily_quotes data are continuous), market cap column to instruments
* reorganize indicators table to simplify structure and SQLs. One table with many columns for each indicator and its parameters.
* consider adding a single id for daily_quotes to be used as foreign key in indicators and signals tables. This will simplify joins and improve performance.
* rename columns in daily_quotes table to be more clear and not to use reserved words: date -> dt, open_price, close_price, low_price, high_price
* add database connection pooling to improve performance and avoid connection issues
* 