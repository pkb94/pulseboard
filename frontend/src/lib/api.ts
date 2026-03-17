import axios from "axios";
import type { Alert, Anomaly, AuthToken, MetricSeries, SystemHealth, User } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
apiClient.interceptors.request.use((config) => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("pb_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralised error handling
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("pb_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthToken> {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await apiClient.post<AuthToken>("/api/auth/token", form.toString(), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/api/auth/me");
  return data;
}

// ─── Metrics ──────────────────────────────────────────────────────────────────

export async function getMetricHistory(
  metric: string,
  windowMinutes = 60
): Promise<MetricSeries> {
  const { data } = await apiClient.get<MetricSeries>(
    `/api/metrics/${metric}?window_minutes=${windowMinutes}`
  );
  return data;
}

export async function getAllMetrics(): Promise<MetricSeries[]> {
  const { data } = await apiClient.get<MetricSeries[]>("/api/metrics");
  return data;
}

// ─── Anomalies ────────────────────────────────────────────────────────────────

export async function getAnomalies(limit = 50): Promise<Anomaly[]> {
  const { data } = await apiClient.get<Anomaly[]>(`/api/anomalies?limit=${limit}`);
  return data;
}

export async function acknowledgeAnomaly(id: string): Promise<void> {
  await apiClient.patch(`/api/anomalies/${id}/acknowledge`);
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export async function getAlerts(status?: string): Promise<Alert[]> {
  const params = status ? `?status=${status}` : "";
  const { data } = await apiClient.get<Alert[]>(`/api/alerts${params}`);
  return data;
}

export async function resolveAlert(id: string): Promise<void> {
  await apiClient.patch(`/api/alerts/${id}/resolve`);
}

// ─── System Health ────────────────────────────────────────────────────────────

export async function getSystemHealth(): Promise<SystemHealth> {
  const { data } = await apiClient.get<SystemHealth>("/api/health/system");
  return data;
}
