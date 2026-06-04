import pytest


class TestSMA:
    def test_sma_function_exists(self):
        from indicators.sma import sma, compute_all_sma
        assert callable(sma)
        assert callable(compute_all_sma)


class TestOBV:
    def test_obv_function_exists(self):
        from indicators.obv import obv
        assert callable(obv)


class TestADR_ATR:
    def test_functions_exist(self):
        from indicators.adr_atr import adr, atr
        assert callable(adr)
        assert callable(atr)


class TestRS:
    def test_rs_function_exists(self):
        from indicators.rs import rs
        assert callable(rs)


class TestVolume:
    def test_functions_exist(self):
        from indicators.volume import avg_volume, avg_turnover
        assert callable(avg_volume)
        assert callable(avg_turnover)
