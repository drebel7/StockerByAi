from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    return SessionLocal()


def ensure_partitions(engine, start_year=2010, end_year=None):
    from datetime import date
    end_year = end_year or date.today().year + 1
    with engine.begin() as conn:
        for year in range(start_year, end_year + 1):
            partition_name = f"daily_quotes_{year}"
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-01-01"
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF daily_quotes
                FOR VALUES FROM ('{start_date}') TO ('{end_date}')
            """))
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{partition_name}_date_instrument
                ON {partition_name} (date, instrument_id)
            """))


def execute_sql_file(filepath: str) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))


def batch_upsert(df, table_name, engine, index_elements):
    from sqlalchemy.dialects.postgresql import insert

    with engine.begin() as conn:
        stmt = insert(table_name).values(df.to_dict(orient="records"))
        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_={c: stmt.excluded[c] for c in df.columns if c not in index_elements},
        )
        conn.execute(stmt)
