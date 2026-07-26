"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export function WakingOverlay({ children }: { children: React.ReactNode }) {
  const [showWaking, setShowWaking] = useState(false);
  const [wakingText, setWakingText] = useState("Waking API…");
  const [manualDismiss, setManualDismiss] = useState(false);
  const [showDismiss, setShowDismiss] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const slowTimer = setTimeout(() => {
      if (!cancelled) setShowWaking(true);
    }, 2000);
    const textTimer = setTimeout(() => {
      if (!cancelled) setWakingText("Still waking… cold start can take 30s+");
    }, 10000);
    const dismissTimer = setTimeout(() => {
      if (!cancelled) setShowDismiss(true);
    }, 8000);
    (async function ping() {
      for (let i = 0; i < 30; i++) {
        if (cancelled) return;
        try {
          const res = await fetch(`${API_BASE}/healthz`, { signal: AbortSignal.timeout(5000) });
          if (res.ok && !cancelled) {
            clearTimeout(slowTimer);
            clearTimeout(textTimer);
            clearTimeout(dismissTimer);
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
      clearTimeout(dismissTimer);
    };
  }, []);

  if (manualDismiss) return <>{children}</>;

  return (
    <>
      {showWaking && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="text-sm font-medium text-foreground">{wakingText}</p>
            <p className="text-xs text-muted-foreground">The API spins down after inactivity — first load is slow</p>
            {showDismiss && (
              <button
                onClick={() => setManualDismiss(true)}
                className="mt-2 text-xs text-muted-foreground underline hover:text-foreground"
                aria-label="Dismiss overlay"
              >
                Dismiss &amp; load anyway
              </button>
            )}
          </div>
        </div>
      )}
      {children}
    </>
  );
}
