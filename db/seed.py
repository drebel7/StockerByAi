from config.settings import EXCHANGES, DATA_SOURCES, INDICES, YF_SUFFIX
from utils.database import get_session, execute_sql_file
from db.models import Exchange, DataSource, Category, Instrument


def seed_exchanges(session):
    for code, info in EXCHANGES.items():
        existing = session.query(Exchange).filter_by(code=code).first()
        if not existing:
            session.add(Exchange(code=code, name=info["name"], country=info["country"], active=True))
    session.commit()
    print(f"Seeded {len(EXCHANGES)} exchanges.")


def seed_data_sources(session):
    for code, name in DATA_SOURCES.items():
        existing = session.query(DataSource).filter_by(code=code).first()
        if not existing:
            session.add(DataSource(code=code, name=name))
    session.commit()
    print(f"Seeded {len(DATA_SOURCES)} data sources.")


CATEGORY_NAMES = [
    "drones", "AI", "silver_mining", "gold", "SMR",
    "RAM_memory", "space_industry", "semiconductors",
    "cloud_computing", "cybersecurity", "fintech",
    "biotechnology", "renewable_energy", "EV",
    "defense", "gaming", "REIT", "robotics", "blockchain",
    "telecom", "pharmaceuticals", "consumer_staples",
]


def seed_categories(session):
    for name in CATEGORY_NAMES:
        existing = session.query(Category).filter_by(name=name).first()
        if not existing:
            session.add(Category(name=name))
    session.commit()
    print(f"Seeded {len(CATEGORY_NAMES)} categories.")


def seed_index_instruments(session):
    ex_map = {ex.code: ex.id for ex in session.query(Exchange).all()}
    count = 0
    for name, yf_ticker in INDICES.items():
        if yf_ticker.startswith("^"):
            # determine exchange by country convention
            if yf_ticker in ("^WIG20", "^WIG_BANKI", "^WIG_GRY", "^WIG_UKRAINA"):
                ex_id = ex_map.get("GPW")
            else:
                ex_id = ex_map.get("NASDAQ")
        else:
            ex_id = ex_map.get("NASDAQ")
        if not ex_id:
            continue

        existing = session.query(Instrument).filter_by(ticker=yf_ticker, exchange_id=ex_id).first()
        if not existing:
            session.add(Instrument(
                ticker=yf_ticker,
                exchange_id=ex_id,
                full_name=name,
                instrument_type="index",
            ))
            count += 1
    session.commit()
    print(f"Seeded {count} index instruments.")


def seed_ibd_categories(session):
    from data_collection.ibd_classifier import seed_ibd_categories
    seed_ibd_categories(session)


def main():
    execute_sql_file("db/schema.sql")
    session = get_session()
    try:
        seed_exchanges(session)
        seed_data_sources(session)
        seed_categories(session)
        seed_ibd_categories(session)
        seed_index_instruments(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()