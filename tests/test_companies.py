import pytest
from data_collection.companies import get_all_tickers, fetch_company_info


class TestCompanies:
    def test_get_all_tickers_has_all_exchanges(self):
        t = get_all_tickers()
        assert set(t.keys()) == {"NASDAQ", "NYSE", "AMEX", "GPW", "NEWCONNECT"}
        for ex in t:
            assert len(t[ex]) > 0

    def test_fetch_company_info_known(self):
        info = fetch_company_info("AAPL", "NASDAQ")
        assert info["full_name"] == "Apple Inc."
        assert info["sector"] is not None
