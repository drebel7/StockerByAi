import pandas as pd
from indicators.base import load_quotes


def avg_volume(instrument_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"avg_volume_{period}d"
    df[col] = df["volume"].rolling(window=period).mean()
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "avg_volume"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]


def avg_turnover(instrument_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    df["turnover"] = df["volume"] * df["close"]
    col = f"avg_turnover_{period}d"
    df[col] = df["turnover"].rolling(window=period).mean()
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "avg_turnover"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]