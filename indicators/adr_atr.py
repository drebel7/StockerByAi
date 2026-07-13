import pandas as pd
import talib
from indicators.base import load_quotes


def adr(instrument_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    df["daily_range_pct"] = (df["high_price"] - df["low_price"]) / df["close_price"].shift(1) * 100
    col = f"adr_{period}"
    df[col] = df["daily_range_pct"].rolling(window=period).mean()
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]


def atr(instrument_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"atr_{period}"
    df[col] = talib.ATR(df["high_price"].astype(float).values, df["low_price"].astype(float).values, df["close_price"].astype(float).values, timeperiod=period)
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]