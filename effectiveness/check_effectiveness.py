import logging
import pandas as pd
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import insert

from db.models import Signal, SignalEffectiveness, DailyQuote
from utils.database import engine, get_session

logger = logging.getLogger(__name__)


def check_effectiveness(signal_id: int, instrument_id: int, signal_date, close_at_signal: float,
                        periods: list = None) -> dict:
    periods = periods or [10, 20, 50, 100]
    query = sa_text("""
        SELECT dt, close_price, low_price, high_price
        FROM daily_quotes
        WHERE instrument_id = :iid AND dt > :dt
        ORDER BY dt
    """)
    df = pd.read_sql(query, engine, params={"iid": instrument_id, "dt": signal_date},
                     parse_dates=["dt"])
    if df.empty:
        return {}

    result = {"signal_id": signal_id, "close_at_signal": close_at_signal,
              "drawdown_failed": False}
    result["low_10d"] = float(df.iloc[:min(10, len(df))]["low_price"].min())

    periods_map = {}
    for p in periods:
        if len(df) >= p:
            end_close = float(df.iloc[p - 1]["close_price"])
            periods_map[f"return_{p}d"] = (end_close - close_at_signal) / close_at_signal
        else:
            periods_map[f"return_{p}d"] = None

    result.update(periods_map)
    result["high_10d"] = float(df.iloc[:min(10, len(df))]["high_price"].max())
    return result


def compute_effectiveness(batch_size: int = 100):
    session = get_session()
    try:
        query = """
            SELECT s.id, s.instrument_id, s.date, s.value, d.close_price
            FROM signals s
            JOIN daily_quotes d ON d.instrument_id = s.instrument_id AND d.dt = s.date
            WHERE s.id NOT IN (SELECT signal_id FROM signal_effectiveness)
            ORDER BY s.id
        """
        rows = session.execute(sa_text(query)).fetchall()
        logger.info("Checking effectiveness for %d signals", len(rows))

        effective_rows = []
        for row in rows:
            result = check_effectiveness(row.id, row.instrument_id, row.date, float(row.close))
            if result:
                result["drawdown_failed"] = (
                    result.get("low_10d", float("inf")) < float(row.close)
                    if row.value == 1
                    else result.get("high_10d", 0) > float(row.close)
                )
                effective_rows.append(result)

            if len(effective_rows) >= batch_size:
                _bulk_insert_effectiveness(effective_rows)
                effective_rows = []

        if effective_rows:
            _bulk_insert_effectiveness(effective_rows)

    finally:
        session.close()


def _bulk_insert_effectiveness(rows: list):
    with engine.begin() as conn:
        stmt = insert(SignalEffectiveness.__table__).values(rows)
        stmt = stmt.on_conflict_do_nothing()
        conn.execute(stmt)
    logger.info("Inserted %d effectiveness records", len(rows))