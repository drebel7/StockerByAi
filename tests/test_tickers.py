import pytest
from data_collection.tickers import fetch_us_tickers


class TestTickers:
    def test_us_tickers_returns_all_exchanges(self):
        result = fetch_us_tickers()
        for ex in ("NASDAQ", "NYSE", "AMEX"):
            assert ex in result
            assert len(result[ex]) > 0

    def test_ticker_format(self):
        result = fetch_us_tickers()
        for ex in result:
            ticker, name = result[ex][0]
            assert isinstance(ticker, str) and len(ticker) > 0
            assert isinstance(name, str) and len(name) > 0
