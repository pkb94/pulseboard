/*
  PRESENTATION — src/presentation/components/ui/Badge.tsx
  Reusable severity badge used on anomaly/alert cards.
*/

import { cn } from "@/lib/utils";
import type { AnomalySeverity, AlertStatus } from "@/domain/entities/metric";

const severityStyles: Record<AnomalySeverity, string> = {
  low:      "bg-blue-500/10 text-blue-400 border border-blue-500/30",
  medium:   "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30",
  high:     "bg-orange-500/10 text-orange-400 border border-orange-500/30",
  critical: "bg-red-500/10 text-red-400 border border-red-500/30 animate-pulse",
};

const statusStyles: Record<AlertStatus, string> = {
  active:       "bg-red-500/10 text-red-400 border border-red-500/30",
  acknowledged: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30",
  resolved:     "bg-green-500/10 text-green-400 border border-green-500/30",
};

interface SeverityBadgeProps {
  severity: AnomalySeverity;
  className?: string;
}

interface StatusBadgeProps {
  status: AlertStatus;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide", severityStyles[severity], className)}>
      {severity}
    </span>
  );
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide", statusStyles[status], className)}>
      {status}
    </span>
  );
}
