import pandas as pd
from indicators.base import load_quotes, store_indicators


def sma(company_id: int, period: int) -> pd.DataFrame:
    df = load_quotes(company_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"sma_{period}d"
    df[col] = df["close"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])


def compute_all_sma(company_id: int) -> pd.DataFrame:
    periods = [10, 20, 50, 200]
    df = load_quotes(company_id)
    if df.empty:
        return pd.DataFrame()
    for p in periods:
        df[f"sma_{p}d"] = df["close"].rolling(window=p).mean()
    cols = ["date"] + [f"sma_{p}d" for p in periods]
    result = df[cols].copy()
    result["company_id"] = company_id
    return result.dropna(subset=[f"sma_{max(periods)}d"])
