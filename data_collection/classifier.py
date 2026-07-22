import logging
import re
import time
from typing import Optional

import yfinance as yf

from config.settings import YF_SUFFIX

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
        r"\bgold\b", r"\bprecious metals?\b",
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
        r"\baerospace", r"\baerospace & defense",
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
        r"\bgaming\b", r"\bgames?\b", r"\bvideo game",
        r"\besports", r"\binteractive entertainment",
        r"\bgambling\b", r"\bcasino\b",
        r"\bmobile (game|gaming)",
        r"\bgame developer", r"\bcomputer games",
        r"\bconsole games", r"\bgame publisher",
        r"\bcd projekt", r"\bci games",
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
        r"\bconsumer staples", r"\bhousehold product",
        r"\bpersonal care", r"\bpackaged food",
        r"\bnon.cyclical",
        r"\bcosmetic", r"\bperfume\b",
        r"\bskin care", r"\bpersonal products",
        r"\bhousehold.&.personal",
        r"\bluxury goods", r"\btobacco\b",
        r"\bconsumer goods",
    ],
    "banks": [
        r"\bbank\b", r"\bbanking\b", r"\bbankowy",
        r"\bfinancial (group|services|holding|institution)",
        r"\bbanco\b", r"\bbanque\b",
        r"\bcash loans?\b", r"\blending\b",
        r"\bcredit (services?|facility|card)",
        r"\bconsumer finance",
    ],
    "insurance": [
        r"\binsurance\b", r"\bubezpiecz",
        r"\breinsurance", r"\bbroker\b.*\b(insurance)",
        r"\bpolis\b",
    ],
    "investment_management": [
        r"\basset management", r"\binvestment (management|services|advisory|banking|holding|company|manager)",
        r"\bwealth management", r"\bprivate equity",
        r"\bventure capital", r"\bcapital (partners|group|management)",
        r"\bfund management", r"\bportfolio management",
        r"\badvisory services", r"\btowarzystwo funduszy",
        r"\bfundusz",
    ],
    "technology": [
        r"\btechnology\b", r"\bsoftware\b", r"\bit services",
        r"\binformation technology", r"\btech\b",
        r"\bdigital\b", r"\bcomputing\b",
        r"\bplatform\b", r"\bapplication software",
        r"\binformatyka", r"\btechnologie",
        r"\bassecov",
    ],
    "software": [
        r"\bsoftware\b", r"\bprogramming\b",
        r"\bapplication software", r"\benterprise software",
        r"\berp\b", r"\bcrm\b",
        r"\bdeveloper tools", r"\bdevops\b",
        r"\bopensource", r"\bopen source",
    ],
    "it_consulting": [
        r"\bit (services|consulting|solutions)",
        r"\btechnology consulting",
        r"\bdigital transformation",
        r"\boutsourcing\b.*\b(it|technology)",
        r"\bsystem integration",
        r"\bconsulting\b",
    ],
    "ecommerce": [
        r"\be.?commerce\b", r"\be.?retail\b",
        r"\bonline (retail|shop|store|market)",
        r"\bmarketplace\b", r"\bshopping\b",
        r"\bdigital commerce",
        r"\be.?business\b",
        r"\ballegro", r"\bamazon\b",
    ],
    "retail": [
        r"\bretail\b", r"\bwholesale\b",
        r"\bdepartment store", r"\bsupermarket",
        r"\bhypermarket", r"\bconvenience store",
        r"\bspecialty retail", r"\bhandel\b",
        r"\bdetaliczn", r"\bconsumer (retail|electronics)",
        r"\bstore\b", r"\bsklep\b",
        r"\bdiscount retailer", r"\belectronic retailer",
        r"\bgrocery\b",
    ],
    "real_estate": [
        r"\breal estate", r"\bproperty (development|investment|manager)",
        r"\bnieruchom",
        r"\bdeweloper", r"\barchicom",
        r"\bapartment", r"\bresidential\b",
        r"\bcommercial property",
        r"\breal estate investment",
    ],
    "construction": [
        r"\bconstruction\b", r"\bbuilding\b",
        r"\binfrastructure\b", r"\bbudownictw",
        r"\bbudowlany", r"\bbudimex",
        r"\bengineering\b.*\b(construction)",
        r"\bgeneral contractor",
        r"\bconstruction materials",
        r"\bcement\b", r"\baggregate\b",
    ],
    "energy": [
        r"\boil\b.*\b(gas|exploration|production|refining)",
        r"\benergy\b", r"\bpetroleum\b",
        r"\bnatural gas", r"\bcrude oil",
        r"\bupstream\b", r"\bdownstream\b",
        r"\bmidstream\b", r"\benergetyka\b",
        r"\bgazownictw", r"\bnafta\b",
        r"\bpaliw", r"\bpetrochem",
    ],
    "utilities": [
        r"\butilities?\b", r"\belectric\b",
        r"\bwater\b", r"\bgas distribution",
        r"\bpower (plant|generation|utility)",
        r"\belectrical (utility|power)",
        r"\benergy (utility|provider|supply)",
        r"\bgrid operator",
    ],
    "manufacturing": [
        r"\bmanufactur", r"\bindustrial\b",
        r"\bproduction\b", r"\bprzemysł",
        r"\bprodukcj", r"\bfactory\b",
        r"\bassembly\b", r"\bfabrication",
        r"\bmachinery\b",
        r"\belectrical equipment\b", r"\bfurnishings?\b",
        r"\bfixtures?\b", r"\bappliances?\b",
        r"\bbusiness equipment\b",
    ],
    "mining": [
        r"\bmining\b", r"\bmine\b", r"\bgornictw",
        r"\bkopalni", r"\bexploration\b.*\b(mineral|metal)",
        r"\bmineral\b", r"\bore\b",
        r"\bkghm\b",
        r"\bcopper\b",
    ],
    "steel": [
        r"\bsteel\b", r"\bstal\b", r"\bhutnic",
        r"\biron\b", r"\bferrous\b",
        r"\bmetallurg", r"\brolled (steel|metal)",
    ],
    "chemicals": [
        r"\bchemical", r"\bchemia\b", r"\bchemiczn",
        r"\bpetrochemical", r"\bfertilizer",
        r"\bpigment", r"\bcoating\b",
        r"\bplastic\b", r"\bpolimer",
        r"\bpcc\b",
    ],
    "agriculture": [
        r"\bagricultur", r"\bagricol\b",
        r"\bfarming\b", r"\bfarm\b",
        r"\bagro\b", r"\bcrop\b",
        r"\blivestock", r"\bagribusiness",
        r"\brolnic", r"\bupraw",
        r"\bhodowl", r"\bgrass\b",
    ],
    "food": [
        r"\bfood\b", r"\bspożywcz",
        r"\bfood processing", r"\bżywności",
        r"\bpackaged food", r"\bdairy\b",
        r"\bbakery\b", r"\bmeat\b",
        r"\bconfectionery", r"\bfruit\b",
        r"\bvegetable", r"\bfrozen food",
        r"\bżywiec",
        r"\bsweets?\b", r"\bcand(y|ies)\b",
        r"\brestaurant", r"\bburger\b",
        r"\bquick service",
        r"\bconfectioners?\b",
    ],
    "beverages": [
        r"\bbeverage", r"\bdrink\b", r"\bnapoje\b",
        r"\bbrewery", r"\bwine\b", r"\bdistillery",
        r"\bsoft drink", r"\bjuice\b",
        r"\bwater\b.*\b(bottling|spring)",
        r"\bpiwo\b", r"\balkohol",
        r"\bwódk", r"\bwiniarn",
    ],
    "media": [
        r"\bmedia\b", r"\bbroadcasting\b",
        r"\bpublishing\b", r"\bpublishes?\b",
        r"\btelevision\b",
        r"\bradio\b", r"\bnewspaper\b",
        r"\badvertising\b", r"\bcontent\b",
        r"\bentertainment\b",
        r"\bagora\b", r"\bcyfrowy polsat",
        r"\btelewizj", r"\bwydawnictw",
        r"\bbooks?\b",
    ],
    "transportation": [
        r"\btransport", r"\blogistics\b",
        r"\bshipping\b", r"\bairline\b",
        r"\brailway\b", r"\bfreight\b",
        r"\bcourier\b", r"\bdelivery\b",
        r"\bcarrier\b", r"\bzarząd\b.*\b(port|lotnis)",
        r"\blogistyk", r"\bspedycj",
        r"\bkolej\b", r"\bżeglug",
        r"\btrucking\b", r"\bairlines?\b",
    ],
    "automotive": [
        r"\bauto\b", r"\bautomotive\b",
        r"\bcar\b", r"\bmotor\b",
        r"\bvehicle\b", r"\bparts?\b.*\b(auto)",
        r"\btyre\b", r"\btire\b",
        r"\bmotoryzacj",
        r"\brecreational vehicles?\b",
    ],
    "wood_paper": [
        r"\bwood\b", r"\bpaper\b", r"\bforest\b",
        r"\btimber\b", r"\bdrzewn",
        r"\bpapiernicz", r"\bpulp\b",
        r"\bcardboard", r"\bpackaging\b",
        r"\bopakowan",
    ],
    "textiles": [
        r"\btextile", r"\bapparel\b", r"\bclothing\b",
        r"\bgarment", r"\bfashion\b",
        r"\bfabric\b", r"\bfootwear\b",
        r"\bodzież", r"\bwłókienn",
    ],
    "healthcare": [
        r"\bhealthcare\b", r"\bhealth\b",
        r"\bhospital\b", r"\bmedical\b",
        r"\bclinical\b", r"\bdiagnostic\b",
        r"\bpatient\b", r"\bmedicover",
        r"\blekar", r"\bzdrowi",
        r"\bmedyczn", r"\bszpital",
    ],
    "medical_devices": [
        r"\bmedical (device|equipment|instrument|supply)",
        r"\bdental\b", r"\bsurgical\b",
        r"\bimplant\b", r"\bprosthetic",
        r"\bdiagnostic equipment",
        r"\boptoelectronic.*\b(medical|health)",
        r"\bcardiology", r"\borthopedic",
    ],
    "education": [
        r"\beducation\b", r"\btraining\b",
        r"\be.?learning\b", r"\bschool\b",
        r"\buniversity\b", r"\beducational",
        r"\bedukacj", r"\bszkoleni",
    ],
    "hotel_tourism": [
        r"\bhotel\b", r"\bresort\b",
        r"\btourism\b", r"\btravel\b",
        r"\bhospitality\b", r"\bcatering\b",
        r"\bhotelarstw", r"\bturystyk",
        r"\bhotele\b",
        r"\bleisure\b",
    ],
    "waste_management": [
        r"\bwaste\b", r"\brecycling\b",
        r"\bwaste management", r"\blandfill\b",
        r"\bgospodark.*odpad",
        r"\brecykling",
        r"\bpollution\b", r"\btreatment controls?\b",
    ],
    "business_services": [
        r"\bspecialty business services?\b",
        r"\bstaffing\b", r"\bemployment services?\b",
        r"\bpersonal services?\b",
        r"\brental\b.*\b(leasing|services)",
        r"\bbusiness services?\b",
        r"\brecruiting\b", r"\btemporary staffing",
    ],
    "holding": [
        r"\bholding\b", r"\bholding (company|group)",
        r"\bcapital group", r"\bgrupa kapitał",
        r"\bnon.performing", r"\bdebt (collection|management|recovery|purchasing)",
        r"\bsecuritization",
        r"\bconglomerates?\b",
    ],
}

ALL_CATEGORY_NAMES = sorted(KEYWORD_MAP.keys())


def classify_instrument(sector: Optional[str] = None,
                        industry: Optional[str] = None,
                        full_name: Optional[str] = None,
                        business_summary: Optional[str] = None) -> set:
    texts = []
    if sector:
        texts.append(sector)
    if industry:
        texts.append(industry)
    if full_name:
        texts.append(full_name)
    if business_summary:
        texts.append(business_summary)

    text = " ".join(texts).lower()
    if not text.strip():
        return set()

    matched = []
    for category, patterns in KEYWORD_MAP.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched.append(category)
                break

    return set(matched[:3])


def fetch_business_summaries(instruments: list, exchange_code: str) -> dict:
    suffix = YF_SUFFIX.get(exchange_code, "")
    results = {}
    batch_size = 3
    total = len(instruments)
    max_retries = 2

    for i in range(0, total, batch_size):
        batch = instruments[i:i + batch_size]
        for inst in batch:
            yf_ticker = f"{inst.ticker}{suffix}"
            for attempt in range(max_retries + 1):
                try:
                    info = yf.Ticker(yf_ticker).info
                    summary = info.get("longBusinessSummary") or info.get("businessSummary")
                    if summary:
                        results[inst.id] = summary
                    break
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(2)
                    else:
                        logger.debug("Failed to fetch summary for %s after %d retries: %s",
                                     yf_ticker, max_retries, e)
        time.sleep(1.5)
        if (i // batch_size) % 20 == 0 or i + len(batch) >= total:
            logger.info("Fetched summaries %d/%d for %s", min(i + len(batch), total), total, exchange_code)

    return results


def classify_all_instruments(session) -> dict:
    from db.models import Instrument, Category

    instruments = session.query(Instrument).filter(
        Instrument.instrument_type == "stock"
    ).all()

    assignments = {}

    # Phase 1: classify using sector/industry/name only
    no_sector_group = []
    for inst in instruments:
        matched = classify_instrument(sector=inst.sector, industry=inst.industry, full_name=inst.full_name)
        if matched:
            assignments[inst.id] = matched
        elif not inst.sector and not inst.industry:
            no_sector_group.append(inst)

    logger.info("Phase 1: classified %d/%d by sector/industry/name", len(assignments), len(instruments))

    # Phase 2: for instruments without sector/industry, fetch business summary from yfinance
    additional_phase2 = 0
    if no_sector_group:
        # group by exchange for correct suffix
        from db.models import Exchange
        by_exchange = {}
        for inst in no_sector_group:
            by_exchange.setdefault(inst.exchange_id, []).append(inst)

        ex_names = {e.id: e.code for e in session.query(Exchange).all()}

        for ex_id, group in by_exchange.items():
            ex_code = ex_names.get(ex_id, "")
            if not ex_code:
                continue
            summaries = fetch_business_summaries(group, ex_code)
            for inst in group:
                summary = summaries.get(inst.id)
                if not summary:
                    continue
                matched = classify_instrument(
                    sector=inst.sector, industry=inst.industry,
                    full_name=inst.full_name, business_summary=summary
                )
                if matched:
                    assignments[inst.id] = matched
                    additional_phase2 += 1

        logger.info("Phase 2: classified %d additional from yfinance summaries", additional_phase2)

    total_classified = len(assignments)
    total_instruments = len(instruments)
    logger.info("Total classified %d/%d instruments", total_classified, total_instruments)
    return assignments


def auto_create_missing_categories(session, assignments: dict):
    from db.models import Category

    assigned_names = set()
    for cats in assignments.values():
        assigned_names.update(cats)

    existing_names = {c.name for c in session.query(Category).all()}
    new_names = [n for n in ALL_CATEGORY_NAMES if n not in existing_names]

    for name in new_names:
        session.add(Category(name=name, source="manual"))
    if new_names:
        session.commit()
        logger.info("Created %d new categories: %s", len(new_names), new_names)

    # also create any assigned names that might not exist yet
    to_create = assigned_names - existing_names - set(new_names)
    for name in to_create:
        session.add(Category(name=name, source="manual"))
    if to_create:
        session.commit()
        logger.info("Created %d additional categories from assignments", len(to_create))


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
    auto_create_missing_categories(session, assignments)
    return persist_classifications(session, assignments)
