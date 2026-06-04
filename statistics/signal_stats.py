import logging
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from db.models import SignalStatistic
from utils.database import engine, get_session

logger = logging.getLogger(__name__)


def compute_statistics():
    query = """
        SELECT
            s.signal_type,
            s.company_id,
            c.exchange_id,
            EXTRACT(YEAR FROM s.date)::smallint AS year,
            COUNT(*) AS occurrences,
            SUM(CASE WHEN se.drawdown_failed = FALSE THEN 1 ELSE 0 END) AS positive_count,
            CASE
                WHEN COUNT(*) > 0
                THEN SUM(CASE WHEN se.drawdown_failed = FALSE THEN 1 ELSE 0 END)::numeric / COUNT(*)
                ELSE 0
            END AS success_rate,
            AVG(se.return_10d) AS avg_return
        FROM signals s
        JOIN signal_effectiveness se ON se.signal_id = s.id
        JOIN companies c ON c.id = s.company_id
        GROUP BY s.signal_type, s.company_id, c.exchange_id, EXTRACT(YEAR FROM s.date)
        ORDER BY s.signal_type, s.company_id, year
    """
    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    if not rows:
        logger.info("No signal statistics to compute")
        return 0

    stats = []
    for r in rows:
        stats.append({
            "signal_type": r.signal_type,
            "company_id": r.company_id,
            "exchange_id": r.exchange_id,
            "year": r.year,
            "occurrences": r.occurrences,
            "positive_count": r.positive_count,
            "success_rate": float(r.success_rate) if r.success_rate else 0,
            "avg_return": float(r.avg_return) if r.avg_return else None,
        })

    with engine.begin() as conn:
        stmt = insert(SignalStatistic.__table__).values(stats)
        stmt = stmt.on_conflict_do_update(
            index_elements=["signal_type", "company_id", "exchange_id", "year"],
            set_={
                "occurrences": stmt.excluded.occurrences,
                "positive_count": stmt.excluded.positive_count,
                "success_rate": stmt.excluded.success_rate,
                "avg_return": stmt.excluded.avg_return,
            },
        )
        conn.execute(stmt)

    logger.info("Computed statistics for %d signal types", len(stats))
    return len(stats)
