import json
import logging
import time

from yfinance.data import YfData

from config.settings import GPW_TICKERS_FILE, YF_SUFFIX, BATCH_SIZE, REQUEST_DELAY, INSTRUMENT_TYPE_MAP
from data_collection.tickers import fetch_us_tickers
from db.models import Instrument, Exchange

logger = logging.getLogger(__name__)

RETRY_LIMIT = 3
_YFDATA = YfData()
QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={}"


def _load_gpw_tickers() -> dict:
    with open(GPW_TICKERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"GPW": data.get("gpw", []), "NEWCONNECT": data.get("newconnect", [])}


_TICKER_CACHE: dict | None = None


def get_all_tickers() -> dict:
    global _TICKER_CACHE
    if _TICKER_CACHE is not None:
        return _TICKER_CACHE
    tickers = {}
    us_tickers = fetch_us_tickers()
    tickers.update(us_tickers)
    pl_tickers = _load_gpw_tickers()
    tickers.update(pl_tickers)
    _TICKER_CACHE = tickers
    return tickers


def _quote_batch(symbols: list[str]) -> list[dict]:
    url = QUOTE_URL.format(",".join(symbols))
    for attempt in range(RETRY_LIMIT):
        try:
            resp = _YFDATA.get(url, timeout=15)
            if resp.status_code == 429:
                wait = (attempt + 1) * 10
                logger.warning("Rate limited (429), retrying in %ds", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data.get("quoteResponse", {}).get("result", [])
        except Exception as e:
            wait = (attempt + 1) * 5
            logger.warning("Attempt %d/%d failed for batch: %s. Retrying in %ds.",
                           attempt + 1, RETRY_LIMIT, e, wait)
            time.sleep(wait)
    return []


def fetch_instruments_for_exchange(exchange: str) -> list:
    ticker_list = get_all_tickers().get(exchange, [])
    results = []
    total = len(ticker_list)
    suffix = YF_SUFFIX.get(exchange, "")
    batch_syms, batch_orig = [], []

    for ticker, _ in ticker_list:
        batch_syms.append(f"{ticker}{suffix}")
        batch_orig.append(ticker)

        if len(batch_syms) >= BATCH_SIZE:
            results.extend(_process_batch(batch_syms, batch_orig, exchange, suffix))
            batch_syms, batch_orig = [], []

    if batch_syms:
        results.extend(_process_batch(batch_syms, batch_orig, exchange, suffix))

    logger.info("Fetched %d instruments for %s (from %d tickers)", len(results), exchange, total)
    return results


def _process_batch(batch_syms: list[str], batch_orig: list[str], exchange: str, suffix: str) -> list:
    quotes = _quote_batch(batch_syms)
    yf_to_orig = {f"{t}{suffix}": t for t in batch_orig}
    results = []
    for q in quotes:
        raw = q.get("symbol", "")
        orig = yf_to_orig.get(raw)
        if not orig:
            continue
        qt = q.get("quoteType", "")
        instrument_type = INSTRUMENT_TYPE_MAP.get(qt)
        if not instrument_type:
            continue
        results.append({
            "ticker": orig,
            "exchange": exchange,
            "full_name": q.get("longName") or q.get("shortName") or orig,
            "sector": q.get("sector"),
            "industry": q.get("industry"),
            "instrument_type": instrument_type,
        })
    time.sleep(REQUEST_DELAY)
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