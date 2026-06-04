import pandas as pd
from indicators.base import load_quotes


def avg_volume(company_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(company_id)
    if len(df) < period:
        return pd.DataFrame()
    col = f"avg_volume_{period}d"
    df[col] = df["volume"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])


def avg_turnover(company_id: int, period: int = 50) -> pd.DataFrame:
    df = load_quotes(company_id)
    if len(df) < period:
        return pd.DataFrame()
    df["turnover"] = df["volume"] * df["close"]
    col = f"avg_turnover_{period}d"
    df[col] = df["turnover"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])
