from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    return SessionLocal()


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
