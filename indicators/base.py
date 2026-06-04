import pandas as pd
from sqlalchemy import text
from utils.database import engine


def load_quotes(company_id: int) -> pd.DataFrame:
    query = text("""
        SELECT date, open, high, low, close, volume
        FROM daily_quotes
        WHERE company_id = :cid
        ORDER BY date
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"cid": company_id}, parse_dates=["date"])


def store_indicators(df: pd.DataFrame) -> int:
    from sqlalchemy.dialects.postgresql import insert
    from db.models import Indicator

    if df.empty:
        return 0
    rows = df.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = insert(Indicator.__table__).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_id", "date"],
            set_={c: stmt.excluded[c] for c in df.columns if c not in ("id", "company_id", "date")},
        )
        conn.execute(stmt)
    return len(rows)
