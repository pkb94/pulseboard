/*
  INFRASTRUCTURE — API REPOSITORY — src/infrastructure/api/metrics-repository.ts
  ─────────────────────────────────────────────────────────────────────────────────
  LESSON: The repository pattern on the frontend mirrors the backend.
  Components never call fetch/axios directly — they go through this layer.
  
  Benefits:
  - Easy to mock in tests (swap the real repo for a fake)
  - One place to handle auth headers, base URLs, error transformation
  - API response shapes are converted to domain entities here
*/

import axios from "axios";
import type { Alert, Anomaly, MetricSeries } from "@/domain/entities/metric";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const http = axios.create({
  baseURL: API_URL,
  timeout: 10_000,
});

export const MetricsRepository = {
  async getAllMetrics(): Promise<MetricSeries[]> {
    const { data } = await http.get<{ metrics: MetricSeries[] }>("/api/metrics");
    return data.metrics;
  },

  async getMetric(metric: string, windowMinutes = 60): Promise<MetricSeries> {
    const { data } = await http.get<MetricSeries>(
      `/api/metrics/${metric}?window_minutes=${windowMinutes}`
    );
    return data;
  },
};

export const AnomalyRepository = {
  async getAnomalies(limit = 50): Promise<Anomaly[]> {
    const { data } = await http.get<Anomaly[]>(`/api/anomalies?limit=${limit}`);
    return data;
  },

  async acknowledgeAnomaly(id: string): Promise<void> {
    await http.patch(`/api/anomalies/${id}/acknowledge`);
  },
};

export const AlertRepository = {
  async getAlerts(status?: string): Promise<Alert[]> {
    const params = status ? `?alert_status=${status}` : "";
    const { data } = await http.get<Alert[]>(`/api/alerts${params}`);
    return data;
  },

  async resolveAlert(id: string): Promise<void> {
    await http.patch(`/api/alerts/${id}/resolve`);
  },
};
