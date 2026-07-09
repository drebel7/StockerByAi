import logging
import pandas as pd
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
    with engine.begin() as conn:
        stmt = insert(Indicator.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["instrument_id", "date", "indicator_name", "parameters"]
        )
        conn.execute(stmt)
    logger.info("Stored %d indicator rows for instrument %d", len(rows), instrument_id)
    return len(rows)