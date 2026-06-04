import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL


@pytest.fixture(scope="session")
def engine():
    e = create_engine(DATABASE_URL, pool_pre_ping=True)
    return e


@pytest.fixture(scope="function")
def session(engine):
    conn = engine.connect()
    trans = conn.begin()
    Session = sessionmaker(bind=conn)
    sess = Session()
    yield sess
    sess.close()
    trans.rollback()
    conn.close()
