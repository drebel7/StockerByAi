import logging
import re

logger = logging.getLogger(__name__)

KEYWORD_MAP = {
    "AI": [
        r"\bai\b", r"\bartificial intelligence", r"\bmachine learning",
        r"\bllm\b", r"\blarge language model", r"\bneural network",
        r"\bdeep learning", r"\bnlp\b", r"\bcomputer vision",
        r"\bgpt\b", r"\bgenai\b", r"\bgenerative ai",
    ],
    "drones": [
        r"\bdrones?\b", r"\buav\b", r"\bunmanned aerial",
        r"\bquadcopter", r"\bdrone",
    ],
    "semiconductors": [
        r"\bsemiconductor", r"\bchip\b", r"\bmicrochip",
        r"\bfabless", r"\bfoundry", r"\bsilicon\b",
        r"\bwafer\b", r"\basic\b", r"\bfpga\b",
        r"\bintegrated circuit", r"\bvliw\b",
        r"\bmemory (chip|module|device)",
        r"\bnand\b", r"\bflash\b", r"\bdram\b",
    ],
    "silver_mining": [
        r"\bsilver\b.*\b(mining|mine|producer|exploration)",
        r"\bsilver\b.*\b(corp|inc|company)",
    ],
    "gold": [
        r"\bgold\b.*\b(mining|mine|producer|exploration)",
        r"\bgold\b.*\b(corp|inc|company)",
        r"\bprecious metals?\b",
    ],
    "SMR": [
        r"\bsmall modular reactor", r"\bsmr\b",
        r"\bnuclear\b.*\b(reactor|energy|power)",
        r"\badvanced reactor",
    ],
    "RAM_memory": [
        r"\bram\b", r"\bmemory (module|chip|device|product)",
        r"\bdram\b", r"\bnand\b", r"\bstorage (chip|device)",
        r"\bssd\b", r"\bsolid.state",
    ],
    "space_industry": [
        r"\bspace\b", r"\bsatellite", r"\blaunch (vehicle|system)",
        r"\baerospace", r"\bdefense",
        r"\borbital", r"\bconstellation",
    ],
    "cloud_computing": [
        r"\bcloud\b", r"\bsaas\b", r"\biaas\b", r"\bpaas\b",
        r"\bcloud.computing", r"\bcloud.based",
        r"\binfrastructure as a service",
        r"\bplatform as a service",
    ],
    "cybersecurity": [
        r"\bcyber", r"\bsecurity\b", r"\bthreat (intelligence|detection)",
        r"\bendpoint protection", r"\bfirewall",
        r"\bencrypt", r"\bantivirus", r"\bzero.trust",
        r"\bidentity (management|protection)",
        r"\bcloud.security", r"\bnetwork.security",
    ],
    "fintech": [
        r"\bfintech\b", r"\bfinancial technology",
        r"\bpayments?\b", r"\bdigital banking",
        r"\bblockchain", r"\bcrypto",
        r"\bpayment processing", r"\bmobile payment",
        r"\bneobank", r"\binsurtech",
    ],
    "biotechnology": [
        r"\bbiotech", r"\bbiotechnology", r"\bbio\b.*\b(tech|pharma)",
        r"\bgene\b", r"\bgenom", r"\bcrispr",
        r"\bcell therapy", r"\bgene therapy",
        r"\bantibody", r"\bvaccine", r"\bimmuno",
        r"\bmrna\b", r"\bprotein",
    ],
    "renewable_energy": [
        r"\brenewable", r"\bsolar\b", r"\bwind\b",
        r"\bphotovoltaic", r"\bclean energy",
        r"\bgrid\b", r"\bbattery\b",
        r"\benergy storage", r"\bgreen energy",
        r"\bhydrogen\b", r"\bgeothermal",
    ],
    "EV": [
        r"\belectric vehicle", r"\bev\b",
        r"\belectric car", r"\bbattery (electric|ev)",
        r"\bcharging (station|infrastructure)",
        r"\bautonomous vehicle",
    ],
    "defense": [
        r"\bdefense\b", r"\bmilitary\b", r"\baerospace & defense",
        r"\bweapon", r"\barmament",
        r"\bgovernment contracting",
    ],
    "gaming": [
        r"\bgaming\b", r"\bvideo game", r"\besports",
        r"\binteractive entertainment",
        r"\bgambling\b", r"\bcasino\b",
        r"\bmobile (game|gaming)",
    ],
    "REIT": [
        r"\breit\b", r"\breal estate investment trust",
        r"\bcommercial real estate",
        r"\breal estate.*(invest|trust)",
    ],
    "robotics": [
        r"\brobot", r"\bautomation\b",
        r"\bautonomous (system|vehicle|robot)",
        r"\bindustrial automation",
        r"\bprocess automation",
    ],
    "blockchain": [
        r"\bblockchain\b", r"\bcryptocurrency",
        r"\bcrypto\b", r"\bdigital asset",
        r"\bdistributed ledger", r"\bweb3\b",
        r"\bdefi\b", r"\bnon.fungible",
    ],
    "telecom": [
        r"\btelecom", r"\btelecommunications",
        r"\bwireless\b", r"\bcell\b.*\b(tower|site)",
        r"\b5g\b", r"\bfiber\b",
        r"\bbroadband\b", r"\bnetwork (operator|provider)",
    ],
    "pharmaceuticals": [
        r"\bpharma", r"\bpharmaceutical",
        r"\bdrug\b", r"\bmedic",
        r"\btherapeutic", r"\bclinical trial",
    ],
    "consumer_staples": [
        r"\bconsumer staples", r"\bfood\b",
        r"\bbeverage", r"\bhousehold product",
        r"\bpersonal care", r"\bpackaged food",
        r"\bnon.cyclical",
    ],
}


def classify_instrument(sector: str, industry: str) -> set:
    if not sector and not industry:
        return set()
    text = f"{sector or ''} {industry or ''}".lower()
    matched = set()
    for category, patterns in KEYWORD_MAP.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched.add(category)
                break
    return matched


def classify_all_instruments(session) -> dict:
    from db.models import Instrument

    instruments = session.query(Instrument).filter(Instrument.instrument_type == "stock").all()
    cat_map = {c.name: c.id for c in session.query(Category).all()}

    assignments = {}
    for inst in instruments:
        matched = classify_instrument(inst.sector, inst.industry)
        if matched:
            assignments[inst.id] = matched

    logger.info("Classified %d/%d instruments into categories", len(assignments), len(instruments))
    return assignments


def persist_classifications(session, assignments: dict):
    from sqlalchemy.dialects.postgresql import insert
    from db.models import instrument_categories as ic_table, Category

    cat_map = {c.name: c.id for c in session.query(Category).all()}
    rows = []
    for instrument_id, cat_names in assignments.items():
        for name in cat_names:
            cat_id = cat_map.get(name)
            if cat_id:
                rows.append({"instrument_id": instrument_id, "category_id": cat_id})

    if not rows:
        return 0

    stmt = insert(ic_table).values(rows)
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    session.commit()
    logger.info("Inserted %d instrument-category assignments", len(rows))
    return len(rows)


def classify_and_persist(session):
    assignments = classify_all_instruments(session)
    return persist_classifications(session, assignments)