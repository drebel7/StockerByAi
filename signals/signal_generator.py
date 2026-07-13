import logging
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from db.models import Signal
from utils.database import engine, get_session
from indicators.base import load_quotes

logger = logging.getLogger(__name__)

SIGNAL_REGISTRY = {}


def register_signal(name):
    def decorator(func):
        SIGNAL_REGISTRY[name] = func
        return func
    return decorator


def get_signal(name):
    func = SIGNAL_REGISTRY.get(name)
    if func is None:
        raise ValueError(f"Unknown signal: {name}. Available: {list(SIGNAL_REGISTRY)}")
    return func


@register_signal("volume_breakout")
def volume_breakout_signal(instrument_id: int, lookback_days: int = 14, min_days: int = 3,
                           min_change_pct: float = 1.7) -> pd.DataFrame:
    df = load_quotes(instrument_id)
    if df.empty or len(df) < lookback_days + 50:
        return pd.DataFrame()

    df["avg_vol_50"] = df["volume"].rolling(window=50).mean()
    df["prev_vol"] = df["volume"].shift(1)
    df["pct_change"] = df["close_price"].pct_change() * 100

    df["condition"] = (
        (df["volume"] > df["avg_vol_50"]) &
        (df["volume"] > df["prev_vol"]) &
        (df["pct_change"] > min_change_pct)
    ).astype(int)

    df["rolling_count"] = df["condition"].rolling(window=lookback_days).sum()

    df["signal"] = 0
    df.loc[df["rolling_count"] >= min_days, "signal"] = 1

    result = df[df["signal"] != 0][["dt", "signal"]].copy()
    if result.empty:
        return pd.DataFrame()
    result["instrument_id"] = instrument_id
    result["signal_type"] = "volume_breakout"
    result.rename(columns={"signal": "value"}, inplace=True)
    return result[["dt", "value", "instrument_id", "signal_type"]]


@register_signal("golden_cross")
def golden_cross_signal(instrument_id: int) -> pd.DataFrame:
    from sqlalchemy import text
    from utils.database import engine

    query = text("""
        SELECT dt, sma_50, sma_200
        FROM indicators
        WHERE instrument_id = :iid
        ORDER BY dt
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"iid": instrument_id}, parse_dates=["dt"])

    if df.empty or len(df) < 2:
        return pd.DataFrame()

    df["prev_sma_50"] = df["sma_50"].shift(1)
    df["prev_sma_200"] = df["sma_200"].shift(1)

    df["signal"] = 0
    df.loc[(df["prev_sma_50"] <= df["prev_sma_200"]) & (df["sma_50"] > df["sma_200"]), "signal"] = 1
    df.loc[(df["prev_sma_50"] >= df["prev_sma_200"]) & (df["sma_50"] < df["sma_200"]), "signal"] = -1

    result = df[df["signal"] != 0][["dt", "signal"]].copy()
    if result.empty:
        return pd.DataFrame()
    result["instrument_id"] = instrument_id
    result["signal_type"] = "golden_cross"
    result.rename(columns={"signal": "value"}, inplace=True)
    return result[["dt", "value", "instrument_id", "signal_type"]]


def compute_all_signals(instrument_id: int):
    results = []
    for name, func in SIGNAL_REGISTRY.items():
        try:
            df = func(instrument_id)
            if not df.empty:
                results.append(df)
        except Exception as e:
            logger.error("Signal %s failed for instrument %d: %s", name, instrument_id, e)

    if not results:
        return 0
    combined = pd.concat(results, ignore_index=True)
    rows = combined.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Signal.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["instrument_id", "date", "signal_type"]
        )
        conn.execute(stmt)
    return len(rows)