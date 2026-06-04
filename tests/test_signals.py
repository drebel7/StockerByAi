import pytest
from signals.signal_generator import SIGNAL_REGISTRY, volume_breakout_signal


class TestSignalRegistry:
    def test_registry_contains_volume_breakout(self):
        assert "volume_breakout" in SIGNAL_REGISTRY
        assert callable(SIGNAL_REGISTRY["volume_breakout"])

    def test_unknown_signal_raises(self):
        from signals.signal_generator import get_signal
        with pytest.raises(ValueError, match="Unknown signal"):
            get_signal("nonexistent")
