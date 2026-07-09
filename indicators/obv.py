import pandas as pd
import talib
from indicators.base import load_quotes


def obv(instrument_id: int, period: int = 100) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if df.empty:
        return pd.DataFrame()
    obv_values = talib.OBV(df["close"].values, df["volume"].values)
    col = f"obv_{period}d"
    df[col] = talib.SMA(obv_values, timeperiod=period)
    result = df[["date", col]].dropna(subset=[col]).copy()
    result["instrument_id"] = instrument_id
    result["indicator_name"] = "obv"
    result["value"] = result[col]
    result["parameters"] = str(period)
    return result[["date", "instrument_id", "indicator_name", "value", "parameters"]]