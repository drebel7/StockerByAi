import pandas as pd
from sqlalchemy import text
from utils.database import engine


def load_quotes(instrument_id: int) -> pd.DataFrame:
    query = text("""
        SELECT dt, open_price, high_price, low_price, close_price, volume
        FROM daily_quotes
        WHERE instrument_id = :iid
        ORDER BY dt
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"iid": instrument_id}, parse_dates=["dt"])



