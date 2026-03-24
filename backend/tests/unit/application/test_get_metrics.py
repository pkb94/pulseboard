"""Unit tests for GetMetricsUseCase and GetSingleMetricUseCase."""

import pytest
from unittest.mock import AsyncMock

from app.application.use_cases.get_metrics import GetMetricsUseCase, GetSingleMetricUseCase
from app.domain.entities.metric import MetricName, MetricSeries


def _empty_series(metric: MetricName) -> MetricSeries:
    return MetricSeries(metric=metric, points=[])


class TestGetMetricsUseCase:
    async def test_returns_snapshot_with_all_metrics(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(side_effect=lambda m, since: _empty_series(m))

        use_case = GetMetricsUseCase(metric_repo=repo)
        result = await use_case.execute(window_minutes=60)

        assert len(result.metrics) == len(MetricName)

    async def test_snapshot_has_timestamp(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(side_effect=lambda m, since: _empty_series(m))

        use_case = GetMetricsUseCase(metric_repo=repo)
        result = await use_case.execute()

        assert result.snapshot_at is not None

    async def test_get_series_called_for_every_metric(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(side_effect=lambda m, since: _empty_series(m))

        use_case = GetMetricsUseCase(metric_repo=repo)
        await use_case.execute(window_minutes=30)

        assert repo.get_series.call_count == len(MetricName)

    async def test_dto_metric_names_match_all_enum_values(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(side_effect=lambda m, since: _empty_series(m))

        use_case = GetMetricsUseCase(metric_repo=repo)
        result = await use_case.execute()

        returned_names = {m.metric for m in result.metrics}
        assert returned_names == set(MetricName)


class TestGetSingleMetricUseCase:
    async def test_returns_correct_metric(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(
            return_value=_empty_series(MetricName.CPU_USAGE)
        )

        use_case = GetSingleMetricUseCase(metric_repo=repo)
        result = await use_case.execute(MetricName.CPU_USAGE, window_minutes=60)

        assert result.metric == MetricName.CPU_USAGE

    async def test_calls_repo_with_correct_metric(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(
            return_value=_empty_series(MetricName.LATENCY_P99)
        )

        use_case = GetSingleMetricUseCase(metric_repo=repo)
        await use_case.execute(MetricName.LATENCY_P99, window_minutes=15)

        call_args = repo.get_series.call_args
        assert call_args[0][0] == MetricName.LATENCY_P99

    async def test_dto_has_label_and_unit(self):
        repo = AsyncMock()
        repo.get_series = AsyncMock(
            return_value=_empty_series(MetricName.CPU_USAGE)
        )

        use_case = GetSingleMetricUseCase(metric_repo=repo)
        result = await use_case.execute(MetricName.CPU_USAGE)

        assert result.label == "CPU Usage"
        assert result.unit == "%"
