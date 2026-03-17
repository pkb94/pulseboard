/*
  FRONTEND — DOMAIN ENTITIES (TypeScript mirror of Python domain)
  src/domain/entities/metric.ts
  ───────────────────────────────────────────────────────────────
  LESSON: In Clean Architecture, the frontend has its own domain layer.
  These types are the frontend's "source of truth" for what a metric IS.
  They are NOT coupled to the API response shape — that's what the
  infrastructure/api layer (repository) translates into.
*/

export type MetricName =
  | "cpu_usage"
  | "memory_usage"
  | "request_rate"
  | "error_rate"
  | "latency_p99"
  | "throughput"
  | "revenue_per_min"
  | "active_users";

export type AnomalySeverity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "active" | "acknowledged" | "resolved";
export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";
export type SystemStatus = "operational" | "degraded" | "outage";

export interface MetricPoint {
  metric: MetricName;
  value: number;
  timestamp: string;
}

export interface MetricSeries {
  metric: MetricName;
  label: string;
  unit: string;
  current: number;
  change_pct: number;
  threshold_upper?: number;
  threshold_lower?: number;
  data: MetricPoint[];
}

export interface Anomaly {
  id: string;
  metric: MetricName;
  observed_value: number;
  expected_range: [number, number];
  confidence: number;
  severity: AnomalySeverity;
  description: string;
  detected_at: string;
  acknowledged: boolean;
}

export interface Alert {
  id: string;
  metric: MetricName;
  title: string;
  message: string;
  severity: AnomalySeverity;
  status: AlertStatus;
  anomaly_id: string;
  triggered_at: string;
  resolved_at?: string;
  duration_seconds: number;
}
