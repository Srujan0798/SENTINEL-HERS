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
  low: "bg-green-100 text-green-800 border-green-300",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
  high: "bg-red-100 text-red-800 border-red-300",
};

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [topErrors, setTopErrors] = useState<TopError[]>([]);
  const [trend, setTrend] = useState<AlertTrend | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalySeriesData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get<AnalyticsSummary>("/api/analytics/incidents/summary"),
      api.get<TopError[]>("/api/analytics/logs/top-errors"),
      api.get<AlertTrend>("/api/analytics/alerts/trend"),
      api.get<AnomalySeriesData>("/api/analytics/anomalies"),
    ]).then(([s, e, t, a]) => {
      if (s.status === "fulfilled") setSummary(s.value);
      if (e.status === "fulfilled") setTopErrors(e.value);
      if (t.status === "fulfilled") setTrend(t.value);
      if (a.status === "fulfilled") setAnomaly(a.value);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Incident trends, error patterns, and reliability metrics</p>
      </div>

      {/* MTTR + Resolution */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.total_incidents ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">MTTR (min)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {summary?.mttr_minutes != null ? Math.round(summary.mttr_minutes) : "—"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Alert Resolution %</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
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
            <div className="text-3xl font-bold text-orange-600">{trend?.open_alerts ?? 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Breakdown */}
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
                  const color = { SEV1: "bg-red-500", SEV2: "bg-orange-500", SEV3: "bg-yellow-400", SEV4: "bg-blue-400" }[sev] || "bg-gray-400";
                  return (
                    <div key={sev}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium">{sev}</span>
                        <span className="text-muted-foreground">{count} ({pct}%)</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded">
                        <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Errors */}
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
                        <p className="text-sm truncate">{label}</p>
                        {e.message && e.service && (
                          <p className="text-xs text-muted-foreground">{e.service}</p>
                        )}
                      </div>
                      <span className="text-sm font-bold text-red-600 shrink-0">{count}×</span>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Anomaly Trend + Risk Badge */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Predictive Anomaly Risk</CardTitle>
            {anomaly && (
              <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${riskColor[anomaly.risk_level] || riskColor.low}`}>
                {anomaly.risk_level.toUpperCase()} RISK
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!anomaly ? (
            <p className="text-muted-foreground text-sm">No anomaly data yet.</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {anomaly.series.map((entry) => (
                  <div
                    key={entry.service}
                    className={`rounded border px-3 py-2 ${entry.is_anomaly ? "border-red-300 bg-red-50" : "border-green-200 bg-green-50"}`}
                  >
                    <p className="text-xs text-muted-foreground truncate">{entry.service}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-2 bg-gray-200 rounded">
                        <div
                          className={`h-2 rounded ${entry.is_anomaly ? "bg-red-500" : "bg-green-500"}`}
                          style={{ width: `${Math.min(Math.abs(entry.score) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono font-bold shrink-0">
                        {entry.score.toFixed(3)}
                      </span>
                    </div>
                    <p className="text-xs mt-1">
                      {entry.is_anomaly ? (
                        <span className="text-red-600 font-semibold">ANOMALOUS</span>
                      ) : (
                        <span className="text-green-700 font-semibold">normal</span>
                      )}
                      <span className="text-muted-foreground ml-2">
                        threshold={entry.threshold.toFixed(3)}
                      </span>
                    </p>
                  </div>
                ))}
              </div>
              <div className="text-sm text-muted-foreground">
                Anomaly-generated alerts: <span className="font-bold">{anomaly.anomaly_alerts_count}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Status Breakdown */}
      {summary?.by_status && (
        <Card>
          <CardHeader>
            <CardTitle>Incidents by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {Object.entries(summary.by_status).map(([status, count]) => (
                <div key={status} className="text-center px-4 py-3 rounded border">
                  <div className="text-2xl font-bold">{count}</div>
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
