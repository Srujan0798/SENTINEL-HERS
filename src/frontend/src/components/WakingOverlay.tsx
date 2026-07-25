"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export function WakingOverlay({ children }: { children: React.ReactNode }) {
  const [showWaking, setShowWaking] = useState(false);
  const [wakingText, setWakingText] = useState("Waking API…");

  useEffect(() => {
    let cancelled = false;
    const slowTimer = setTimeout(() => {
      if (!cancelled) setShowWaking(true);
    }, 3000);
    const textTimer = setTimeout(() => {
      if (!cancelled) setWakingText("Still waking… cold start can take 30s+");
    }, 10000);
    // Ping health until it responds
    (async function ping() {
      for (let i = 0; i < 30; i++) {
        if (cancelled) return;
        try {
          const res = await fetch(`${API_BASE}/healthz`, { signal: AbortSignal.timeout(5000) });
          if (res.ok && !cancelled) {
            clearTimeout(slowTimer);
            clearTimeout(textTimer);
            setShowWaking(false);
            return;
          }
        } catch {
          /* still waking */
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
    })();
    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
      clearTimeout(textTimer);
    };
  }, []);

  return (
    <>
      {showWaking && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="text-sm font-medium text-foreground">{wakingText}</p>
            <p className="text-xs text-muted-foreground">The API spins down after inactivity — first load is slow</p>
          </div>
        </div>
      )}
      {children}
    </>
  );
}
