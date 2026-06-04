import logging
import time
from datetime import date

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert

from config.settings import INDICES, BACKFILL_START_YEAR, REQUEST_DELAY
from utils.database import engine

logger = logging.getLogger(__name__)


def download_index_data(name: str, yf_ticker: str) -> pd.DataFrame:
    start = f"{BACKFILL_START_YEAR}-01-01"
    end = date.today().isoformat()
    try:
        df = yf.download(yf_ticker, start=start, end=end, progress=False, auto_adjust=True)
        time.sleep(REQUEST_DELAY)
    except Exception as e:
        logger.warning("Failed to download index %s: %s", name, e)
        return pd.DataFrame()

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    df["index_name"] = name
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date", "index": "date"}, inplace=True)
    return df


def download_all_indices():
    for name, yf_ticker in INDICES.items():
        df = download_index_data(name, yf_ticker)
        if not df.empty:
            logger.info("Downloaded %s: %d rows", name, len(df))
