/*
  PRESENTATION — src/presentation/components/ui/ConnectionStatus.tsx
  Shows a live/disconnected dot in the top bar.
*/
"use client";
import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "@/domain/entities/metric";

const label: Record<ConnectionStatus, string> = {
  connecting:   "Connecting…",
  connected:    "Live",
  disconnected: "Reconnecting…",
  error:        "Connection error",
};

const dotColor: Record<ConnectionStatus, string> = {
  connecting:   "bg-yellow-400 animate-pulse",
  connected:    "bg-green-400 animate-pulse-slow",
  disconnected: "bg-orange-400 animate-pulse",
  error:        "bg-red-500",
};

interface Props { status: ConnectionStatus }

export function ConnectionStatus({ status }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className={cn("w-2 h-2 rounded-full", dotColor[status])} />
      {label[status]}
    </div>
  );
}
