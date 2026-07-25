"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
  api,
  type Incident,
  type IncidentTask,
  type SlaStatus,
  type TimelineEvent,
} from "@/lib/api";
import { useUser } from "@/lib/auth";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { CommsPanel } from "@/components/comms/CommsPanel";
import { VoiceRecorder } from "@/components/voice/VoiceRecorder";

const SEV_COLORS: Record<string, string> = {
  SEV1: "destructive",
  SEV2: "destructive",
  SEV3: "secondary",
  SEV4: "outline",
} as const;

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  open: "destructive",
  detected: "destructive",
  triaging: "destructive",
  investigating: "destructive",
  mitigating: "secondary",
  resolved: "outline",
  closed: "outline",
};

const STATUS_OPTIONS: Incident["status"][] = [
  "detected",
  "triaging",
  "investigating",
  "mitigating",
  "resolved",
  "closed",
];

function formatSla(remaining: number, breached: boolean): string {
  const abs = Math.abs(remaining);
  const h = Math.floor(abs / 60);
  const m = Math.floor(abs % 60);
  const s = Math.floor((abs * 60) % 60);
  const clock =
    h > 0
      ? `${h}h ${m.toString().padStart(2, "0")}m`
      : `${m}m ${s.toString().padStart(2, "0")}s`;
  if (breached || remaining < 0) return `BREACHED ${clock}`;
  return `${clock} left`;
}

export default function IncidentsPage() {
  const user = useUser();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [postmortem, setPostmortem] = useState<string | null>(null);
  const [postmortemLoading, setPostmortemLoading] = useState(false);
  const [postmortemOpen, setPostmortemOpen] = useState(false);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [tasks, setTasks] = useState<IncidentTask[]>([]);
  const [sla, setSla] = useState<SlaStatus | null>(null);
  const [warLoading, setWarLoading] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showVoice, setShowVoice] = useState(false);

  const refreshIncidents = useCallback(async () => {
    const res = await api.get<{ data: Incident[] }>("/api/incidents?per_page=50");
    setIncidents(res.data);
    return res.data;
  }, []);

  const loadWarRoom = useCallback(async (inc: Incident) => {
    setWarLoading(true);
    setActionError(null);
    setTimeline([]);
    setTasks([]);
    setSla(null);
    try {
      const [tl, tk, slaList] = await Promise.all([
        api.get<{ data: TimelineEvent[] }>(`/api/incidents/${inc.id}/timeline`).catch(() => ({ data: [] })),
        api.get<{ data: IncidentTask[] }>(`/api/incidents/${inc.id}/tasks`).catch(() => ({ data: [] })),
        api.get<SlaStatus[]>("/api/sla").catch(() => [] as SlaStatus[]),
      ]);
      setTimeline(tl.data || []);
      setTasks(tk.data || []);
      const match = (Array.isArray(slaList) ? slaList : []).find((s) => s.incident_id === inc.id) || null;
      setSla(match);
    } finally {
      setWarLoading(false);
    }
  }, []);

  const loadSummary = useCallback(
    async (inc: Incident) => {
      setSelected(inc);
      setAiSummary(null);
      setAiLoading(true);
      void loadWarRoom(inc);
      try {
        const res = await api.get<{ summary: string }>(`/api/ai/incidents/${inc.id}/summary`);
        setAiSummary(res.summary);
      } catch {
        setAiSummary("AI summary unavailable.");
      } finally {
        setAiLoading(false);
      }
    },
    [loadWarRoom]
  );

  // Demo path: auto-open open SEV1 (or first incident) so judges land in the war room.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await refreshIncidents();
        if (cancelled) return;
        const sev1 =
          list.find(
            (i) =>
              i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed"
          ) ||
          list.find((i) => i.severity === "SEV1") ||
          list[0];
        if (sev1) await loadSummary(sev1);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshIncidents, loadSummary]);

  // Live SLA countdown (1s tick) for the selected incident badge.
  // Depend only on incident_id so the interval is not reset every tick.
  const slaIncidentId = sla?.incident_id;
  useEffect(() => {
    if (!slaIncidentId) return;
    const id = window.setInterval(() => {
      setSla((prev) => {
        if (!prev || prev.incident_id !== slaIncidentId) return prev;
        const remaining_minutes = prev.remaining_minutes - 1 / 60;
        return {
          ...prev,
          remaining_minutes,
          breached: remaining_minutes < 0,
        };
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [slaIncidentId]);

  async function generatePostmortem() {
    if (!selected) return;
    setPostmortemLoading(true);
    setPostmortem(null);
    setPostmortemOpen(true);
    try {
      const res = await api.get<{ content: string }>(`/api/ai/postmortem/${selected.id}`);
      setPostmortem(res.content);
    } catch {
      setPostmortem("Postmortem generation failed. Ensure the incident has timeline data.");
    } finally {
      setPostmortemLoading(false);
    }
  }

  async function downloadPostmortem() {
    if (!selected) return;
    try {
      const token =
        localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
      const base =
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        process.env.NEXT_PUBLIC_API_URL ||
        "http://localhost:8000";
      const res = await fetch(`${base}/api/ai/postmortem/${selected.id}?format=md`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `postmortem-${selected.id.slice(0, 8)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setPostmortem("Download failed.");
    }
  }

  async function updateStatus(status: Incident["status"]) {
    if (!selected) return;
    setActionBusy(true);
    setActionError(null);
    try {
      const updated = await api.patch<Incident>(`/api/incidents/${selected.id}`, { status });
      setSelected(updated);
      setIncidents((prev) => prev.map((i) => (i.id === updated.id ? { ...i, ...updated } : i)));
      await loadWarRoom(updated);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Status update failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function assignToMe() {
    if (!selected || !user?.id) return;
    setActionBusy(true);
    setActionError(null);
    try {
      const updated = await api.post<Incident>(`/api/incidents/${selected.id}/assign`, {
        user_id: user.id,
      });
      setSelected(updated);
      setIncidents((prev) => prev.map((i) => (i.id === updated.id ? { ...i, ...updated } : i)));
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Assign failed");
    } finally {
      setActionBusy(false);
    }
  }

  async function toggleTask(task: IncidentTask) {
    const next = task.status === "completed" ? "open" : "completed";
    try {
      const updated = await api.patch<IncidentTask>(`/api/tasks/${task.id}`, { status: next });
      setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)));
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Task update failed");
    }
  }

  const openSev1 = useMemo(
    () => incidents.find((i) => i.severity === "SEV1" && i.status !== "resolved" && i.status !== "closed"),
    [incidents]
  );

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
          <p className="text-muted-foreground">
            {incidents.length} total incidents
            {openSev1 ? " · open SEV1 active — select it for the war room" : ""}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowVoice((v) => !v)}>
          {showVoice ? "Hide voice ticket" : "Voice → ticket"}
        </Button>
      </div>

      {showVoice && user?.team_id && (
        <VoiceRecorder
          teamId={user.team_id}
          onIncidentCreated={() => {
            void refreshIncidents();
          }}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident list */}
        <div className="lg:col-span-2 space-y-3">
          {incidents.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">No incidents yet.</CardContent>
            </Card>
          )}
          {incidents.map((inc) => (
            <Card
              key={inc.id}
              className={`cursor-pointer transition-all hover:ring-2 hover:ring-primary ${
                selected?.id === inc.id ? "ring-2 ring-primary" : ""
              }`}
              onClick={() => loadSummary(inc)}
            >
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{inc.title}</p>
                    <p className="text-sm text-muted-foreground truncate mt-1">{inc.description}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(inc.detected_at || inc.created_at).toLocaleString()}
                      {inc.assigned_to ? " · assigned" : " · unassigned"}
                    </p>
                  </div>
                  <div className="flex flex-col gap-1 items-end shrink-0">
                    <Badge variant={SEV_COLORS[inc.severity] as "destructive" | "secondary" | "outline" | "default"}>
                      {inc.severity}
                    </Badge>
                    <Badge variant={STATUS_BADGE[inc.status] || "default"}>{inc.status}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Detail / war room */}
        <div className="space-y-4">
          {selected ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{selected.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2 items-center">
                  <Badge variant={SEV_COLORS[selected.severity] as "destructive" | "secondary" | "outline" | "default"}>
                    {selected.severity}
                  </Badge>
                  <Badge variant={STATUS_BADGE[selected.status] || "default"}>{selected.status}</Badge>
                  {sla && (
                    <Badge variant={sla.breached ? "destructive" : "secondary"}>
                      SLA {formatSla(sla.remaining_minutes, sla.breached)}
                    </Badge>
                  )}
                </div>

                {/* Assign + status controls */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Status
                  </label>
                  <select
                    className="w-full h-9 rounded-md border bg-background px-2 text-sm"
                    value={selected.status}
                    disabled={actionBusy}
                    onChange={(e) => updateStatus(e.target.value as Incident["status"])}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="default"
                    size="sm"
                    className="w-full"
                    disabled={actionBusy || !user?.id}
                    onClick={assignToMe}
                  >
                    {selected.assigned_to === user?.id ? "Assigned to you" : "Assign to me"}
                  </Button>
                  {actionError && <p className="text-xs text-destructive">{actionError}</p>}
                </div>

                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                    AI Summary
                  </p>
                  {aiLoading ? (
                    <p className="text-sm text-muted-foreground animate-pulse">Generating summary…</p>
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">{aiSummary || "Click an incident to load AI summary."}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full" onClick={() => loadSummary(selected)}>
                    Refresh Summary
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={async () => {
                      try {
                        type RootCauseRow = {
                          hypothesis?: string;
                          cause?: string;
                          confidence?: number;
                          suggested_action?: string;
                        };
                        const res = await api.post<{
                          root_causes?: RootCauseRow[];
                          suggestions?: RootCauseRow[];
                        }>(`/api/ai/incidents/${selected.id}/root-causes`, {});
                        const rows: RootCauseRow[] = res.root_causes || res.suggestions || [];
                        if (!rows.length) {
                          setAiSummary("No root-cause hypotheses returned.");
                          return;
                        }
                        const causes = rows
                          .map((s) => {
                            const label = s.hypothesis || s.cause || "Unknown";
                            const pct = Math.round((s.confidence ?? 0) * 100);
                            const action = s.suggested_action ? `\n  → ${s.suggested_action}` : "";
                            return `• ${label} (${pct}%)${action}`;
                          })
                          .join("\n");
                        setAiSummary(`Root Causes:\n${causes}`);
                      } catch {
                        setAiSummary("Root cause analysis failed.");
                      }
                    }}
                  >
                    Root Cause Analysis
                  </Button>
                  <Dialog open={postmortemOpen} onOpenChange={setPostmortemOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full" onClick={generatePostmortem}>
                        Generate Postmortem
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Postmortem — {selected?.title}</DialogTitle>
                      </DialogHeader>
                      {postmortemLoading ? (
                        <p className="text-sm text-muted-foreground animate-pulse">Generating postmortem…</p>
                      ) : (
                        <div className="space-y-3">
                          <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">{postmortem}</div>
                          <Button variant="default" size="sm" onClick={downloadPostmortem}>
                            Download Markdown
                          </Button>
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                </div>

                {/* Timeline provenance */}
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    Timeline
                  </p>
                  {warLoading ? (
                    <p className="text-xs text-muted-foreground animate-pulse">Loading war room…</p>
                  ) : timeline.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No timeline events yet.</p>
                  ) : (
                    <ol className="space-y-2 border-l-2 border-muted pl-3">
                      {timeline.map((ev) => (
                        <li key={ev.id} className="text-xs">
                          <div className="font-medium">{ev.event_type}</div>
                          <div className="text-muted-foreground">{ev.description}</div>
                          <div className="text-[10px] text-muted-foreground mt-0.5">
                            {ev.source} · {ev.actor} · {new Date(ev.ts).toLocaleString()}
                          </div>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>

                {/* Tasks */}
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    Tasks
                  </p>
                  {tasks.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No tasks for this incident.</p>
                  ) : (
                    <ul className="space-y-1.5">
                      {tasks.map((t) => (
                        <li key={t.id} className="flex items-start gap-2 text-sm">
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={t.status === "completed"}
                            onChange={() => toggleTask(t)}
                          />
                          <div className="min-w-0">
                            <p className={t.status === "completed" ? "line-through text-muted-foreground" : ""}>
                              {t.title}
                            </p>
                            <p className="text-[10px] text-muted-foreground uppercase">{t.priority}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground text-sm">
                Select an incident to open the war room (timeline, tasks, SLA, AI).
              </CardContent>
            </Card>
          )}

          {selected && (
            <CommsPanel
              incidentId={selected.id}
              currentUserId={user?.id}
              defaultOpen={true}
              showToggle={true}
            />
          )}

          <div>
            <ChatPanel incidentId={selected?.id} />
          </div>
        </div>
      </div>
    </div>
  );
}
