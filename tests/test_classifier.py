import pytest
from data_collection.classifier import classify_instrument, KEYWORD_MAP


class TestClassifier:
    def test_all_categories_have_patterns(self):
        for cat, patterns in KEYWORD_MAP.items():
            assert len(patterns) > 0, f"Category '{cat}' has no patterns"

    def test_ai_detected(self):
        result = classify_instrument("Technology", "Artificial Intelligence")
        assert "AI" in result

    def test_cloud_industry_detected(self):
        result = classify_instrument("Technology", "Cloud Computing")
        assert "cloud_computing" in result

    def test_gaming_detected(self):
        result = classify_instrument("Communication Services", "Electronic Gaming & Multimedia")
        assert "gaming" in result

    def test_semiconductor_detected(self):
        result = classify_instrument("Technology", "Semiconductors")
        assert "semiconductors" in result

    def test_no_match_returns_empty(self):
        result = classify_instrument("Utilities", "Diversified Utility")
        assert result == set()

    def test_biotech_detected(self):
        result = classify_instrument("Healthcare", "Biotechnology")
        assert "biotechnology" in result

    def test_none_inputs(self):
        result = classify_instrument(None, None)
        assert result == set()

    def test_fintech_by_industry(self):
        result = classify_instrument("Financial", "Fintech Payment Solutions")
        assert "fintech" in result