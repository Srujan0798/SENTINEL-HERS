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

    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = typeof window !== "undefined" ? localStorage.getItem("sentinel_token") : null;
    if (!token) return;

    const url = `${base}/api/realtime/sse?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);

    es.onopen = () => setState("connected");
    es.onerror = () => setState("disconnected");
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setLastEvent(data.event_type || "event");
      } catch {
        // ignore malformed events
      }
    };

    return () => {
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
