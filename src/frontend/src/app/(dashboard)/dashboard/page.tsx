"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useUser, useRole } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, AnalyticsSummary, Incident, type SlaStatus } from "@/lib/api";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatMTTR(minutes: number): string {
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }
  return `${Math.round(minutes)}m`;
}

const severityVariant: Record<string, "destructive" | "warning" | "info" | "secondary"> = {
  SEV1: "destructive",
  SEV2: "warning",
  SEV3: "info",
  SEV4: "secondary",
};

export default function DashboardPage() {
  const user = useUser();
  const role = useRole();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [slaRows, setSlaRows] = useState<SlaStatus[]>([]);

  useEffect(() => {
    api.get<AnalyticsSummary>("/api/analytics/incidents/summary").then(setSummary);
    api.get<{ data: Incident[] }>("/api/incidents").then((res) => setIncidents(res.data));
    api.get<SlaStatus[]>("/api/sla").then((rows) => setSlaRows(Array.isArray(rows) ? rows : [])).catch(() => setSlaRows([]));
  }, []);

  const totalIncidents = summary?.total_incidents ?? 0;
  const sev1Active =
    incidents.filter((i) => i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed")
      .length ||
    summary?.by_severity?.SEV1 ||
    0;
  const mttr = summary?.mttr_minutes ?? 0;
  const openSla = slaRows.length;
  const breached = slaRows.filter((s) => s.breached).length;
  // Honest SLA face: among open incidents tracked by /api/sla, % not breached.
  const slaCompliance =
    openSla > 0 ? Math.round(((openSla - breached) / openSla) * 100) : summary && summary.total_incidents > 0
      ? Math.round((summary.resolved_incidents / summary.total_incidents) * 100)
      : 0;
  const openSev1 = incidents.find(
    (i) => i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed"
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user?.name}. You are signed in as <strong>{role}</strong>.
          </p>
        </div>
        {openSev1 && (
          <Button asChild variant="destructive" size="sm">
            <Link href="/incidents">Open SEV1 war room →</Link>
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Incidents</CardTitle>
            <Badge variant="secondary">SEV1-4</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalIncidents}</div>
            <p className="text-xs text-muted-foreground">Last 7 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SEV1 Active</CardTitle>
            <Badge variant="destructive">Critical</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{sev1Active}</div>
            <p className="text-xs text-muted-foreground">Requires immediate attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MTTR</CardTitle>
            <Badge variant="info">Avg</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatMTTR(mttr)}</div>
            <p className="text-xs text-muted-foreground">Mean time to resolve</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open SLA</CardTitle>
            <Badge variant={breached > 0 ? "destructive" : "success"}>
              {breached > 0 ? `${breached} breached` : "On Track"}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{slaCompliance}%</div>
            <p className="text-xs text-muted-foreground">
              {openSla > 0
                ? `${openSla - breached}/${openSla} open within SLA`
                : "No open SLA timers"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Incidents</CardTitle>
          <Button asChild variant="ghost" size="sm">
            <Link href="/incidents">View all</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {incidents.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No recent incidents.</p>
            ) : (
              incidents.slice(0, 5).map((inc) => {
                const sla = slaRows.find((s) => s.incident_id === inc.id);
                return (
                  <Link
                    key={inc.id}
                    href="/incidents"
                    className="flex items-center justify-between p-4 border rounded-lg hover:ring-2 hover:ring-primary transition-all"
                  >
                    <div className="min-w-0">
                      <p className="font-medium truncate">{inc.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {inc.status}
                        {" · "}
                        {inc.assigned_to ? "assigned" : "unassigned"}
                        {" · "}
                        {timeAgo(inc.detected_at || inc.created_at)}
                        {sla
                          ? ` · SLA ${sla.breached ? "BREACHED" : `${Math.round(sla.remaining_minutes)}m left`}`
                          : ""}
                      </p>
                    </div>
                    <Badge variant={severityVariant[inc.severity] ?? "secondary"}>
                      {inc.severity}
                    </Badge>
                  </Link>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
