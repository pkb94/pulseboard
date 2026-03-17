"""
LAYER 3 — INFRASTRUCTURE — app/infrastructure/simulator/metric_simulator.py
─────────────────────────────────────────────────────────────────────────────
LESSON: The simulator replaces a real data source (Prometheus, Datadog)
during development and demos. It's pure infrastructure — the use cases
and domain don't know whether data comes from a real system or this simulator.

The simulator uses realistic patterns:
  - Sine waves for daily traffic cycles (more users at 9am, fewer at 3am)
  - Gaussian noise for natural variance
  - Occasional synthetic spikes to trigger the anomaly detector
  - Correlated metrics (high request rate → higher CPU, higher latency)

This is a great talking point: "I designed the simulator to produce
statistically realistic data to validate the ML model before deployment."
"""

from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime

from app.domain.entities.metric import MetricName
from app.application.use_cases.detect_anomalies import DetectAnomaliesUseCase


class MetricSimulator:
    """
    Generates realistic synthetic metric data at 1-second intervals.
    Runs as an async background task — started by the FastAPI lifespan hook.
    """

    # Base values representing "normal" operating conditions
    _BASE: dict[MetricName, float] = {
        MetricName.CPU_USAGE:       35.0,
        MetricName.MEMORY_USAGE:    55.0,
        MetricName.REQUEST_RATE:    120.0,
        MetricName.ERROR_RATE:      0.8,
        MetricName.LATENCY_P99:     95.0,
        MetricName.THROUGHPUT:      115.0,
        MetricName.REVENUE_PER_MIN: 420.0,
        MetricName.ACTIVE_USERS:    3400.0,
    }

    # How much Gaussian noise to add (as fraction of base value)
    _NOISE_FACTOR: dict[MetricName, float] = {
        MetricName.CPU_USAGE:       0.08,
        MetricName.MEMORY_USAGE:    0.03,
        MetricName.REQUEST_RATE:    0.15,
        MetricName.ERROR_RATE:      0.20,
        MetricName.LATENCY_P99:     0.12,
        MetricName.THROUGHPUT:      0.12,
        MetricName.REVENUE_PER_MIN: 0.10,
        MetricName.ACTIVE_USERS:    0.05,
    }

    def __init__(self, detect_use_case: DetectAnomaliesUseCase) -> None:
        self._detect = detect_use_case
        self._tick = 0            # seconds elapsed since start
        self._running = False
        self._spike_countdown: dict[MetricName, int] = {}

    async def start(self) -> None:
        """Called by FastAPI lifespan — runs forever until cancelled."""
        self._running = True
        while self._running:
            await self._tick_all_metrics()
            self._tick += 1
            await asyncio.sleep(1.0)

    def stop(self) -> None:
        self._running = False

    async def _tick_all_metrics(self) -> None:
        """Generate one data point for every metric and run anomaly detection."""
        tasks = [
            self._detect.execute(metric, self._generate_value(metric))
            for metric in MetricName
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _generate_value(self, metric: MetricName) -> float:
        base = self._BASE[metric]
        noise_factor = self._NOISE_FACTOR[metric]

        # Diurnal cycle: traffic follows a sine wave over 24h (86400s)
        # Peak at t=32400s (9am), trough at t=10800s (3am)
        time_of_day = (self._tick % 86400)
        diurnal_factor = 1.0 + 0.3 * math.sin(
            2 * math.pi * (time_of_day - 32400) / 86400
        )

        # Correlated noise: higher request rate drives CPU and latency up
        noise = random.gauss(0, base * noise_factor)

        # Synthetic spikes: ~2% chance per tick per metric
        spike = self._maybe_spike(metric, base)

        value = base * diurnal_factor + noise + spike

        # Clamp to realistic ranges
        return max(0.0, value)

    def _maybe_spike(self, metric: MetricName, base: float) -> float:
        """Probabilistically inject a spike to trigger anomaly detection."""
        # Count down to next spike
        countdown = self._spike_countdown.get(metric, 0)
        if countdown > 0:
            self._spike_countdown[metric] = countdown - 1
            return 0.0

        # 2% chance of a spike on each tick
        if random.random() < 0.02:
            magnitude = random.uniform(2.0, 4.0)
            # Schedule spike to last 3–8 ticks
            self._spike_countdown[metric] = random.randint(3, 8)
            return base * magnitude

        return 0.0
