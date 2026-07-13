import logging
import time
import math
import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from indicators.base import load_quotes
from db.models import Indicator
from utils.database import engine
from indicators.sma import compute_all_sma
from indicators.obv import obv
from indicators.adr_atr import adr, atr
from indicators.rs import rs
from indicators.volume import avg_volume, avg_turnover

logger = logging.getLogger(__name__)


def _merge_indicators(base: pd.DataFrame, parts: list[pd.DataFrame]) -> pd.DataFrame:
    result = base[["dt", "instrument_id"]].copy()
    for df in parts:
        if df.empty:
            continue
        merge_cols = [c for c in df.columns if c not in ("dt", "instrument_id")]
        result = result.merge(df, on=["dt", "instrument_id"], how="left")
    return result


INDICATOR_COLS = [
    "sma_10", "sma_20", "sma_50", "sma_200",
    "obv_100", "adr_30", "atr_30", "rs",
    "avg_volume_50", "avg_turnover_50",
]


def compute_all_indicators(instrument_id: int):
    skip_query = "SELECT 1 FROM indicators WHERE instrument_id = :iid LIMIT 1"
    with engine.connect() as conn:
        if conn.execute(text(skip_query), {"iid": instrument_id}).scalar():
            logger.debug("Skipping instrument %d (already has indicators)", instrument_id)
            return 0

    dates = load_quotes(instrument_id)[["dt"]].copy()
    if dates.empty:
        return 0
    dates["instrument_id"] = instrument_id

    parts = [
        compute_all_sma(instrument_id),
        obv(instrument_id, period=100),
        adr(instrument_id, period=30),
        atr(instrument_id, period=30),
        rs(instrument_id),
        avg_volume(instrument_id, period=50),
        avg_turnover(instrument_id, period=50),
    ]

    combined = _merge_indicators(dates, parts)
    existing_cols = [c for c in INDICATOR_COLS if c in combined.columns]
    if not existing_cols:
        return 0
    has_data = combined[existing_cols].notna().any(axis=1)
    combined = combined[has_data]
    if combined.empty:
        return 0

    rows = combined[["dt", "instrument_id"] + existing_cols].to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Indicator.__table__).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["instrument_id", "dt"],
            set_={c: stmt.excluded[c] for c in existing_cols},
        )
        conn.execute(stmt)
    logger.info("Stored %d wide indicator rows for instrument %d", len(rows), instrument_id)
    time.sleep(0.2)
    return len(rows)