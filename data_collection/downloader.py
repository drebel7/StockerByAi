import logging
import time
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert

from config.settings import BACKFILL_START_YEAR, YF_SUFFIX, BATCH_SIZE, REQUEST_DELAY
from data_collection.companies import get_all_tickers
from db.models import Company, DailyQuote, Exchange
from utils.database import get_session, engine

logger = logging.getLogger(__name__)


def _get_exchange_map(session) -> dict:
    return {row.code: row.id for row in session.query(Exchange).all()}


def _get_company_map(session) -> dict:
    rows = session.query(Company.ticker, Company.exchange_id, Company.id).all()
    return {(r.ticker, r.exchange_id): r.id for r in rows}


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
            for dt, row in sub.iterrows():
                records.append({
                    "date": dt,
                    "ticker": raw_ticker,
                    "exchange": exchange,
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume"),
                })
    else:
        ticker = tickers[0]
        for dt, row in df.iterrows():
            records.append({
                "date": dt,
                "ticker": ticker,
                "exchange": exchange,
                "open": row.get("Open") or row.get("open"),
                "high": row.get("High") or row.get("high"),
                "low": row.get("Low") or row.get("low"),
                "close": row.get("Close") or row.get("close"),
                "volume": row.get("Volume") or row.get("volume"),
            })

    return pd.DataFrame(records)


def bulk_upsert_quotes(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    session = get_session()
    try:
        ex_map = _get_exchange_map(session)
        co_map = _get_company_map(session)

        df["exchange_id"] = df["exchange"].map(ex_map)
        df = df.dropna(subset=["exchange_id"])
        df["exchange_id"] = df["exchange_id"].astype(int)

        df["company_id"] = df.apply(
            lambda r: co_map.get((r["ticker"], r["exchange_id"])), axis=1
        )
        df = df.dropna(subset=["company_id"])
        if df.empty:
            return 0

        df["company_id"] = df["company_id"].astype(int)
        rows = df[["company_id", "date", "open", "high", "low", "close", "volume"]].to_dict(orient="records")

        with engine.begin() as conn:
            stmt = insert(DailyQuote.__table__).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["company_id", "date"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
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
            batch = ticker_names[i : i + BATCH_SIZE]
            df = download_batch_quotes(batch, exchange)
            if not df.empty:
                count = bulk_upsert_quotes(df)
                logger.info(
                    "Stored %d quote rows for %s batch %d/%d",
                    count, exchange,
                    i // BATCH_SIZE + 1,
                    (len(ticker_names) + BATCH_SIZE - 1) // BATCH_SIZE,
                )
