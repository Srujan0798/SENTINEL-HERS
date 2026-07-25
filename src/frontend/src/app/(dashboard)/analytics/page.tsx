"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type AnalyticsSummary, type AnomalySeriesData } from "@/lib/api";

interface TopError {
  /** API returns service + error_count; older shape used message/count */
  service: string;
  error_count?: number;
  message?: string;
  count?: number;
}

interface AlertTrend {
  total_alerts: number;
  resolved_alerts: number;
  open_alerts: number;
  resolution_rate?: number;
  by_severity?: Record<string, number>;
  period_days?: number;
}

const riskColor: Record<string, string> = {
  low: "bg-[color:var(--ok)]/15 text-[color:var(--ok)] border-[color:var(--ok)]/40",
  medium: "bg-[color:var(--warn)]/15 text-[color:var(--warn)] border-[color:var(--warn)]/40",
  high: "bg-[color:var(--sev1)]/15 text-[color:var(--sev1)] border-[color:var(--sev1)]/40",
};

const SEV_BAR: Record<string, string> = {
  SEV1: "bg-[color:var(--sev1)]",
  SEV2: "bg-[color:var(--warn)]",
  SEV3: "bg-[color:var(--phosphor)]",
  SEV4: "bg-[color:var(--ice)]",
};

/** Race a promise against a timeout so one slow API never freezes the page. */
function withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const t = window.setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms);
    p.then(
      (v) => {
        window.clearTimeout(t);
        resolve(v);
      },
      (e) => {
        window.clearTimeout(t);
        reject(e);
      }
    );
  });
}

function asArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object" && Array.isArray((value as { data?: unknown }).data)) {
    return (value as { data: T[] }).data;
  }
  return [];
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [topErrors, setTopErrors] = useState<TopError[]>([]);
  const [trend, setTrend] = useState<AlertTrend | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalySeriesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoadError(null);
      try {
        const [s, e, t, a] = await Promise.allSettled([
          withTimeout(api.get<AnalyticsSummary>("/api/analytics/incidents/summary"), 12000, "summary"),
          withTimeout(api.get<TopError[] | { data: TopError[] }>("/api/analytics/logs/top-errors"), 12000, "top-errors"),
          withTimeout(api.get<AlertTrend>("/api/analytics/alerts/trend"), 12000, "alert-trend"),
          withTimeout(api.get<AnomalySeriesData>("/api/analytics/anomalies"), 12000, "anomalies"),
        ]);
        if (cancelled) return;
        if (s.status === "fulfilled") setSummary(s.value);
        if (e.status === "fulfilled") setTopErrors(asArray<TopError>(e.value));
        if (t.status === "fulfilled") setTrend(t.value);
        if (a.status === "fulfilled") setAnomaly(a.value);
        const failed = [s, e, t, a].filter((r) => r.status === "rejected").length;
        if (failed === 4) {
          setLoadError("Analytics APIs unreachable. Retry or check API URL / CORS.");
        } else if (failed > 0) {
          setLoadError(`${failed} of 4 analytics panels timed out or failed — partial data shown.`);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-[color:var(--ink-muted)] font-data text-sm">
        Loading analytics…
      </div>
    );
  }

  const series = anomaly?.series ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Incident trends, error patterns, and reliability metrics</p>
        {loadError && (
          <p className="mt-2 text-xs font-data text-[color:var(--warn)]" role="status">
            {loadError}
          </p>
        )}
      </div>

      {/* MTTR + Resolution */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-data">{summary?.total_incidents ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">MTTR (min)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-data text-[color:var(--ice)]">
              {summary?.mttr_minutes != null ? Math.round(summary.mttr_minutes) : "—"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Alert Resolution %</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-data text-[color:var(--ok)]">
              {trend
                ? `${Math.round(
                    (trend.resolution_rate != null
                      ? trend.resolution_rate
                      : trend.total_alerts > 0
                      ? trend.resolved_alerts / trend.total_alerts
                      : 0) * 100
                  )}%`
                : "—"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Open Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-data text-[color:var(--phosphor)]">
              {trend?.open_alerts ?? 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {summary?.by_severity && (
          <Card>
            <CardHeader>
              <CardTitle>Incidents by Severity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(summary.by_severity).map(([sev, count]) => {
                  const total = summary.total_incidents || 1;
                  const pct = Math.round((count / total) * 100);
                  const color = SEV_BAR[sev] || "bg-[color:var(--ink-muted)]";
                  return (
                    <div key={sev}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium font-data">{sev}</span>
                        <span className="text-muted-foreground font-data">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2 bg-[color:var(--panel-elevated)] rounded">
                        <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Top Error Services</CardTitle>
          </CardHeader>
          <CardContent>
            {topErrors.length === 0 ? (
              <p className="text-muted-foreground text-sm">No error logs yet.</p>
            ) : (
              <div className="space-y-3">
                {topErrors.slice(0, 8).map((e, i) => {
                  const count = e.error_count ?? e.count ?? 0;
                  const label = e.message || e.service || "unknown";
                  return (
                    <div key={i} className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm truncate font-data">{label}</p>
                        {e.message && e.service && (
                          <p className="text-xs text-muted-foreground">{e.service}</p>
                        )}
                      </div>
                      <span className="text-sm font-bold text-[color:var(--sev1)] shrink-0 font-data">
                        {count}×
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <CardTitle>Predictive Anomaly Risk</CardTitle>
            {anomaly && (
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold border font-data ${
                  riskColor[anomaly.risk_level] || riskColor.low
                }`}
              >
                {(anomaly.risk_level || "low").toUpperCase()} RISK
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!anomaly || series.length === 0 ? (
            <p className="text-muted-foreground text-sm">No anomaly data yet.</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {series.map((entry) => (
                  <div
                    key={entry.service}
                    className={`rounded border px-3 py-2 ${
                      entry.is_anomaly
                        ? "border-[color:var(--sev1)]/40 bg-[color:var(--sev1)]/10"
                        : "border-[color:var(--ok)]/30 bg-[color:var(--ok)]/5"
                    }`}
                  >
                    <p className="text-xs text-muted-foreground truncate font-data">{entry.service}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-2 bg-[color:var(--panel-elevated)] rounded">
                        <div
                          className={`h-2 rounded ${entry.is_anomaly ? "bg-[color:var(--sev1)]" : "bg-[color:var(--ok)]"}`}
                          style={{ width: `${Math.min(Math.abs(entry.score) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs font-data font-bold shrink-0">
                        {entry.score.toFixed(3)}
                      </span>
                    </div>
                    <p className="text-xs mt-1">
                      {entry.is_anomaly ? (
                        <span className="text-[color:var(--sev1)] font-semibold">ANOMALOUS</span>
                      ) : (
                        <span className="text-[color:var(--ok)] font-semibold">normal</span>
                      )}
                      <span className="text-muted-foreground ml-2 font-data">
                        threshold={Number(entry.threshold).toFixed(3)}
                      </span>
                    </p>
                  </div>
                ))}
              </div>
              <div className="text-sm text-muted-foreground">
                Anomaly-generated alerts:{" "}
                <span className="font-bold font-data">{anomaly.anomaly_alerts_count ?? 0}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {summary?.by_status && (
        <Card>
          <CardHeader>
            <CardTitle>Incidents by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {Object.entries(summary.by_status).map(([status, count]) => (
                <div
                  key={status}
                  className="text-center px-4 py-3 rounded border border-[color:var(--line)] bg-[color:var(--panel-elevated)]/40"
                >
                  <div className="text-2xl font-bold font-data">{count}</div>
                  <div className="text-xs text-muted-foreground mt-1 capitalize">{status}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
