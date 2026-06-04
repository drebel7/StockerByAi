from config.settings import EXCHANGES, INDICES
from utils.database import get_session, execute_sql_file
from db.models import Exchange, Category


def seed_exchanges(session):
    for code, info in EXCHANGES.items():
        existing = session.query(Exchange).filter_by(code=code).first()
        if not existing:
            session.add(Exchange(code=code, name=info["name"], country=info["country"]))
    session.commit()
    print(f"Seeded {len(EXCHANGES)} exchanges.")


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


def main():
    execute_sql_file("db/schema.sql")
    session = get_session()
    try:
        seed_exchanges(session)
        seed_categories(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
