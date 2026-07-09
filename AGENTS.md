# StockerByAI — Agent Guide

## Architecture Overview

4-layer pipeline orchestrated by `pipeline.py`:
1. **ETL** — `data_collection/`: companies, daily quotes, indices (yfinance source)
2. **Indicators** — `indicators/`: per-company pandas-based TA (SMA, OBV, ADR, ATR, RS, vol/turnover)
3. **Signals** — `signals/signal_generator.py`: registry-based signal engine (`@register_signal` decorator)
4. **Effectiveness + Stats** — `effectiveness/`, `statistics/`: post-signal return analysis

Each step is a module function called per-company or globally via `pipeline.py`.

## Database

- **PostgreSQL** via SQLAlchemy. Connection from `config/settings.py` (env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
- Schema in `db/schema.sql` (raw SQL — always run this directly). ORM models in `db/models.py` mirror the same tables.
- Key tables: `daily_quotes` (raw OHLCV), `indicators` (wide table: one row per company/date with all indicators as columns), `signals` (sparse — only triggered rows), `signal_effectiveness`, `signal_statistics`.
- **Pattern**: All upserts use `sqlalchemy.dialects.postgresql.insert` with `on_conflict_do_update` or `on_conflict_do_nothing` — never raw INSERT.
- `daily_quotes` has index on `(date, company_id)` and a unique constraint on `(company_id, date)`.

## Indicator Pattern

Every indicator in `indicators/` is a **standalone function** that:
- Takes `company_id: int` and optional `period`
- Calls `load_quotes(company_id)` from `indicators/base.py` (returns a DataFrame with columns: date, open, high, low, close, volume)
- Returns a DataFrame with columns: `date`, `company_id`, `{indicator_name}` (always includes `company_id` for merge)
- `compute_all_indicators(company_id)` in `compute.py` calls each indicator, merges on `[date, company_id]`, then bulk upserts

Never add new columns to the indicators table without updating both `db/schema.sql` and `db/models.py.Indicator`.

## Signal Pattern

Signals live in `signals/signal_generator.py`. New signals:
1. Define a function taking `company_id: int` returning a DataFrame with columns `date`, `value` (1 or -1), `company_id`, `signal_type` (string)
2. Decorate with `@register_signal("signal_name")`
3. The registry auto-discovers it — no manual wiring needed
4. Use `.on_conflict_do_nothing()` — duplicate signals are silently skipped

## Classifier

Rule-based keyword matching in `data_collection/classifier.py`. `KEYWORD_MAP` maps category names to lists of regex patterns. `classify_company(sector, industry)` returns a `set` of matched categories. To add a new theme, extend `CATEGORY_NAMES` in `db/seed.py` and add entries to `KEYWORD_MAP`.

## External Dependencies

- **yfinance** — only source for quotes, company info, and index data. `YF_SUFFIX` in `config/settings.py` appends `.WA` for GPW/NewConnect.
- **NASDAQ FTP** (`ftp://ftp.nasdaqtrader.com/symboldirectory/`) — ticker lists for US exchanges.
- **GPW tickers** — from local `config/gpw_tickers.json` file.
- Request delay `0.5s` between yfinance calls (`config/settings.py:REQUEST_DELAY`), batch size 50.

## Tests

- pytest, require live PostgreSQL. Session fixture in `conftest.py` wraps each test in a transaction that rolls back.
- Tests currently verify function existence and classifier logic — no DB-dependent integration tests yet.
- Run: `pytest tests/`

## Running the Pipeline

```bash
python pipeline.py                          # run all 9 steps
python pipeline.py --steps quotes indicators # run specific steps
```

Steps: `schema`, `seed`, `companies`, `quotes`, `indices`, `indicators`, `signals`, `effectiveness`, `stats`.

## Categorization Dates

`BACKFILL_START_YEAR = 2010` in `config/settings.py`. Quotes download from Jan 1 of that year.