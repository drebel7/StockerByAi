#!/usr/bin/env python3
import logging
from datetime import datetime
from sqlalchemy import text

from db.seed import main as seed_database
from data_collection.instruments import get_all_tickers, fetch_instruments_for_exchange, upsert_instruments
from data_collection.downloader import download_all_quotes
from utils.database import execute_sql_file, ensure_partitions, get_session, engine
from db.models import PipelineRun

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def get_all_instrument_ids():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM instruments")).fetchall()
    return [r[0] for r in rows]


def _log_run(step: str, func, *args, **kwargs):
    session = get_session()
    try:
        run = PipelineRun(step=step, status="running", started_at=datetime.now())
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()

    try:
        result = func(*args, **kwargs)
        rows = result if isinstance(result, int) else None
        logger.info("Step %s completed", step)
    except Exception as e:
        session = get_session()
        try:
            r = session.query(PipelineRun).filter_by(id=run_id).first()
            if r:
                r.status = "failed"
                r.finished_at = datetime.now()
                session.commit()
        finally:
            session.close()
        raise e

    session = get_session()
    try:
        r = session.query(PipelineRun).filter_by(id=run_id).first()
        if r:
            r.status = "success"
            r.finished_at = datetime.now()
            r.rows_affected = rows if rows else None
            session.commit()
    finally:
        session.close()


def run_schema():
    logger.info("Step 1: Creating DB schema...")
    execute_sql_file("db/schema.sql")
    ensure_partitions(engine)


def run_seed():
    _log_run("seed", seed_database)


def run_instruments():
    def _do():
        session = get_session()
        try:
            total = 0
            for exchange in get_all_tickers():
                instruments = fetch_instruments_for_exchange(exchange)
                upsert_instruments(session, instruments)
                total += len(instruments)
            return total
        finally:
            session.close()
    _log_run("instruments", _do)


def run_classify():
    def _do():
        session = get_session()
        try:
            from data_collection.classifier import classify_and_persist
            return classify_and_persist(session)
        finally:
            session.close()
    _log_run("classify", _do)


def run_quotes():
    _log_run("quotes", download_all_quotes)


def run_indicators():
    def _do():
        from indicators.compute import compute_all_indicators
        instrument_ids = get_all_instrument_ids()
        total = 0
        for iid in instrument_ids:
            total += compute_all_indicators(iid)
        return total
    _log_run("indicators", _do)


def run_signals():
    def _do():
        from signals.signal_generator import compute_all_signals
        instrument_ids = get_all_instrument_ids()
        total = 0
        for iid in instrument_ids:
            total += compute_all_signals(iid)
        return total
    _log_run("signals", _do)


def run_effectiveness():
    def _do():
        from effectiveness.check_effectiveness import compute_effectiveness
        compute_effectiveness()
        return None
    _log_run("effectiveness", _do)


def run_stats():
    def _do():
        from statistics.signal_stats import compute_statistics
        return compute_statistics()
    _log_run("stats", _do)


def run_pipeline(steps: list[str] = None):
    allowed = steps or ["schema", "seed", "instruments", "classify", "quotes", "indicators", "signals", "effectiveness", "stats"]

    if "schema" in allowed:
        run_schema()
    if "seed" in allowed:
        run_seed()
    if "instruments" in allowed:
        run_instruments()
    if "classify" in allowed:
        run_classify()
    if "quotes" in allowed:
        run_quotes()
    if "indicators" in allowed:
        run_indicators()
    if "signals" in allowed:
        run_signals()
    if "effectiveness" in allowed:
        run_effectiveness()
    if "stats" in allowed:
        run_stats()

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    import sys
    if "--steps" in sys.argv:
        idx = sys.argv.index("--steps")
        steps = sys.argv[idx + 1].split(",")
        run_pipeline(steps)
    else:
        run_pipeline()