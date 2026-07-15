import logging

from sqlalchemy import text as sa_text

from utils.database import engine

logger = logging.getLogger(__name__)

BULK_SQL = sa_text("""
    WITH ranked_quotes AS (
        SELECT
            instrument_id, dt, close_price, low_price, high_price,
            ROW_NUMBER() OVER (PARTITION BY instrument_id ORDER BY dt) AS rn
        FROM daily_quotes
    ),
    signal_base AS (
        SELECT
            s.id AS signal_id,
            s.instrument_id,
            s.value AS signal_value,
            d.close_price AS close_at_signal,
            q.rn AS signal_rn
        FROM signals s
        JOIN daily_quotes d ON d.instrument_id = s.instrument_id AND d.dt = s.date
        JOIN ranked_quotes q ON q.instrument_id = s.instrument_id AND q.dt = s.date
        WHERE s.id NOT IN (SELECT signal_id FROM signal_effectiveness)
    ),
    future AS (
        SELECT
            sb.signal_id,
            sb.instrument_id,
            sb.signal_value,
            sb.close_at_signal,
            q10.close_price AS close_10d,
            q20.close_price AS close_20d,
            q50.close_price AS close_50d,
            q100.close_price AS close_100d,
            MIN(CASE WHEN q.rn BETWEEN sb.signal_rn + 1 AND sb.signal_rn + 10
                     THEN q.low_price END) AS low_10d,
            MAX(CASE WHEN q.rn BETWEEN sb.signal_rn + 1 AND sb.signal_rn + 10
                     THEN q.high_price END) AS high_10d
        FROM signal_base sb
        LEFT JOIN ranked_quotes q10 ON q10.instrument_id = sb.instrument_id AND q10.rn = sb.signal_rn + 10
        LEFT JOIN ranked_quotes q20 ON q20.instrument_id = sb.instrument_id AND q20.rn = sb.signal_rn + 20
        LEFT JOIN ranked_quotes q50 ON q50.instrument_id = sb.instrument_id AND q50.rn = sb.signal_rn + 50
        LEFT JOIN ranked_quotes q100 ON q100.instrument_id = sb.instrument_id AND q100.rn = sb.signal_rn + 100
        LEFT JOIN ranked_quotes q ON q.instrument_id = sb.instrument_id
            AND q.rn BETWEEN sb.signal_rn + 1 AND sb.signal_rn + 10
        GROUP BY sb.signal_id, sb.instrument_id, sb.signal_value, sb.close_at_signal,
                 q10.close_price, q20.close_price, q50.close_price, q100.close_price
    )
    INSERT INTO signal_effectiveness (signal_id, close_at_signal, return_10d, return_20d,
                                      return_50d, return_100d, drawdown_failed, low_10d, high_10d)
    SELECT
        signal_id,
        close_at_signal,
        (close_10d - close_at_signal) / NULLIF(close_at_signal, 0) AS return_10d,
        (close_20d - close_at_signal) / NULLIF(close_at_signal, 0) AS return_20d,
        (close_50d - close_at_signal) / NULLIF(close_at_signal, 0) AS return_50d,
        (close_100d - close_at_signal) / NULLIF(close_at_signal, 0) AS return_100d,
        CASE
            WHEN signal_value = 1  THEN COALESCE(low_10d, 999999) < close_at_signal
            WHEN signal_value = -1 THEN COALESCE(high_10d, -1) > close_at_signal
            ELSE FALSE
        END AS drawdown_failed,
        low_10d,
        high_10d
    FROM future
""")


def compute_effectiveness():
    with engine.begin() as conn:
        result = conn.execute(BULK_SQL)
        logger.info("Inserted %d effectiveness records via bulk SQL", result.rowcount)