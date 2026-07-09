import pandas as pd
from sqlalchemy import text
from utils.database import engine


def load_quotes(instrument_id: int) -> pd.DataFrame:
    query = text("""
        SELECT date, open, high, low, close, volume
        FROM daily_quotes
        WHERE instrument_id = :iid
        ORDER BY date
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"iid": instrument_id}, parse_dates=["date"])


def store_indicators(df: pd.DataFrame) -> int:
    from sqlalchemy.dialects.postgresql import insert
    from db.models import Indicator

    if df.empty:
        return 0
    rows = df.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Indicator.__table__).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["instrument_id", "date", "indicator_name", "parameters"],
            set_={c: stmt.excluded[c] for c in df.columns if c not in ("id", "instrument_id", "date", "indicator_name", "parameters")},
        )
        conn.execute(stmt)
    return len(rows)
