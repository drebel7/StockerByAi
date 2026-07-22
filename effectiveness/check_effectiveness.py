import logging

import pandas as pd
from sqlalchemy import text

from db.models import SignalEffectiveness
from utils.database import engine, get_session

logger = logging.getLogger(__name__)


def compute_effectiveness():
    session = get_session()
    try:
        pending = session.execute(text("""
            SELECT DISTINCT s.instrument_id
            FROM signals s
            WHERE NOT EXISTS (SELECT 1 FROM signal_effectiveness se WHERE se.signal_id = s.id)
        """)).fetchall()

        instrument_ids = [r[0] for r in pending]
        if not instrument_ids:
            logger.info("No pending signals to compute effectiveness for")
            return 0

        logger.info("Processing effectiveness for %d instruments", len(instrument_ids))

        total = 0
        for iid in instrument_ids:
            quotes = pd.read_sql_query(
                text("SELECT dt, close_price, low_price, high_price FROM daily_quotes WHERE instrument_id = :iid ORDER BY dt"),
                session.bind, params={"iid": iid}
            )
            if quotes.empty:
                continue

            signals = session.execute(text("""
                SELECT s.id, s.date, s.value AS signal_value
                FROM signals s
                WHERE s.instrument_id = :iid
                AND NOT EXISTS (SELECT 1 FROM signal_effectiveness se WHERE se.signal_id = s.id)
                ORDER BY s.date
            """), {"iid": iid}).fetchall()

            if not signals:
                continue

            prices = quotes[["close_price", "low_price", "high_price"]].to_numpy()
            n = len(prices)
            date_index = {d: i for i, d in enumerate(quotes["dt"])}

            records = []
            for sig in signals:
                pos = date_index.get(sig.date)
                if pos is None:
                    continue

                close_at_signal = float(prices[pos][0])

                close_10d = float(prices[pos + 10][0]) if pos + 10 < n else None
                close_20d = float(prices[pos + 20][0]) if pos + 20 < n else None
                close_50d = float(prices[pos + 50][0]) if pos + 50 < n else None
                close_100d = float(prices[pos + 100][0]) if pos + 100 < n else None

                if pos + 1 < n:
                    end = min(pos + 11, n)
                    low_10d = float(prices[pos + 1:end, 1].min())
                    high_10d = float(prices[pos + 1:end, 2].max())
                else:
                    low_10d = None
                    high_10d = None

                records.append({
                    "signal_id": sig.id,
                    "close_at_signal": close_at_signal,
                    "return_10d": (close_10d - close_at_signal) / close_at_signal if close_10d else None,
                    "return_20d": (close_20d - close_at_signal) / close_at_signal if close_20d else None,
                    "return_50d": (close_50d - close_at_signal) / close_at_signal if close_50d else None,
                    "return_100d": (close_100d - close_at_signal) / close_at_signal if close_100d else None,
                    "drawdown_failed": (
                        bool(low_10d < close_at_signal) if sig.signal_value == 1 and low_10d is not None
                        else bool(high_10d > close_at_signal) if sig.signal_value == -1 and high_10d is not None
                        else False
                    ),
                    "low_10d": low_10d,
                    "high_10d": high_10d,
                })

            if records:
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO signal_effectiveness (signal_id, close_at_signal, return_10d, return_20d, return_50d, return_100d, drawdown_failed, low_10d, high_10d) VALUES (:signal_id, :close_at_signal, :return_10d, :return_20d, :return_50d, :return_100d, :drawdown_failed, :low_10d, :high_10d)"),
                        records,
                    )
                total += len(records)

            if total % 5000 == 0:
                logger.info("Processed %d effectiveness records", total)

        logger.info("Inserted %d effectiveness records total", total)
        return total
    finally:
        session.close()
