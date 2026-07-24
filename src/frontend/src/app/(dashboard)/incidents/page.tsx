"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { api, type Incident } from "@/lib/api";
import { ChatPanel } from "@/components/chat/ChatPanel";

const SEV_COLORS: Record<string, string> = {
  SEV1: "destructive",
  SEV2: "destructive",
  SEV3: "secondary",
  SEV4: "outline",
} as const;

const STATUS_BADGE: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  open: "destructive",
  investigating: "destructive",
  mitigating: "secondary",
  resolved: "outline",
  closed: "outline",
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [postmortem, setPostmortem] = useState<string | null>(null);
  const [postmortemLoading, setPostmortemLoading] = useState(false);
  const [postmortemOpen, setPostmortemOpen] = useState(false);

  useEffect(() => {
    api.get<Incident[]>("/api/incidents")
      .then(setIncidents)
      .finally(() => setLoading(false));
  }, []);

  async function loadSummary(inc: Incident) {
    setSelected(inc);
    setAiSummary(null);
    setAiLoading(true);
    try {
      const res = await api.get<{ summary: string }>(`/api/ai/incidents/${inc.id}/summary`);
      setAiSummary(res.summary);
    } catch {
      setAiSummary("AI summary unavailable.");
    } finally {
      setAiLoading(false);
    }
  }

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
      const token = localStorage.getItem("sentinel_token");
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Incidents</h1>
        <p className="text-muted-foreground">{incidents.length} total incidents</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident list */}
        <div className="lg:col-span-2 space-y-3">
          {incidents.length === 0 && (
            <Card><CardContent className="py-8 text-center text-muted-foreground">No incidents yet.</CardContent></Card>
          )}
          {incidents.map((inc) => (
            <Card
              key={inc.id}
              className={`cursor-pointer transition-all hover:ring-2 hover:ring-primary ${selected?.id === inc.id ? "ring-2 ring-primary" : ""}`}
              onClick={() => loadSummary(inc)}
            >
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{inc.title}</p>
                    <p className="text-sm text-muted-foreground truncate mt-1">{inc.description}</p>
                    <p className="text-xs text-muted-foreground mt-2">{new Date(inc.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-col gap-1 items-end shrink-0">
                    <Badge variant={SEV_COLORS[inc.severity] as "destructive" | "secondary" | "outline" | "default"}>
                      {inc.severity}
                    </Badge>
                    <Badge variant={STATUS_BADGE[inc.status] || "default"}>
                      {inc.status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Detail panel */}
        <div>
          {selected ? (
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle className="text-base">{selected.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Badge variant={SEV_COLORS[selected.severity] as "destructive" | "secondary" | "outline" | "default"}>
                    {selected.severity}
                  </Badge>
                  <Badge variant={STATUS_BADGE[selected.status] || "default"}>{selected.status}</Badge>
                </div>

                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">AI Summary</p>
                  {aiLoading ? (
                    <p className="text-sm text-muted-foreground animate-pulse">Generating summary…</p>
                  ) : (
                    <p className="text-sm">{aiSummary || "Click an incident to load AI summary."}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => loadSummary(selected)}
                  >
                    Refresh Summary
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const res = await api.post<{ suggestions: Array<{ cause: string; confidence: number }> }>(
                          `/api/ai/incidents/${selected.id}/root-causes`,
                          {}
                        );
                        const causes = res.suggestions
                          .map((s) => `• ${s.cause} (${Math.round(s.confidence * 100)}%)`)
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
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={generatePostmortem}
                      >
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
                          <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">
                            {postmortem}
                          </div>
                          <Button variant="default" size="sm" onClick={downloadPostmortem}>
                            Download Markdown
                          </Button>
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground text-sm">
                Select an incident to view details and AI analysis.
              </CardContent>
            </Card>
          )}

          {/* AI Chat Panel */}
          <div className="mt-4">
            <ChatPanel incidentId={selected?.id} />
          </div>
        </div>
      </div>
    </div>
  );
}
