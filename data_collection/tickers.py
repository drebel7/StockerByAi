import csv
import io
import json
import logging
from urllib.request import urlopen

logger = logging.getLogger(__name__)

NASDAQ_LISTED_URL = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt"
OTHER_LISTED_URL = "ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt"

GPW_TICKERS_FILE = "config/gpw_tickers.json"


def _fetch_txt(url: str) -> str:
    with urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


EXCHANGE_MAP = {
    "N": "NYSE",
    "A": "AMEX",
    "P": "NYSE",
}


def fetch_us_tickers() -> dict:
    """Returns {exchange_code: [(ticker, name), ...]} for NASDAQ, NYSE, AMEX."""
    result = {"NASDAQ": [], "NYSE": [], "AMEX": []}

    raw = _fetch_txt(NASDAQ_LISTED_URL)
    reader = csv.DictReader(io.StringIO(raw), delimiter="|")
    for row in reader:
        symbol = row.get("Symbol", "").strip()
        name = row.get("Security Name", "").strip()
        if symbol and name:
            result["NASDAQ"].append((symbol, name))

    raw = _fetch_txt(OTHER_LISTED_URL)
    reader = csv.DictReader(io.StringIO(raw), delimiter="|")
    for row in reader:
        symbol = row.get("ACT Symbol", "").strip()
        name = row.get("Security Name", "").strip()
        exchange = row.get("Exchange", "").strip()
        if not symbol:
            continue
        ex_name = EXCHANGE_MAP.get(exchange)
        if ex_name:
            result[ex_name].append((symbol, name))

    for ex in list(result):
        logger.info("%s: %d tickers", ex, len(result[ex]))
    return result


def fetch_gpw_tickers() -> list:
    """Returns [(ticker, name), ...] for GPW + NewConnect from config file."""
    with open(GPW_TICKERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("gpw", []) + data.get("newconnect", [])
