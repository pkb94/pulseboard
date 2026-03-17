// ─── Metric Types ─────────────────────────────────────────────────────────────

export type MetricName =
  | "cpu_usage"
  | "memory_usage"
  | "request_rate"
  | "error_rate"
  | "latency_p99"
  | "throughput"
  | "revenue_per_min"
  | "active_users";

export interface MetricPoint {
  timestamp: string; // ISO 8601
  value: number;
  metric: MetricName;
}

export interface MetricSeries {
  metric: MetricName;
  unit: string;
  label: string;
  data: MetricPoint[];
  current: number;
  change_pct: number; // % change vs. previous window
  threshold_upper?: number;
  threshold_lower?: number;
}

// ─── Anomaly Types ────────────────────────────────────────────────────────────

export type AnomalySeverity = "low" | "medium" | "high" | "critical";

export interface Anomaly {
  id: string;
  metric: MetricName;
  timestamp: string;
  value: number;
  expected_range: [number, number];
  severity: AnomalySeverity;
  confidence: number; // 0–1
  description: string;
  acknowledged: boolean;
}

// ─── Alert Types ──────────────────────────────────────────────────────────────

export type AlertStatus = "active" | "resolved" | "acknowledged";

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: AnomalySeverity;
  status: AlertStatus;
  metric: MetricName;
  triggered_at: string;
  resolved_at?: string;
}

// ─── WebSocket Message Types ──────────────────────────────────────────────────

export type WSMessageType =
  | "metrics_update"
  | "anomaly_detected"
  | "alert_triggered"
  | "alert_resolved"
  | "heartbeat";

export interface WSMessage<T = unknown> {
  type: WSMessageType;
  payload: T;
  timestamp: string;
  sequence: number;
}

export type MetricsUpdatePayload = Record<MetricName, MetricPoint>;
export type AnomalyPayload = Anomaly;
export type AlertPayload = Alert;

// ─── Dashboard State ──────────────────────────────────────────────────────────

export interface DashboardState {
  metrics: Record<MetricName, MetricSeries>;
  anomalies: Anomaly[];
  alerts: Alert[];
  connectionStatus: "connecting" | "connected" | "disconnected" | "error";
  lastUpdated: string | null;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "viewer" | "analyst";
  avatar_url?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

// ─── System Health ────────────────────────────────────────────────────────────

export type SystemStatus = "operational" | "degraded" | "outage";

export interface SystemHealth {
  status: SystemStatus;
  services: ServiceHealth[];
  uptime_pct: number;
}

export interface ServiceHealth {
  name: string;
  status: SystemStatus;
  latency_ms: number;
}
