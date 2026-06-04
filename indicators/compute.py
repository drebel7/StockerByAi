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


def compute_all_indicators(company_id: int):
    sma_df = compute_all_sma(company_id)
    obv_df = obv(company_id, period=100)
    adr_df = adr(company_id, period=30)
    atr_df = atr(company_id, period=30)
    rs_df = rs(company_id)
    avg_vol_df = avg_volume(company_id, period=50)
    avg_turn_df = avg_turnover(company_id, period=50)

    merged = sma_df.copy() if not sma_df.empty else pd.DataFrame()
    for _df in [obv_df, adr_df, atr_df, rs_df, avg_vol_df, avg_turn_df]:
        if merged.empty:
            merged = _df.copy()
        elif not _df.empty:
            merged = merged.merge(_df, on=["date", "company_id"], how="outer")

    if merged.empty:
        return 0

    rows = merged.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Indicator.__table__).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_id", "date"],
            set_={c.name: stmt.excluded[c.name] for c in Indicator.__table__.columns
                  if c.name not in ("id", "company_id", "date") and c.name in merged.columns},
        )
        conn.execute(stmt)
    logger.info("Stored %d indicator rows for company %d", len(rows), company_id)
    return len(rows)
