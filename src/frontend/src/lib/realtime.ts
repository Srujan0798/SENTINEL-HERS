"use client";

import { useEffect, useRef, useCallback } from "react";
import { getAccessToken } from "./auth";

// Origin only (no path). Prefer NEXT_PUBLIC_API_BASE_URL; fall back to legacy names.
const API_ORIGIN = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://localhost:8000"
).replace(/\/api\/v1\/?$/, "");

export interface RealtimeEvent {
  event_type: string;
  payload: Record<string, unknown>;
  team_id: string;
  timestamp: number;
}

type EventHandler = (event: RealtimeEvent) => void;

interface UseRealtimeStreamOptions {
  enabled?: boolean;
  onOpen?: () => void;
  onError?: (error: Event) => void;
  onDisconnect?: () => void;
}

export function useRealtimeStream(
  handler: EventHandler,
  options: UseRealtimeStreamOptions = {}
) {
  const { enabled = true, onOpen, onError, onDisconnect } = options;
  const handlerRef = useRef(handler);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retriesRef = useRef(0);
  const maxRetries = 10;

  handlerRef.current = handler;

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!enabled) return;

    const token = getAccessToken();
    if (!token) return;

    cleanup();

    const wsBase = process.env.NEXT_PUBLIC_WS_URL;
    const url = wsBase
      ? `${wsBase.replace(/\/$/, "")}/api/v1/realtime/events?token=${encodeURIComponent(token)}`
      : `${API_ORIGIN}/api/v1/realtime/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      retriesRef.current = 0;
      onOpen?.();
    };

    es.onerror = (event) => {
      onError?.(event);
      es.close();

      if (retriesRef.current < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
        retriesRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      } else {
        onDisconnect?.();
      }
    };

    // Listen for all event types via the generic 'message' handler
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handlerRef.current(data);
      } catch {
        // Ignore malformed messages
      }
    };
  }, [enabled, cleanup, onOpen, onError, onDisconnect]);

  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);
}

export function useRealtimeEvents(
  eventTypes: string[],
  handler: EventHandler,
  options: UseRealtimeStreamOptions = {}
) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  const wrappedHandler = useCallback(
    (event: RealtimeEvent) => {
      if (eventTypes.length === 0 || eventTypes.includes(event.event_type)) {
        handlerRef.current(event);
      }
    },
    [eventTypes]
  );

  return useRealtimeStream(wrappedHandler, options);
}
