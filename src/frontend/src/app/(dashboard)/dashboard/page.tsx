"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useUser, useRole } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, AnalyticsSummary, Incident, type SlaStatus } from "@/lib/api";
import { useRealtimeEvents } from "@/lib/realtime";
import { Inbox, AlertTriangle, ArrowRight } from "lucide-react";

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
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadDashboard = useCallback(() => {
    setLoadError(null);
    setLoading(true);
    Promise.allSettled([
      api.get<AnalyticsSummary>("/api/analytics/incidents/summary"),
      api.get<{ data: Incident[] }>("/api/incidents"),
      api.get<SlaStatus[]>("/api/sla"),
    ]).then(([s, i, sla]) => {
      let fails = 0;
      if (s.status === "fulfilled") setSummary(s.value);
      else { setSummary(null); fails += 1; }
      if (i.status === "fulfilled") setIncidents(i.value?.data || []);
      else { setIncidents([]); fails += 1; }
      if (sla.status === "fulfilled") setSlaRows(Array.isArray(sla.value) ? sla.value : []);
      else { setSlaRows([]); fails += 1; }
      if (fails === 3) {
        setLoadError("Dashboard APIs unreachable. Check network, login, or API URL — not an empty healthy system.");
      } else if (fails > 0) {
        setLoadError(`${fails} of 3 dashboard panels failed — partial data shown.`);
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  useRealtimeEvents(
    ["incident.create", "incident.update", "incident.assign", "incident.escalate", "task.create", "task.update"],
    () => { loadDashboard(); }
  );

  const totalIncidents = summary?.total_incidents ?? 0;
  const sev1Active =
    incidents.filter((i) => i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed").length ||
    summary?.by_severity?.SEV1 || 0;
  const mttr = summary?.mttr_minutes ?? 0;
  const openSla = slaRows.length;
  const breached = slaRows.filter((s) => s.breached).length;
  const slaCompliance =
    openSla > 0 ? Math.round(((openSla - breached) / openSla) * 100) : summary && summary.total_incidents > 0
      ? Math.round((summary.resolved_incidents / summary.total_incidents) * 100) : 0;
  const openSev1 = incidents.find(
    (i) => i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed"
  );

  if (loading) {
    return (
      <div className="space-y-6 p-4 sm:p-0">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}><CardContent className="p-6"><Skeleton className="h-20 w-full" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="p-6"><Skeleton className="h-48 w-full" /></CardContent></Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 sm:p-0">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user?.name}. You are signed in as <strong>{role}</strong>.
          </p>
          {loadError && (
            <p className="mt-2 text-xs text-warning" role="alert">
              {loadError}{" "}
              <button type="button" className="underline text-primary" onClick={() => loadDashboard()}>
                Retry
              </button>
            </p>
          )}
        </div>
        {openSev1 && (
          <Button asChild variant="destructive" size="sm">
            <Link href="/incidents">Open SEV1 war room <ArrowRight className="ml-1 h-4 w-4" /></Link>
          </Button>
        )}
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
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

        <Card className={sev1Active > 0 ? "ring-2 ring-destructive" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SEV1 Active</CardTitle>
            <Badge variant={sev1Active > 0 ? "destructive" : "secondary"}>
              {sev1Active > 0 ? "Critical" : "None"}
            </Badge>
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
              {openSla > 0 ? `${openSla - breached}/${openSla} open within SLA` : "No open SLA timers"}
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
          {incidents.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <Inbox className="h-12 w-12 text-muted-foreground" />
              <h3 className="font-semibold text-lg">No incidents yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Your team hasn&apos;t had any incidents. Try creating one or wait for a webhook integration.
              </p>
              <Button asChild variant="outline" size="sm">
                <Link href="/incidents">Go to War Room</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {incidents.slice(0, 5).map((inc) => {
                const sla = slaRows.find((s) => s.incident_id === inc.id);
                const isOpenSev1 = inc.severity === "SEV1" && inc.status !== "resolved" && inc.status !== "closed";
                return (
                  <Link
                    key={inc.id}
                    href={`/incidents?id=${inc.id}`}
                    className={`flex items-center justify-between p-4 border rounded-lg hover:ring-2 hover:ring-primary transition-all ${
                      isOpenSev1 ? "border-destructive/50 bg-destructive/5" : ""
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {isOpenSev1 && <AlertTriangle className="h-4 w-4 shrink-0 text-destructive" />}
                        <p className="font-medium truncate">{inc.title}</p>
                      </div>
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
                    <Badge variant={severityVariant[inc.severity] ?? "secondary"} className="shrink-0 ml-2">
                      {inc.severity}
                    </Badge>
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
