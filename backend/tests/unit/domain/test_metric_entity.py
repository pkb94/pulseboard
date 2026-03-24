"""Unit tests for MetricPoint and MetricSeries domain entities."""

import pytest
from datetime import datetime

from app.domain.entities.metric import MetricName, MetricPoint, MetricSeries


def _pt(metric: MetricName = MetricName.CPU_USAGE, value: float = 50.0) -> MetricPoint:
    return MetricPoint(metric=metric, value=value, timestamp=datetime.utcnow())


# ── MetricPoint ────────────────────────────────────────────────────────────────

class TestMetricPoint:
    def test_valid_creation(self):
        pt = _pt(value=75.0)
        assert pt.value == 75.0
        assert pt.metric == MetricName.CPU_USAGE

    def test_zero_value_is_allowed(self):
        pt = _pt(value=0.0)
        assert pt.value == 0.0

    def test_negative_value_raises_for_cpu(self):
        with pytest.raises(ValueError):
            MetricPoint(metric=MetricName.CPU_USAGE, value=-1.0, timestamp=datetime.utcnow())

    def test_negative_value_raises_for_error_rate(self):
        with pytest.raises(ValueError):
            MetricPoint(metric=MetricName.ERROR_RATE, value=-0.5, timestamp=datetime.utcnow())

    def test_negative_revenue_is_allowed(self):
        pt = MetricPoint(
            metric=MetricName.REVENUE_PER_MIN,
            value=-100.0,
            timestamp=datetime.utcnow(),
        )
        assert pt.value == -100.0

    def test_frozen_prevents_mutation(self):
        pt = _pt()
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            pt.value = 99.0  # type: ignore[misc]


# ── MetricSeries ───────────────────────────────────────────────────────────────

class TestMetricSeries:
    def test_latest_is_none_when_empty(self):
        series = MetricSeries(metric=MetricName.CPU_USAGE)
        assert series.latest is None

    def test_latest_returns_last_added_point(self):
        pts = [_pt(value=float(i)) for i in range(5)]
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=pts)
        assert series.latest == pts[-1]

    def test_current_value_is_zero_when_empty(self):
        series = MetricSeries(metric=MetricName.CPU_USAGE)
        assert series.current_value == 0.0

    def test_current_value_matches_latest_point(self):
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=[_pt(value=42.0)])
        assert series.current_value == 42.0

    def test_change_pct_returns_zero_with_too_few_points(self):
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=[_pt(value=10.0)])
        assert series.change_pct() == 0.0

    def test_change_pct_positive_increase(self):
        # 6 points; oldest-in-window = 10.0, latest = 20.0 → +100%
        pts = [_pt(value=10.0)] * 5 + [_pt(value=20.0)]
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=pts)
        assert series.change_pct() == pytest.approx(100.0)

    def test_change_pct_negative_decrease(self):
        pts = [_pt(value=20.0)] * 5 + [_pt(value=10.0)]
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=pts)
        assert series.change_pct() == pytest.approx(-50.0)

    def test_change_pct_zero_when_old_value_is_zero(self):
        pts = [_pt(value=0.0)] * 5 + [_pt(value=10.0)]
        series = MetricSeries(metric=MetricName.CPU_USAGE, points=pts)
        assert series.change_pct() == 0.0

    def test_is_breaching_upper_threshold_true(self):
        series = MetricSeries(
            metric=MetricName.CPU_USAGE,
            points=[_pt(value=90.0)],
            threshold_upper=85.0,
        )
        assert series.is_breaching_threshold() is True

    def test_is_breaching_upper_threshold_false(self):
        series = MetricSeries(
            metric=MetricName.CPU_USAGE,
            points=[_pt(value=50.0)],
            threshold_upper=85.0,
        )
        assert series.is_breaching_threshold() is False

    def test_no_threshold_never_breaches(self):
        series = MetricSeries(
            metric=MetricName.CPU_USAGE,
            points=[_pt(value=9999.0)],
        )
        assert series.is_breaching_threshold() is False
