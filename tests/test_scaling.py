"""Tests for HiDPI scaling detection (pure logic; no display required)."""
import math

from ui.scaling import clamp_scale, detect_scale_from_dpi


class TestClampScale:
    def test_within_range_passthrough(self):
        assert clamp_scale(1.5) == 1.5

    def test_below_min_clamped(self):
        assert clamp_scale(0.5) == 1.0
        assert clamp_scale(0.0) == 1.0

    def test_above_max_clamped(self):
        assert clamp_scale(3.0) == 2.5

    def test_nan_returns_min(self):
        assert clamp_scale(float("nan")) == 1.0

    def test_negative_returns_min(self):
        assert clamp_scale(-2.0) == 1.0


class TestDetectScaleFromDpi:
    def test_baseline_96_is_unity(self):
        assert detect_scale_from_dpi(96.0) == 1.0

    def test_144_dpi_is_1_5(self):
        assert detect_scale_from_dpi(144.0) == 1.5

    def test_192_dpi_is_2_0(self):
        assert detect_scale_from_dpi(192.0) == 2.0

    def test_384_dpi_clamped_to_max(self):
        assert detect_scale_from_dpi(384.0) == 2.5

    def test_low_dpi_clamped_to_min(self):
        assert detect_scale_from_dpi(48.0) == 1.0

    def test_zero_dpi_returns_min(self):
        assert detect_scale_from_dpi(0.0) == 1.0

    def test_invalid_baseline_returns_min(self):
        assert detect_scale_from_dpi(144.0, baseline=0.0) == 1.0

    def test_fractional_dpi(self):
        assert math.isclose(detect_scale_from_dpi(120.0), 1.25)

    def test_near_baseline_rounds_to_unity(self):
        assert detect_scale_from_dpi(96.1) == 1.0
