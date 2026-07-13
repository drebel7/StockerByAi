import pandas as pd
from indicators.base import load_quotes


def avg_volume(instrument_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"avg_volume_{period}"
    df[col] = df["volume"].rolling(window=period).mean()
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]


def avg_turnover(instrument_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < period:
        return pd.DataFrame()
    df["turnover"] = df["volume"] * df["close_price"]
    col = f"avg_turnover_{period}"
    df[col] = df["turnover"].rolling(window=period).mean()
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]