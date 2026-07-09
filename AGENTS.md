# StockerByAI — Agent Guide

## Architecture Overview

4-layer pipeline orchestrated by `pipeline.py`:
1. **ETL** — `data_collection/`: instruments, daily quotes (yfinance source)
2. **Indicators** — `indicators/`: per-instrument pandas-based TA (long model: instrument_id + date + indicator_name + parameters + value)
3. **Signals** — `signals/signal_generator.py`: registry-based signal engine (`@register_signal` decorator)
4. **Effectiveness + Stats** — `effectiveness/`, `statistics/`: post-signal return analysis

Each step is a module function called per-instrument or globally via `pipeline.py`.

## Database

- **PostgreSQL** via SQLAlchemy. Connection from `config/settings.py` (env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
- Schema in `db/schema.sql` (raw SQL — run this directly, includes DROP CASCADE for clean rebuild). ORM models in `db/models.py` mirror the same tables.
- Key tables: `instruments` (stocks/indices/ETFs with `instrument_type`), `daily_quotes` (partitioned by year, REAL types), `indicators` (long model), `signals`, `signal_effectiveness`, `signal_statistics`.
- **Pattern**: All upserts use `sqlalchemy.dialects.postgresql.insert` with `on_conflict_do_update` or `on_conflict_do_nothing` — never raw INSERT.
- `daily_quotes` is `PARTITION BY RANGE (date)` with yearly partitions created automatically by `ensure_partitions()` in `utils/database.py`.

## Instrument Types

`instruments.instrument_type` is auto-detected from yfinance `quoteType`: `"EQUITY"` → `"stock"`, `"ETF"` → `"etf"`, `"INDEX"` → `"index"`. Unknown types are silently skipped. Mapping in `config/settings.py:INSTRUMENT_TYPE_MAP`.

## Indicator Pattern (Long Model)

Every indicator in `indicators/` is a **standalone function** that:
- Takes `instrument_id: int` and optional `period`
- Calls `load_quotes(instrument_id)` from `indicators/base.py`
- Returns a DataFrame with columns: `date`, `instrument_id`, `indicator_name`, `value`, `parameters`
- `compute_all_indicators(instrument_id)` in `compute.py` calls each, concats, then bulk upserts with `on_conflict_do_nothing`

To add a new indicator: create a function returning the 5-column DataFrame, add it to `compute_all_indicators` import/call list.

## Signal Pattern

Signals live in `signals/signal_generator.py`. New signals:
1. Define a function taking `instrument_id: int` returning a DataFrame with columns `date`, `value` (1 or -1), `instrument_id`, `signal_type` (string)
2. Decorate with `@register_signal("signal_name")`
3. The registry auto-discovers it — no manual wiring needed
4. Use `.on_conflict_do_nothing()` — duplicate signals are silently skipped

## Classifier

Rule-based keyword matching in `data_collection/classifier.py`. `KEYWORD_MAP` maps category names to lists of regex patterns. `classify_instrument(sector, industry)` returns a `set` of matched categories. To add a new theme, extend `CATEGORY_NAMES` in `db/seed.py` and add entries to `KEYWORD_MAP`.

## External Dependencies

- **yfinance** — only source for quotes, company info, and index data. `YF_SUFFIX` appends `.WA` for GPW/NewConnect.
- **NASDAQ FTP** — ticker lists for US exchanges.
- **GPW tickers** — from local `config/gpw_tickers.json` file.
- Request delay `0.5s` between yfinance calls, batch size 50.

## Tests

- pytest, require live PostgreSQL. Session fixture in `conftest.py` wraps each test in a transaction that rolls back.
- Run: `pytest tests/`

## Running the Pipeline

```bash
python pipeline.py
python pipeline.py --steps schema seed instruments classify quotes
```

Steps: `schema`, `seed`, `instruments`, `classify`, `quotes`, `indicators`, `signals`, `effectiveness`, `stats`.

## Categorization Dates

`BACKFILL_START_YEAR = 2010` in `config/settings.py`. Quotes download from Jan 1 of that year.