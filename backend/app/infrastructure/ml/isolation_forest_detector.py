"""
LAYER 3 — INFRASTRUCTURE — app/infrastructure/ml/isolation_forest_detector.py
────────────────────────────────────────────────────────────────────────────────
LESSON: THIS is where the ML library (scikit-learn) lives.
It implements the IAnomalyDetector Protocol defined in the domain service.

WHY Isolation Forest for anomaly detection?
  - Unsupervised: no labelled training data needed (perfect for ops metrics)
  - Fast: O(n log n) training, O(log n) prediction
  - Works well on univariate time-series with sudden spikes/drops
  - Explainable: you can describe it in an interview in 2 sentences:
    "It builds random trees that isolate points. Anomalies are isolated
     in fewer splits because they're statistically different from normal."

interview q: "Why not Z-score?"
answer: "Z-score assumes normally distributed data. Request rates at 3am
         vs midday are NOT normal — Isolation Forest handles multimodal
         distributions naturally."
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest  # type: ignore

from app.domain.entities.metric import MetricSeries


class IsolationForestDetector:
    """
    Concrete implementation of IAnomalyDetector (satisfies the Protocol
    via structural subtyping — no explicit inheritance needed).
    """

    # Contamination = expected fraction of anomalies in training data.
    # 0.05 = we expect ~5% of readings to be anomalous.
    CONTAMINATION = 0.05
    # Minimum points needed before the model can make reliable predictions
    MIN_POINTS = 20

    def __init__(self) -> None:
        # One model instance per detector — retrained on each series window
        self._model = IsolationForest(
            contamination=self.CONTAMINATION,
            random_state=42,      # reproducible results
            n_estimators=100,     # number of trees
        )

    def detect(self, series: MetricSeries) -> tuple[bool, float, tuple[float, float]]:
        """
        Analyse the series and return (is_anomaly, confidence, expected_range).

        Returns (False, 0.0, (0,0)) if not enough data to make a call —
        this is safer than a false positive on startup.
        """
        if len(series.points) < self.MIN_POINTS:
            return False, 0.0, (0.0, 0.0)

        values = np.array([p.value for p in series.points]).reshape(-1, 1)
        latest_value = values[-1][0]

        # Fit on the full window, predict on the latest point only
        self._model.fit(values)
        score = self._model.decision_function(values[-1::])[0]
        prediction = self._model.predict(values[-1::])[0]  # -1 = anomaly, 1 = normal

        is_anomaly = prediction == -1

        # Convert raw score to 0–1 confidence.
        # decision_function returns negative scores for anomalies;
        # the more negative, the more anomalous.
        confidence = float(np.clip(1.0 - (score + 0.5), 0.0, 1.0))

        # Expected range = mean ± 2 standard deviations of the window
        mean = float(np.mean(values))
        std = float(np.std(values))
        expected_range = (
            max(0.0, mean - 2 * std),
            mean + 2 * std,
        )

        return is_anomaly, confidence, expected_range
