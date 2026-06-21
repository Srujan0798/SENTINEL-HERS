"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type AnalyticsSummary } from "@/lib/api";

interface TopError {
  message: string;
  count: number;
  service: string;
}

interface AlertTrend {
  total_alerts: number;
  resolved_alerts: number;
  open_alerts: number;
  resolution_rate: number;
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [topErrors, setTopErrors] = useState<TopError[]>([]);
  const [trend, setTrend] = useState<AlertTrend | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get<AnalyticsSummary>("/api/analytics/incidents/summary"),
      api.get<TopError[]>("/api/analytics/logs/top-errors"),
      api.get<AlertTrend>("/api/analytics/alerts/trend"),
    ]).then(([s, e, t]) => {
      if (s.status === "fulfilled") setSummary(s.value);
      if (e.status === "fulfilled") setTopErrors(e.value);
      if (t.status === "fulfilled") setTrend(t.value);
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
              {trend ? `${Math.round(trend.resolution_rate * 100)}%` : "—"}
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
            <CardTitle>Top Error Messages</CardTitle>
          </CardHeader>
          <CardContent>
            {topErrors.length === 0 ? (
              <p className="text-muted-foreground text-sm">No error logs yet.</p>
            ) : (
              <div className="space-y-3">
                {topErrors.slice(0, 8).map((e, i) => (
                  <div key={i} className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm truncate">{e.message}</p>
                      <p className="text-xs text-muted-foreground">{e.service}</p>
                    </div>
                    <span className="text-sm font-bold text-red-600 shrink-0">{e.count}×</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
