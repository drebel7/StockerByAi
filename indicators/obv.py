import pandas as pd
import talib
from indicators.base import load_quotes


def obv(instrument_id: int, period: int = 100) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if df.empty:
        return pd.DataFrame()
    obv_values = talib.OBV(df["close_price"].astype(float).values, df["volume"].astype(float).values)
    col = f"obv_{period}"
    df[col] = talib.SMA(obv_values, timeperiod=period)
    result = df[["dt", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id", col]]