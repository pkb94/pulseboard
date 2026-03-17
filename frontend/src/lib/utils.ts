import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";
import type { AnomalySeverity, MetricName, SystemStatus } from "@/types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatMetricValue(metric: MetricName, value: number): string {
  switch (metric) {
    case "cpu_usage":
    case "memory_usage":
    case "error_rate":
      return `${value.toFixed(1)}%`;
    case "latency_p99":
      return `${value.toFixed(0)}ms`;
    case "throughput":
    case "request_rate":
      return `${value.toFixed(0)}/s`;
    case "revenue_per_min":
      return `$${value.toFixed(2)}`;
    case "active_users":
      return value.toLocaleString();
    default:
      return value.toFixed(2);
  }
}

export function formatTimestamp(iso: string, mode: "short" | "relative" = "short"): string {
  const date = new Date(iso);
  if (mode === "relative") return formatDistanceToNow(date, { addSuffix: true });
  return format(date, "HH:mm:ss");
}

export function getSeverityColor(severity: AnomalySeverity): string {
  const map: Record<AnomalySeverity, string> = {
    low: "text-blue-500",
    medium: "text-yellow-500",
    high: "text-orange-500",
    critical: "text-red-500",
  };
  return map[severity];
}

export function getSeverityBg(severity: AnomalySeverity): string {
  const map: Record<AnomalySeverity, string> = {
    low: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    high: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    critical: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return map[severity];
}

export function getStatusColor(status: SystemStatus): string {
  const map: Record<SystemStatus, string> = {
    operational: "text-green-400",
    degraded: "text-yellow-400",
    outage: "text-red-400",
  };
  return map[status];
}

export function getMetricLabel(metric: MetricName): string {
  const labels: Record<MetricName, string> = {
    cpu_usage: "CPU Usage",
    memory_usage: "Memory Usage",
    request_rate: "Request Rate",
    error_rate: "Error Rate",
    latency_p99: "Latency (P99)",
    throughput: "Throughput",
    revenue_per_min: "Revenue / Min",
    active_users: "Active Users",
  };
  return labels[metric];
}

export function getMetricUnit(metric: MetricName): string {
  const units: Record<MetricName, string> = {
    cpu_usage: "%",
    memory_usage: "%",
    request_rate: "req/s",
    error_rate: "%",
    latency_p99: "ms",
    throughput: "req/s",
    revenue_per_min: "USD",
    active_users: "users",
  };
  return units[metric];
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function getChangeIndicator(changePct: number): { symbol: string; color: string } {
  if (changePct > 0) return { symbol: "▲", color: "text-green-400" };
  if (changePct < 0) return { symbol: "▼", color: "text-red-400" };
  return { symbol: "●", color: "text-muted-foreground" };
}
