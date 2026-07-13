import logging
import time
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert

from config.settings import BACKFILL_START_YEAR, YF_SUFFIX, BATCH_SIZE, REQUEST_DELAY
from data_collection.instruments import get_all_tickers
from db.models import Instrument, DailyQuote, Exchange, DataSource
from utils.database import get_session, engine

logger = logging.getLogger(__name__)


def _get_exchange_map(session) -> dict:
    return {row.code: row.id for row in session.query(Exchange).all()}


def _get_instrument_map(session) -> dict:
    rows = session.query(Instrument.ticker, Instrument.exchange_id, Instrument.id).all()
    return {(r.ticker, r.exchange_id): r.id for r in rows}


def _get_data_source_id(session) -> int:
    ds = session.query(DataSource).filter_by(code="yahoo_finance").first()
    return ds.id if ds else 1


def download_batch_quotes(
    tickers: list,
    exchange: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    suffix = YF_SUFFIX.get(exchange, "")
    yf_tickers = [f"{t}{suffix}" for t in tickers]
    start = start or f"{BACKFILL_START_YEAR}-01-01"
    end = end or date.today().isoformat()

    try:
        df = yf.download(yf_tickers, start=start, end=end, progress=False, auto_adjust=True, group_by="ticker")
        time.sleep(REQUEST_DELAY)
    except Exception as e:
        logger.warning("Batch download failed for %s: %s", exchange, e)
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    records = []
    if isinstance(df.columns, pd.MultiIndex):
        tickers_in_result = [c for c in df.columns.levels[0] if c in yf_tickers]
        for yf_t in tickers_in_result:
            sub = df[yf_t].dropna(how="all")
            if sub.empty:
                continue
            raw_ticker = yf_t.replace(suffix, "")
            for dt_val, row in sub.iterrows():
                records.append({
                    "dt": dt_val,
                    "ticker": raw_ticker,
                    "exchange": exchange,
                    "open_price": row.get("Open"),
                    "high_price": row.get("High"),
                    "low_price": row.get("Low"),
                    "close_price": row.get("Close"),
                    "volume": row.get("Volume"),
                })
    else:
        ticker = tickers[0]
        for dt_val, row in df.iterrows():
            records.append({
                "dt": dt_val,
                "ticker": ticker,
                "exchange": exchange,
                "open_price": row.get("Open") or row.get("open"),
                "high_price": row.get("High") or row.get("high"),
                "low_price": row.get("Low") or row.get("low"),
                "close_price": row.get("Close") or row.get("close"),
                "volume": row.get("Volume") or row.get("volume"),
            })

    return pd.DataFrame(records)


def bulk_upsert_quotes(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    session = get_session()
    try:
        ex_map = _get_exchange_map(session)
        inst_map = _get_instrument_map(session)
        ds_id = _get_data_source_id(session)

        df["exchange_id"] = df["exchange"].map(ex_map)
        df = df.dropna(subset=["exchange_id"])
        df["exchange_id"] = df["exchange_id"].astype(int)

        df["instrument_id"] = df.apply(
            lambda r: inst_map.get((r["ticker"], r["exchange_id"])), axis=1
        )
        df = df.dropna(subset=["instrument_id"])
        if df.empty:
            return 0

        df["instrument_id"] = df["instrument_id"].astype(int)
        df["data_source_id"] = ds_id

        from utils.database import ensure_partitions
        ensure_partitions(engine)

        rows = df[["instrument_id", "dt", "open_price", "high_price", "low_price", "close_price", "volume", "data_source_id"]].to_dict(orient="records")

        with engine.begin() as conn:
            # Insert in chunks of 2000 rows to avoid PostgreSQL parameter limit (~32767)
            chunk_size = 2000
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                stmt = insert(DailyQuote.__table__).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["instrument_id", "dt"],
                    set_={
                        "open_price": stmt.excluded.open_price,
                        "high_price": stmt.excluded.high_price,
                        "low_price": stmt.excluded.low_price,
                        "close_price": stmt.excluded.close_price,
                        "volume": stmt.excluded.volume,
                        "data_source_id": stmt.excluded.data_source_id,
                    },
                )
                conn.execute(stmt)
        return len(rows)
    finally:
        session.close()


def download_all_quotes(exchanges: Optional[list] = None):
    all_tickers = get_all_tickers()
    exchanges = exchanges or list(all_tickers.keys())

    for exchange in exchanges:
        ticker_list = all_tickers.get(exchange, [])
        ticker_names = [t[0] for t in ticker_list]
        logger.info("Downloading %d tickers for %s", len(ticker_names), exchange)

        for i in range(0, len(ticker_names), BATCH_SIZE):
            batch = ticker_names[i: i + BATCH_SIZE]
            df = download_batch_quotes(batch, exchange)
            if not df.empty:
                count = bulk_upsert_quotes(df)
                logger.info(
                    "Stored %d quote rows for %s batch %d/%d",
                    count, exchange,
                    i // BATCH_SIZE + 1,
                    (len(ticker_names) + BATCH_SIZE - 1) // BATCH_SIZE,
                )