/*
  PRESENTATION — src/app/dashboard/page.tsx
  Next.js App Router page — the main dashboard.
  Renders at route: /dashboard
*/
"use client";

import { useEffect } from "react";
import { useDashboardStore } from "@/application/use-cases/dashboard-store";
import { MetricsRepository, AnomalyRepository, AlertRepository } from "@/infrastructure/api/metrics-repository";
import { useMetricsStream } from "@/infrastructure/websocket/useMetricsStream";
import { ConnectionStatus } from "@/presentation/components/ui/ConnectionStatus";
import { Card, CardHeader, CardTitle } from "@/presentation/components/ui/Card";
import { SeverityBadge } from "@/presentation/components/ui/Badge";
import { Spinner } from "@/presentation/components/ui/Spinner";
import { cn } from "@/lib/utils";
import type { MetricName } from "@/domain/entities/metric";

const METRIC_ICONS: Record<MetricName, string> = {
  cpu_usage:       "⚡",
  memory_usage:    "💾",
  request_rate:    "📡",
  error_rate:      "⚠️",
  latency_p99:     "⏱️",
  throughput:      "🚀",
  revenue_per_min: "💰",
  active_users:    "👥",
};

function formatValue(metric: MetricName, value: number): string {
  switch (metric) {
    case "cpu_usage": case "memory_usage": case "error_rate":
      return `${value.toFixed(1)}%`;
    case "latency_p99":
      return `${value.toFixed(0)} ms`;
    case "revenue_per_min":
      return `$${value.toFixed(2)}`;
    case "active_users":
      return value.toLocaleString();
    default:
      return `${value.toFixed(1)}/s`;
  }
}

export default function DashboardPage() {
  const { metrics, anomalies, alerts, connectionStatus, lastUpdated, setMetrics, addAnomaly, addAlert } =
    useDashboardStore();

  // Connect WebSocket stream for live updates
  useMetricsStream();

  // Load initial data
  useEffect(() => {
    MetricsRepository.getAllMetrics().then(setMetrics).catch(console.error);
    AnomalyRepository.getAnomalies(20).then((list) => list.forEach(addAnomaly)).catch(console.error);
    AlertRepository.getAlerts().then((list) => list.forEach(addAlert)).catch(console.error);
  }, []);

  const metricList = Object.values(metrics);
  const activeAlerts = alerts.filter((a) => a.status === "active");
  const recentAnomalies = anomalies.slice(0, 5);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">PulseBoard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI-powered real-time operations intelligence
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-xs text-muted-foreground">
              Last updated: {new Date(lastUpdated).toLocaleTimeString()}
            </span>
          )}
          <ConnectionStatus status={connectionStatus} />
        </div>
      </div>

      {/* ── Alert Banner ────────────────────────────────────────────────── */}
      {activeAlerts.length > 0 && (
        <div className="mb-6 p-4 rounded-lg border border-red-500/30 bg-red-500/5">
          <p className="text-sm font-medium text-red-400">
            🚨 {activeAlerts.length} active alert{activeAlerts.length > 1 ? "s" : ""} —{" "}
            {activeAlerts[0].title}
          </p>
        </div>
      )}

      {/* ── Metrics Grid ────────────────────────────────────────────────── */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
          Live Metrics
        </h2>
        {metricList.length === 0 ? (
          <div className="flex items-center gap-3 text-muted-foreground p-8">
            <Spinner />
            <span>Waiting for backend data…</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {metricList.map((series) => {
              const isUp = series.change_pct > 0;
              const isDown = series.change_pct < 0;
              return (
                <Card key={series.metric} className="hover:border-border transition-colors">
                  <CardHeader>
                    <CardTitle>{METRIC_ICONS[series.metric as MetricName]} {series.label}</CardTitle>
                    <span
                      className={cn(
                        "text-xs font-mono",
                        isUp ? "text-green-400" : isDown ? "text-red-400" : "text-muted-foreground"
                      )}
                    >
                      {isUp ? "▲" : isDown ? "▼" : "●"} {Math.abs(series.change_pct).toFixed(1)}%
                    </span>
                  </CardHeader>
                  <p className="text-2xl font-bold font-mono tabular-nums text-foreground">
                    {formatValue(series.metric as MetricName, series.current)}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{series.unit}</p>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Bottom panels ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Anomalies */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Anomalies</CardTitle>
            <span className="text-xs text-muted-foreground">{anomalies.length} total</span>
          </CardHeader>
          {recentAnomalies.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4">No anomalies detected yet.</p>
          ) : (
            <ul className="space-y-3 mt-2">
              {recentAnomalies.map((a) => (
                <li key={a.id} className="flex items-start gap-3">
                  <SeverityBadge severity={a.severity} />
                  <div className="min-w-0">
                    <p className="text-sm text-foreground truncate">{a.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(a.detected_at).toLocaleTimeString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Active Alerts</CardTitle>
            <span className="text-xs text-muted-foreground">{activeAlerts.length} active</span>
          </CardHeader>
          {activeAlerts.length === 0 ? (
            <p className="text-sm text-green-400 py-4">✅ All systems operational</p>
          ) : (
            <ul className="space-y-3 mt-2">
              {activeAlerts.slice(0, 5).map((a) => (
                <li key={a.id} className="flex items-start gap-3">
                  <SeverityBadge severity={a.severity} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">{a.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{a.message}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
