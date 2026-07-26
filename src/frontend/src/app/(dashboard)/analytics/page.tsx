"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type AnalyticsSummary, type AnomalySeriesData } from "@/lib/api";
import {
  AlertTriangle,
  Clock,
  RefreshCw,
  TrendingDown,
} from "lucide-react";

interface TopError {
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

type PanelId = "summary" | "topErrors" | "trend" | "anomaly";

const SEV_BAR: Record<string, string> = {
  SEV1: "bg-[color:var(--sev1)]",
  SEV2: "bg-[color:var(--warn)]",
  SEV3: "bg-[color:var(--phosphor)]",
  SEV4: "bg-[color:var(--ice)]",
};

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

function PanelError({ label, onRetry }: { label: string; onRetry: () => void }) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-10 gap-3">
        <AlertTriangle className="h-8 w-8 text-[color:var(--warn)]" />
        <p className="text-sm text-muted-foreground text-center">{label} failed to load</p>
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[color:var(--ice)] hover:underline"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      </CardContent>
    </Card>
  );
}

function EmptyState({ icon: Icon, message }: { icon: React.ComponentType<{ className?: string }>; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 gap-3">
      <Icon className="h-8 w-8 text-muted-foreground/40" />
      <p className="text-sm text-muted-foreground text-center">{message}</p>
    </div>
  );
}

function formatMttr(minutes: number): string {
  if (minutes < 1) return "< 1 min";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const hours = minutes / 60;
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h} h`;
  return `${h} h ${m} min`;
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [topErrors, setTopErrors] = useState<TopError[]>([]);
  const [trend, setTrend] = useState<AlertTrend | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalySeriesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [panelErrors, setPanelErrors] = useState<Record<PanelId, boolean>>({
    summary: false,
    topErrors: false,
    trend: false,
    anomaly: false,
  });
  const mountedRef = useRef(true);

  const fetchAll = useCallback(async () => {
    setLoadError(null);
    setLoading(true);
    setPanelErrors({ summary: false, topErrors: false, trend: false, anomaly: false });
    try {
      const [s, e, t, a] = await Promise.allSettled([
        withTimeout(api.get<AnalyticsSummary>("/api/analytics/incidents/summary"), 12000, "summary"),
        withTimeout(api.get<TopError[] | { data: TopError[] }>("/api/analytics/logs/top-errors"), 12000, "top-errors"),
        withTimeout(api.get<AlertTrend>("/api/analytics/alerts/trend"), 12000, "alert-trend"),
        withTimeout(api.get<AnomalySeriesData>("/api/analytics/anomalies"), 12000, "anomalies"),
      ]);
      if (!mountedRef.current) return;
      if (s.status === "fulfilled") setSummary(s.value);
      else setPanelErrors((prev) => ({ ...prev, summary: true }));
      if (e.status === "fulfilled") setTopErrors(asArray<TopError>(e.value));
      else setPanelErrors((prev) => ({ ...prev, topErrors: true }));
      if (t.status === "fulfilled") setTrend(t.value);
      else setPanelErrors((prev) => ({ ...prev, trend: true }));
      if (a.status === "fulfilled") setAnomaly(a.value);
      else setPanelErrors((prev) => ({ ...prev, anomaly: true }));
      const failed = [s, e, t, a].filter((r) => r.status === "rejected").length;
      if (failed === 4) {
        setLoadError("Analytics APIs unreachable. Retry or check API URL / CORS.");
      } else if (failed > 0) {
        setLoadError(`${failed} of 4 analytics panels failed — partial data shown.`);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchAll();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchAll]);

  const retryPanel = useCallback(
    async (panel: PanelId) => {
      setPanelErrors((prev) => ({ ...prev, [panel]: false }));
      try {
        switch (panel) {
          case "summary": {
            const s = await withTimeout(
              api.get<AnalyticsSummary>("/api/analytics/incidents/summary"),
              12000,
              "summary",
            );
            setSummary(s);
            break;
          }
          case "topErrors": {
            const e = await withTimeout(
              api.get<TopError[] | { data: TopError[] }>("/api/analytics/logs/top-errors"),
              12000,
              "top-errors",
            );
            setTopErrors(asArray<TopError>(e));
            break;
          }
          case "trend": {
            const t = await withTimeout(
              api.get<AlertTrend>("/api/analytics/alerts/trend"),
              12000,
              "alert-trend",
            );
            setTrend(t);
            break;
          }
          case "anomaly": {
            const a = await withTimeout(
              api.get<AnomalySeriesData>("/api/analytics/anomalies"),
              12000,
              "anomalies",
            );
            setAnomaly(a);
            break;
          }
        }
      } catch {
        setPanelErrors((prev) => ({ ...prev, [panel]: true }));
      }
    },
    [],
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48" />
          <Skeleton className="h-5 w-72 mt-2" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-9 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array.from({ length: 2 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j}>
                      <div className="flex justify-between mb-1">
                        <Skeleton className="h-4 w-16" />
                        <Skeleton className="h-4 w-20" />
                      </div>
                      <Skeleton className="h-2 w-full" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-48" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded border p-3 space-y-2">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-2 w-full" />
                  <Skeleton className="h-3 w-20" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const series = anomaly?.series ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Incident trends, error patterns, and reliability metrics</p>
          {loadError && (
            <p className="mt-2 text-xs font-data text-[color:var(--warn)]" role="status">
              {loadError}
            </p>
          )}
        </div>
        <button
          onClick={fetchAll}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh all
        </button>
      </div>

      {/* KPI Cards — 1 col mobile, 2 col tablet, 4 col desktop */}
      {panelErrors.summary ? (
        <PanelError label="Summary metrics" onRetry={() => retryPanel("summary")} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                MTTR
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-data text-[color:var(--ice)]">
                {summary?.mttr_minutes != null ? formatMttr(summary.mttr_minutes) : "—"}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-muted-foreground">avg resolution time</span>
                {summary?.mttr_minutes != null && (
                  <span className="text-[10px] text-muted-foreground/60 font-data">
                    ({Math.round(summary.mttr_minutes)} min)
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Alert Resolution %</CardTitle>
            </CardHeader>
            <CardContent>
              {panelErrors.trend ? (
                <div className="text-3xl font-bold font-data text-muted-foreground">—</div>
              ) : (
                <>
                  <div className="text-3xl font-bold font-data text-[color:var(--ok)]">
                    {trend
                      ? `${Math.round(
                          (trend.resolution_rate != null
                            ? trend.resolution_rate
                            : trend.total_alerts > 0
                            ? trend.resolved_alerts / trend.total_alerts
                            : 0) * 100,
                        )}%`
                      : "—"}
                  </div>
                  {trend && trend.total_alerts > 0 && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">
                        {trend.resolved_alerts}/{trend.total_alerts} resolved
                      </span>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                Open Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {panelErrors.trend ? (
                <div className="text-3xl font-bold font-data text-muted-foreground">—</div>
              ) : (
                <>
                  <div className="text-3xl font-bold font-data text-[color:var(--phosphor)]">
                    {trend?.open_alerts ?? 0}
                  </div>
                  {trend && trend.open_alerts > 0 && trend.resolved_alerts > 0 && (
                    <div className="flex items-center gap-1 mt-1">
                      <TrendingDown className="h-3 w-3 text-[color:var(--ok)]" />
                      <span className="text-xs text-muted-foreground">
                        {Math.round((trend.resolved_alerts / (trend.open_alerts + trend.resolved_alerts)) * 100)}% resolved
                      </span>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Severity + Top Errors — 1 col mobile, 2 col desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {panelErrors.summary ? (
          <PanelError label="Incidents by severity" onRetry={() => retryPanel("summary")} />
        ) : summary?.by_severity && Object.keys(summary.by_severity).length > 0 ? (
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
                  const badgeVariant =
                    sev === "SEV1"
                      ? "destructive"
                      : sev === "SEV2"
                        ? "warning"
                        : sev === "SEV3"
                          ? "info"
                          : "secondary";
                  return (
                    <div key={sev}>
                      <div className="flex justify-between text-sm mb-1">
                        <Badge variant={badgeVariant as "destructive" | "warning" | "info" | "secondary"}>{sev}</Badge>
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
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Incidents by Severity</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState icon={AlertTriangle} message="No severity data yet." />
            </CardContent>
          </Card>
        )}

        {panelErrors.topErrors ? (
          <PanelError label="Top error services" onRetry={() => retryPanel("topErrors")} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Top Error Services</CardTitle>
            </CardHeader>
            <CardContent>
              {topErrors.length === 0 ? (
                <EmptyState icon={AlertTriangle} message="No error logs yet." />
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
                          {count}
                          <span className="text-xs text-muted-foreground font-normal">×</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Predictive Anomaly Risk */}
      {panelErrors.anomaly ? (
        <PanelError label="Anomaly risk data" onRetry={() => retryPanel("anomaly")} />
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <CardTitle>Predictive Anomaly Risk</CardTitle>
              {anomaly && (
                <Badge
                  variant={
                    anomaly.risk_level === "high"
                      ? "destructive"
                      : anomaly.risk_level === "medium"
                        ? "warning"
                        : "success"
                  }
                >
                  {anomaly.risk_level.toUpperCase()} RISK
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!anomaly || series.length === 0 ? (
              <EmptyState icon={AlertTriangle} message="No anomaly data yet." />
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
                      <p className="text-xs mt-2 flex items-center gap-1.5">
                        {entry.is_anomaly ? (
                          <Badge variant="destructive" className="text-[10px] px-1.5 py-0">ANOMALOUS</Badge>
                        ) : (
                          <Badge variant="success" className="text-[10px] px-1.5 py-0">normal</Badge>
                        )}
                        <span className="text-muted-foreground font-data">
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
      )}

      {/* Incidents by Status */}
      {panelErrors.summary ? null : summary?.by_status && Object.keys(summary.by_status).length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Incidents by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
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
      ) : null}
    </div>
  );
}
