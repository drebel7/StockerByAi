import pandas as pd
import talib
from indicators.base import load_quotes


def adr(instrument_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    df["daily_range_pct"] = (df["high"] - df["low"]) / df["close"].shift(1) * 100
    col = f"adr_{period}d"
    df[col] = df["daily_range_pct"].rolling(window=period).mean()
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "adr"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]


def atr(instrument_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"atr_{period}d"
    df[col] = talib.ATR(df["high"].values, df["low"].values, df["close"].values, timeperiod=period)
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "atr"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]