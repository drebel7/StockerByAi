import pandas as pd
import talib
from indicators.base import load_quotes


def sma(instrument_id: int, period: int) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"sma_{period}d"
    df[col] = talib.SMA(df["close"].astype(float).values, timeperiod=period)
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "sma"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]


def compute_all_sma(instrument_id: int) -> pd.DataFrame:
    periods = [10, 20, 50, 200]
    results = []
    for p in periods:
        df = sma(instrument_id, period=p)
        if not df.empty:
            results.append(df)
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()