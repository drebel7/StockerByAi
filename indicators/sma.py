import pandas as pd
import talib
from indicators.base import load_quotes


def sma(instrument_id: int, period: int) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"sma_{period}"
    df[col] = talib.SMA(df["close_price"].astype(float).values, timeperiod=period)
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]


def compute_all_sma(instrument_id: int) -> pd.DataFrame:
    periods = [10, 20, 50, 200]
    results = []
    for p in periods:
        df = sma(instrument_id, period=p)
        if not df.empty:
            results.append(df)
    if not results:
        return pd.DataFrame()
    combined = results[0]
    for df in results[1:]:
        combined = combined.merge(df, on=["dt", "instrument_id"], how="outer")
    return combined