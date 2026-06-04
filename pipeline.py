#!/usr/bin/env python3
import logging

from sqlalchemy import text

from db.seed import main as seed_database
from data_collection.companies import get_all_tickers, fetch_all_companies, upsert_companies
from data_collection.downloader import download_all_quotes
from data_collection.indices import download_all_indices
from utils.database import execute_sql_file, get_session, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def get_all_company_ids():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id FROM companies")).fetchall()
    return [r[0] for r in rows]


def run_pipeline(steps: list[str] = None):
    allowed = steps or ["schema", "seed", "companies", "quotes", "indices", "indicators", "signals", "effectiveness", "stats"]

    if "schema" in allowed:
        logger.info("Step 1: Creating DB schema...")
        execute_sql_file("db/schema.sql")

    if "seed" in allowed:
        logger.info("Step 2: Seeding exchanges and categories...")
        seed_database()

    if "companies" in allowed:
        logger.info("Step 3: Fetching and upserting companies...")
        session = get_session()
        try:
            for exchange in get_all_tickers():
                logger.info("Fetching companies for %s...", exchange)
                companies = fetch_all_companies(exchange)
                upsert_companies(session, companies)
                logger.info("Upserted %d companies for %s", len(companies), exchange)
        finally:
            session.close()

        logger.info("Step 3b: Classifying companies into categories...")
        session = get_session()
        try:
            from data_collection.classifier import classify_and_persist
            count = classify_and_persist(session)
            logger.info("Created %d company-category assignments", count)
        finally:
            session.close()

    if "quotes" in allowed:
        logger.info("Step 4: Downloading daily quotes...")
        download_all_quotes()

    if "indices" in allowed:
        logger.info("Step 5: Downloading index data...")
        download_all_indices()

    if "indicators" in allowed:
        logger.info("Step 6: Computing technical indicators...")
        from indicators.compute import compute_all_indicators
        company_ids = get_all_company_ids()
        for cid in company_ids:
            compute_all_indicators(cid)
        logger.info("Indicators computed for %d companies", len(company_ids))

    if "signals" in allowed:
        logger.info("Step 7: Generating signals...")
        from signals.signal_generator import compute_all_signals
        company_ids = get_all_company_ids()
        for cid in company_ids:
            compute_all_signals(cid)
        logger.info("Signals generated for %d companies", len(company_ids))

    if "effectiveness" in allowed:
        logger.info("Step 8: Checking signal effectiveness...")
        from effectiveness.check_effectiveness import compute_effectiveness
        compute_effectiveness()

    if "stats" in allowed:
        logger.info("Step 9: Computing signal statistics...")
        from statistics.signal_stats import compute_statistics
        compute_statistics()

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
