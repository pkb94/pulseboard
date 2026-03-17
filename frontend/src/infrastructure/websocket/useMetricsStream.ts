/*
  INFRASTRUCTURE — WEBSOCKET — src/infrastructure/websocket/useMetricsStream.ts
  ────────────────────────────────────────────────────────────────────────────────
  LESSON: This is the frontend's infrastructure layer — it handles the
  low-level WebSocket connection and translates raw messages into domain
  store actions (use cases).

  Key engineering decisions:
  1. EXPONENTIAL BACKOFF reconnection — don't hammer the server on failure
     (doubles delay each attempt: 1s → 2s → 4s → 8s → max 30s)
  2. Message type dispatch — switch on "type" field, ignore unknown types
  3. Connection status is exposed to the UI so users see "connected/disconnected"
  4. Cleanup on unmount — essential to prevent memory leaks in React

  Interview talking point: "I implemented exponential backoff reconnection
  so the dashboard gracefully recovers from network blips without manual refresh,
  which is critical for an operations tool where uptime visibility is essential."
*/

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useDashboardStore } from "@/application/use-cases/dashboard-store";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const MAX_RETRY_DELAY_MS = 30_000;

export function useMetricsStream(): void {
  const wsRef = useRef<WebSocket | null>(null);
  const retryDelayRef = useRef(1000);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const { addAnomaly, addAlert, setConnectionStatus } = useDashboardStore();

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    setConnectionStatus("connecting");
    const ws = new WebSocket(`${WS_URL}/ws/metrics`);
    wsRef.current = ws;

    ws.onopen = () => {
      retryDelayRef.current = 1000; // Reset backoff on successful connection
      setConnectionStatus("connected");

      // Send a ping every 25s to keep the connection alive through proxies
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 25_000);
      (ws as WebSocket & { _pingInterval?: ReturnType<typeof setInterval> })._pingInterval = pingInterval;
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const msg = JSON.parse(event.data) as { type: string; payload: unknown; alert?: unknown };
        dispatch(msg);
      } catch {
        // Malformed JSON — ignore, don't crash
      }
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      scheduleReconnect();
    };

    ws.onerror = () => {
      setConnectionStatus("error");
      ws.close();
    };
  }, [setConnectionStatus, addAnomaly, addAlert]);

  const dispatch = useCallback(
    (msg: { type: string; payload: unknown; alert?: unknown }) => {
      switch (msg.type) {
        case "anomaly_detected":
          addAnomaly(msg.payload as Parameters<typeof addAnomaly>[0]);
          if (msg.alert) {
            addAlert(msg.alert as Parameters<typeof addAlert>[0]);
          }
          break;
        case "heartbeat":
          // No-op — keeps connection alive
          break;
        default:
          break;
      }
    },
    [addAnomaly, addAlert]
  );

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;
    retryTimeoutRef.current = setTimeout(() => {
      retryDelayRef.current = Math.min(retryDelayRef.current * 2, MAX_RETRY_DELAY_MS);
      connect();
    }, retryDelayRef.current);
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      const ws = wsRef.current;
      if (ws) {
        const interval = (ws as WebSocket & { _pingInterval?: ReturnType<typeof setInterval> })._pingInterval;
        if (interval) clearInterval(interval);
        ws.close();
      }
    };
  }, [connect]);
}
