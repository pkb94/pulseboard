/*
  APPLICATION — ZUSTAND STORE — src/application/use-cases/dashboard-store.ts
  ────────────────────────────────────────────────────────────────────────────
  LESSON: Zustand is the application state manager (like Redux but minimal).
  
  In Clean Architecture terms this is the APPLICATION layer of the frontend:
  - It holds the current state (metrics, anomalies, alerts)
  - It exposes actions (use cases): updateMetric, addAnomaly, resolveAlert
  - Components READ from the store; they don't manage state themselves

  WHY Zustand over Redux?
    - No boilerplate (no actions/reducers/selectors files)
    - Hooks-based — feels natural in React
    - Immer-style mutations via the set callback
    - Tiny bundle (under 1kb minzipped)
  
  Interview answer: "I used Zustand as my application state layer because it
  cleanly separates state logic from UI components, making each independently
  testable — consistent with Clean Architecture."
*/

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  Alert,
  AlertStatus,
  Anomaly,
  ConnectionStatus,
  MetricName,
  MetricPoint,
  MetricSeries,
} from "@/domain/entities/metric";

interface DashboardState {
  // ── State ──────────────────────────────────────────────────────────────────
  metrics: Record<MetricName, MetricSeries>;
  anomalies: Anomaly[];
  alerts: Alert[];
  connectionStatus: ConnectionStatus;
  lastUpdated: string | null;

  // ── Actions (Use Cases) ────────────────────────────────────────────────────
  setMetrics: (metrics: MetricSeries[]) => void;
  updateMetricPoint: (metric: MetricName, point: MetricPoint) => void;
  addAnomaly: (anomaly: Anomaly) => void;
  acknowledgeAnomaly: (id: string) => void;
  addAlert: (alert: Alert) => void;
  updateAlertStatus: (id: string, status: AlertStatus) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

const EMPTY_METRICS = {} as Record<MetricName, MetricSeries>;

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      // Initial state
      metrics: EMPTY_METRICS,
      anomalies: [],
      alerts: [],
      connectionStatus: "connecting",
      lastUpdated: null,

      // Load the full snapshot on initial mount
      setMetrics: (metricsList) =>
        set(
          (state) => ({
            metrics: metricsList.reduce(
              (acc, series) => ({ ...acc, [series.metric]: series }),
              state.metrics
            ),
            lastUpdated: new Date().toISOString(),
          }),
          false,
          "setMetrics"
        ),

      // Append a single new point (from WebSocket stream)
      updateMetricPoint: (metric, point) =>
        set(
          (state) => {
            const existing = state.metrics[metric];
            if (!existing) return state;
            const data = [...existing.data, point].slice(-120); // keep last 2 min
            return {
              metrics: {
                ...state.metrics,
                [metric]: {
                  ...existing,
                  current: point.value,
                  data,
                },
              },
              lastUpdated: point.timestamp,
            };
          },
          false,
          "updateMetricPoint"
        ),

      addAnomaly: (anomaly) =>
        set(
          (state) => ({
            anomalies: [anomaly, ...state.anomalies].slice(0, 100),
          }),
          false,
          "addAnomaly"
        ),

      acknowledgeAnomaly: (id) =>
        set(
          (state) => ({
            anomalies: state.anomalies.map((a) =>
              a.id === id ? { ...a, acknowledged: true } : a
            ),
          }),
          false,
          "acknowledgeAnomaly"
        ),

      addAlert: (alert) =>
        set(
          (state) => ({
            alerts: [alert, ...state.alerts].slice(0, 50),
          }),
          false,
          "addAlert"
        ),

      updateAlertStatus: (id, status) =>
        set(
          (state) => ({
            alerts: state.alerts.map((a) =>
              a.id === id ? { ...a, status } : a
            ),
          }),
          false,
          "updateAlertStatus"
        ),

      setConnectionStatus: (connectionStatus) =>
        set({ connectionStatus }, false, "setConnectionStatus"),
    }),
    { name: "PulseBoard" }
  )
);
