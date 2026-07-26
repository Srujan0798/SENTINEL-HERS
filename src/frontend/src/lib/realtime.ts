"use client";

import { useEffect, useRef, useCallback } from "react";
import { getAccessToken } from "./auth";

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
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retriesRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const maxRetries = 10;

  handlerRef.current = handler;

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    retriesRef.current = 0;
  }, []);

  const connect = useCallback(() => {
    if (!enabled) return;
    const token = getAccessToken();
    if (!token) return;

    cleanup();

    const wsBase = process.env.NEXT_PUBLIC_WS_URL;
    const baseUrl = wsBase
      ? `${wsBase.replace(/\/$/, "")}/api/realtime/events`
      : `${API_ORIGIN}/api/realtime/events`;

    const controller = new AbortController();
    abortRef.current = controller;
    let closed = false;

    (async () => {
      try {
        const response = await fetch(baseUrl, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        if (!response.ok || !response.body) {
          throw new Error(`SSE connection failed: ${response.status}`);
        }
        retriesRef.current = 0;
        onOpen?.();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!closed) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          let eventType = "";
          let data = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              data = line.slice(6).trim();
            } else if (line === "" && data) {
              try {
                const parsed = JSON.parse(data) as RealtimeEvent;
                if (eventType) parsed.event_type = eventType;
                handlerRef.current(parsed);
              } catch { /* ignore malformed */ }
              eventType = "";
              data = "";
            }
          }
        }
      } catch {
        if (closed) return;
        onError?.(new Event("sse-error"));
        if (retriesRef.current < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
          retriesRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        } else {
          onDisconnect?.();
        }
      }
    })();

    return () => { closed = true; controller.abort(); };
  }, [enabled, cleanup, onOpen, onError, onDisconnect]);

  useEffect(() => {
    const cancel = connect();
    return () => {
      cancel?.();
      cleanup();
    };
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
