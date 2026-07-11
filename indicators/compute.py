import logging
import time
import math
import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from db.models import Indicator
from utils.database import engine
from indicators.sma import compute_all_sma
from indicators.obv import obv
from indicators.adr_atr import adr, atr
from indicators.rs import rs
from indicators.volume import avg_volume, avg_turnover

logger = logging.getLogger(__name__)


def compute_all_indicators(instrument_id: int):
    skip_query = "SELECT 1 FROM indicators WHERE instrument_id = :iid LIMIT 1"
    with engine.connect() as conn:
        if conn.execute(text(skip_query), {"iid": instrument_id}).scalar():
            logger.debug("Skipping instrument %d (already has indicators)", instrument_id)
            return 0
    dfs = [
        compute_all_sma(instrument_id),
        obv(instrument_id, period=100),
        adr(instrument_id, period=30),
        atr(instrument_id, period=30),
        rs(instrument_id),
        avg_volume(instrument_id, period=50),
        avg_turnover(instrument_id, period=50),
    ]
    dfs = [d for d in dfs if not d.empty]
    if not dfs:
        return 0

    combined = pd.concat(dfs, ignore_index=True)
    rows = combined.to_dict(orient="records")
    chunk_size = 2000
    total = 0
    with engine.begin() as conn:
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            stmt = insert(Indicator.__table__).values(chunk)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["instrument_id", "date", "indicator_name", "parameters"]
            )
            conn.execute(stmt)
            total += len(chunk)
    logger.info("Stored %d indicator rows for instrument %d", total, instrument_id)
    time.sleep(0.2)
    return total