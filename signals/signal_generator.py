import logging
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from db.models import Signal
from utils.database import engine, get_session
from indicators.base import load_quotes, store_indicators

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
def volume_breakout_signal(company_id: int, lookback_days: int = 14, min_days: int = 3,
                           min_change_pct: float = 1.7) -> pd.DataFrame:
    """
    Positive signal: at least `min_days` within `lookback_days` where:
      - volume > avg_volume_50d
      - volume > previous day volume
      - 1D change > min_change_pct%
    """
    df = load_quotes(company_id)
    if df.empty or len(df) < lookback_days + 50:
        return pd.DataFrame()

    df["avg_vol_50"] = df["volume"].rolling(window=50).mean()
    df["prev_vol"] = df["volume"].shift(1)
    df["pct_change"] = df["close"].pct_change() * 100

    df["condition"] = (
        (df["volume"] > df["avg_vol_50"]) &
        (df["volume"] > df["prev_vol"]) &
        (df["pct_change"] > min_change_pct)
    ).astype(int)

    df["rolling_count"] = df["condition"].rolling(window=lookback_days).sum()

    df["signal"] = 0
    df.loc[df["rolling_count"] >= min_days, "signal"] = 1

    result = df[df["signal"] != 0][["date", "signal"]].copy()
    if result.empty:
        return pd.DataFrame()
    result["company_id"] = company_id
    result["signal_type"] = "volume_breakout"
    result.rename(columns={"signal": "value"}, inplace=True)
    return result


def compute_all_signals(company_id: int):
    results = []
    for name, func in SIGNAL_REGISTRY.items():
        try:
            df = func(company_id)
            if not df.empty:
                results.append(df)
        except Exception as e:
            logger.error("Signal %s failed for company %d: %s", name, company_id, e)

    if not results:
        return 0
    combined = pd.concat(results, ignore_index=True)
    rows = combined.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Signal.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["company_id", "date", "signal_type"]
        )
        conn.execute(stmt)
    return len(rows)
