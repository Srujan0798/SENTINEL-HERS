"use client";

import { useEffect, useState } from "react";

type ConnState = "connecting" | "connected" | "disconnected";

interface StatusBarProps {
  teamId?: string;
}

export function StatusBar({ teamId }: StatusBarProps) {
  const [state, setState] = useState<ConnState>("connecting");
  const [lastEvent, setLastEvent] = useState<string | null>(null);

  useEffect(() => {
    if (!teamId) return;

    const base =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token") || localStorage.getItem("sentinel_token")
        : null;
    if (!token) {
      // No session yet — show disconnected rather than spinning forever.
      setState("disconnected");
      return;
    }

    // Backend router: GET /api/realtime/events?token=… (not /sse)
    const url = `${base}/api/realtime/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);

    es.onopen = () => setState("connected");
    es.onerror = () => setState("disconnected");
    // Backend emits named SSE events: event: connected / channel.message / …
    const onNamed = (e: MessageEvent) => {
      setState("connected");
      try {
        const data = JSON.parse(e.data);
        setLastEvent(
          (data && (data.event_type || data.type)) || e.type || "event"
        );
      } catch {
        setLastEvent(e.type || "event");
      }
    };
    es.addEventListener("connected", onNamed as EventListener);
    es.addEventListener("channel.message", onNamed as EventListener);
    es.addEventListener("ping", () => setState("connected"));
    es.onmessage = onNamed;

    return () => {
      es.removeEventListener("connected", onNamed as EventListener);
      es.removeEventListener("channel.message", onNamed as EventListener);
      es.close();
      setState("disconnected");
    };
  }, [teamId]);

  const dot =
    state === "connected"
      ? "bg-green-500"
      : state === "connecting"
      ? "bg-yellow-400 animate-pulse"
      : "bg-red-500";

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className={`w-2 h-2 rounded-full ${dot}`} />
      <span className="capitalize">{state}</span>
      {lastEvent && <span className="opacity-60">· {lastEvent}</span>}
    </div>
  );
}
