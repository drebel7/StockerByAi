import pandas as pd
from indicators.base import load_quotes


def ichimoku(instrument_id: int) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if len(df) < 52:
        return pd.DataFrame()

    tenkan_high = df["high_price"].rolling(window=9).max()
    tenkan_low = df["low_price"].rolling(window=9).min()
    df["ichimoku_tenkan_sen_9"] = (tenkan_high + tenkan_low) / 2

    kijun_high = df["high_price"].rolling(window=26).max()
    kijun_low = df["low_price"].rolling(window=26).min()
    df["ichimoku_kijun_sen_26"] = (kijun_high + kijun_low) / 2

    df["ichimoku_senkou_span_a_26"] = (
        (df["ichimoku_tenkan_sen_9"] + df["ichimoku_kijun_sen_26"]) / 2
    ).shift(26)

    senkou_b_high = df["high_price"].rolling(window=52).max()
    senkou_b_low = df["low_price"].rolling(window=52).min()
    df["ichimoku_senkou_span_b_26"] = ((senkou_b_high + senkou_b_low) / 2).shift(26)

    cols = [
        "ichimoku_tenkan_sen_9",
        "ichimoku_kijun_sen_26",
        "ichimoku_senkou_span_a_26",
        "ichimoku_senkou_span_b_26",
    ]

    result = df[["dt"] + cols].dropna(subset=cols).copy()
    result["instrument_id"] = instrument_id
    return result[["dt", "instrument_id"] + cols]
