import json
import logging
import time

import yfinance as yf

from config.settings import GPW_TICKERS_FILE, YF_SUFFIX, BATCH_SIZE, REQUEST_DELAY, INSTRUMENT_TYPE_MAP
from data_collection.tickers import fetch_us_tickers
from db.models import Instrument, Exchange

logger = logging.getLogger(__name__)


def _load_gpw_tickers() -> dict:
    with open(GPW_TICKERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"GPW": data.get("gpw", []), "NEWCONNECT": data.get("newconnect", [])}


def get_all_tickers() -> dict:
    tickers = {}
    us_tickers = fetch_us_tickers()
    tickers.update(us_tickers)
    pl_tickers = _load_gpw_tickers()
    tickers.update(pl_tickers)
    return tickers


def fetch_instrument_info(ticker: str, exchange: str) -> dict | None:
    suffix = YF_SUFFIX.get(exchange, "")
    yf_ticker = f"{ticker}{suffix}"
    try:
        info = yf.Ticker(yf_ticker).info
        time.sleep(REQUEST_DELAY)
    except Exception as e:
        logger.warning("Failed to fetch info for %s: %s", yf_ticker, e)
        return None

    qt = info.get("quoteType", "")
    instrument_type = INSTRUMENT_TYPE_MAP.get(qt)
    if not instrument_type:
        logger.warning("Unknown quoteType=%s for %s, skipping", qt, yf_ticker)
        return None

    return {
        "ticker": ticker,
        "full_name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "instrument_type": instrument_type,
    }


def fetch_instruments_for_exchange(exchange: str) -> list:
    ticker_list = get_all_tickers().get(exchange, [])
    results = []
    for i in range(0, len(ticker_list), BATCH_SIZE):
        batch = ticker_list[i: i + BATCH_SIZE]
        for ticker, _ in batch:
            info = fetch_instrument_info(ticker, exchange)
            if info:
                info["exchange"] = exchange
                results.append(info)
        logger.info("Fetched %d/%d instruments for %s",
                     min(i + BATCH_SIZE, len(ticker_list)), len(ticker_list), exchange)
    return results


def upsert_instruments(session, instruments: list):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    exchange_map = {ex.code: ex.id for ex in session.query(Exchange).all()}
    for inst in instruments:
        ex_id = exchange_map.get(inst["exchange"])
        if not ex_id:
            continue
        stmt = pg_insert(Instrument).values(
            ticker=inst["ticker"],
            exchange_id=ex_id,
            full_name=inst["full_name"],
            instrument_type=inst["instrument_type"],
            sector=inst.get("sector"),
            industry=inst.get("industry"),
        ).on_conflict_do_update(
            index_elements=["ticker", "exchange_id"],
            set_={
                "full_name": inst["full_name"],
                "instrument_type": inst["instrument_type"],
                "sector": inst.get("sector"),
                "industry": inst.get("industry"),
            },
        )
        session.execute(stmt)
    session.commit()