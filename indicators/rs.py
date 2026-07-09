import yfinance as yf
import pandas as pd
import time
from sqlalchemy import text
from indicators.base import load_quotes, engine
from config.settings import BNCHMARK_INDEX, REQUEST_DELAY, BACKFILL_START_YEAR


def _get_instrument_country(instrument_id: int) -> str:
    query = """
        SELECT e.country
        FROM instruments i
        JOIN exchanges e ON i.exchange_id = e.id
        WHERE i.id = :iid
    """
    with engine.connect() as conn:
        row = conn.execute(text(query), {"iid": instrument_id}).fetchone()
    return row[0] if row else "US"


def _get_benchmark_quotes(instrument_id: int) -> pd.DataFrame:
    country = _get_instrument_country(instrument_id)
    bench_ticker = BNCHMARK_INDEX.get(country, "^GSPC")
    df = yf.download(bench_ticker, start=f"{BACKFILL_START_YEAR}-01-01", progress=False, auto_adjust=True)
    time.sleep(REQUEST_DELAY)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Close"]].copy()
    df.rename(columns={"Close": "bench_close"}, inplace=True)
    df.index = pd.to_datetime(df.index)
    return df


def rs(instrument_id: int) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    bench = _get_benchmark_quotes(instrument_id)
    if df.empty or bench.empty:
        return pd.DataFrame()
    merged = df[["date", "close"]].merge(bench[["bench_close"]], left_on="date", right_index=True, how="inner")
    merged["stock_return"] = merged["close"].pct_change()
    merged["bench_return"] = merged["bench_close"].pct_change()
    merged["rs_value"] = (1 + merged["stock_return"]).cumprod() / (1 + merged["bench_return"]).cumprod()
    result = merged[["date", "rs_value"]].dropna(subset=["rs_value"]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "rs"
    result["value"] = result["rs_value"]
    result["parameters"] = None
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]