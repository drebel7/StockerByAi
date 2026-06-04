import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "stocker")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

BACKFILL_START_YEAR = 2010

EXCHANGES = {
    "GPW": {"country": "PL", "name": "Giełda Papierów Wartościowych w Warszawie"},
    "NEWCONNECT": {"country": "PL", "name": "NewConnect"},
    "NASDAQ": {"country": "US", "name": "NASDAQ"},
    "NYSE": {"country": "US", "name": "New York Stock Exchange"},
    "AMEX": {"country": "US", "name": "American Stock Exchange"},
}

INDICES = {
    "WIG20": "^WIG20",
    "WIG_BANKI": "^WIG_BANKI",
    "WIG_GRY": "^WIG_GRY",
    "WIG_UKRAINA": "^WIG_UKRAINA",
    "SPX": "^GSPC",
    "DJI": "^DJI",
    "IXIC": "^IXIC",
}

BNCHMARK_INDEX = {"PL": "^WIG20", "US": "^GSPC"}

GPW_TICKERS_FILE = "config/gpw_tickers.json"

YF_SUFFIX = {"GPW": ".WA", "NEWCONNECT": ".WA", "NASDAQ": "", "NYSE": "", "AMEX": ""}

BATCH_SIZE = 50
REQUEST_DELAY = 0.5
