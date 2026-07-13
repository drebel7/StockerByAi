import csv
import logging
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from config.settings import DATABASE_URL
from utils.database import engine, get_session
from db.models import Category

logger = logging.getLogger(__name__)

IBD_CSV = Path(__file__).parent.parent / "config" / "ibd_industry_groups.csv"


def load_ibd_map() -> dict[str, str]:
    ibd = {}
    with open(IBD_CSV) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                ticker = row[0].strip().upper()
                group = row[1].strip()
                if group != "Group not available":
                    ibd[ticker] = group
    return ibd


def _normalize(t: str) -> str:
    return t.upper().replace(".", "").replace("-", "").replace("/", "")


def seed_ibd_categories(session):
    ibd = load_ibd_map()
    groups = sorted(set(ibd.values()))
    existing = {c.name for c in session.query(Category).all()}
    for name in groups:
        if name not in existing:
            session.add(Category(name=name))
    session.commit()
    logger.info("Seeded %d IBD categories", len(groups) - len(existing))


def classify_us_instruments(session) -> int:
    from db.models import Instrument, instrument_categories as ic_table

    ibd = load_ibd_map()
    cat_map = {c.name: c.id for c in session.query(Category).all()}

    instruments = session.query(Instrument).filter(
        Instrument.instrument_type == "stock",
    ).all()

    assignments = {}
    for inst in instruments:
        norm = _normalize(inst.ticker)
        if norm in ibd:
            assignments[inst.id] = ibd[norm]

    # Remove old IBD-based assignments (keep keyword-based ones)
    ibd_cat_ids = {v for k, v in cat_map.items() if v is not None}
    session.execute(
        ic_table.delete().where(ic_table.c.category_id.in_(list(ibd_cat_ids)))
    )
    session.commit()

    # Insert new
    rows = []
    for inst_id, group_name in assignments.items():
        cat_id = cat_map.get(group_name)
        if cat_id:
            rows.append({"instrument_id": inst_id, "category_id": cat_id})

    if not rows:
        return 0

    stmt = insert(ic_table).values(rows)
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    session.commit()
    logger.info("Classified %d US instruments via IBD industry groups", len(rows))
    return len(rows)
