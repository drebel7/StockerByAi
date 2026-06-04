import pandas as pd
from indicators.base import load_quotes


def adr(company_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(company_id)
    if len(df) < period:
        return pd.DataFrame()
    df["daily_range_pct"] = (df["high"] - df["low"]) / df["close"].shift(1) * 100
    col = f"adr_{period}d"
    df[col] = df["daily_range_pct"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])


def atr(company_id: int, period: int = 30) -> pd.DataFrame:
    df = load_quotes(company_id)
    if len(df) < period:
        return pd.DataFrame()
    prev_close = df["close"].shift(1)
    df["tr"] = pd.concat([
        (df["high"] - df["low"]).abs(),
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    col = f"atr_{period}d"
    df[col] = df["tr"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])
