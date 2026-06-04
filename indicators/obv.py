import pandas as pd
from indicators.base import load_quotes, store_indicators


def obv(company_id: int, period: int = 100) -> pd.DataFrame:
    df = load_quotes(company_id)
    if df.empty:
        return pd.DataFrame()
    df["daily_obv"] = 0
    df.loc[df["close"] > df["close"].shift(1), "daily_obv"] = df["volume"]
    df.loc[df["close"] < df["close"].shift(1), "daily_obv"] = -df["volume"]
    df["obv"] = df["daily_obv"].cumsum()
    col = f"obv_{period}d"
    df[col] = df["obv"].rolling(window=period).mean()
    result = df[["date"]].copy()
    result["company_id"] = company_id
    result[col] = df[col]
    return result.dropna(subset=[col])
