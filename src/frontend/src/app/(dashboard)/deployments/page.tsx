"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Deployment {
  id: string;
  service: string;
  environment: string;
  version: string;
  sha: string;
  status: string;
  source: "github" | "gitlab";
  deployed_by: string;
  deployed_at: string;
}

interface Commit {
  id: string;
  sha: string;
  message: string;
  author: string;
  service: string;
  branch: string;
  source: "github" | "gitlab";
}

const STATUS_COLORS: Record<string, string> = {
  success: "bg-[color:var(--ok)]/15 text-[color:var(--ok)]",
  pending: "bg-[color:var(--warn)]/15 text-[color:var(--warn)]",
  failed: "bg-[color:var(--sev1)]/15 text-[color:var(--sev1)]",
  running: "bg-[color:var(--ice)]/15 text-[color:var(--ice)]",
};

const SOURCE_COLORS: Record<string, string> = {
  github: "bg-[color:var(--panel-elevated)] text-[color:var(--ink)] border border-[color:var(--line)]",
  gitlab: "bg-[color:var(--phosphor)]/20 text-[color:var(--phosphor)]",
};

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token") || localStorage.getItem("sentinel_token")
        : null;
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    Promise.allSettled([
      fetch(`${apiBase}/api/integrations/deployments`, { headers }).then((r) => r.ok ? r.json() : []),
      fetch(`${apiBase}/api/integrations/commits`, { headers }).then((r) => r.ok ? r.json() : []),
    ]).then(([depRes, comRes]) => {
      if (depRes.status === "fulfilled") setDeployments(depRes.value);
      if (comRes.status === "fulfilled") setCommits(comRes.value);
      setLoading(false);
    }).catch((e) => {
      setError(e instanceof Error ? e.message : "Failed to load");
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>;
  if (error) return <div className="text-red-600 p-4">Error: {error}</div>;

  const successRate = deployments.length
    ? Math.round((deployments.filter((d) => d.status === "success").length / deployments.length) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Deployments</h1>
        <p className="text-muted-foreground">VCS-integrated deployment tracking</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Deployments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{deployments.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-data text-[color:var(--ok)]">{successRate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Commits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{commits.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mt-1">
              <Badge className={SOURCE_COLORS.github}>GitHub</Badge>
              <Badge className={SOURCE_COLORS.gitlab}>GitLab</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Deployments</CardTitle>
        </CardHeader>
        <CardContent>
          {deployments.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No deployments yet. Connect GitHub or GitLab webhooks to start tracking.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground text-xs uppercase">
                    <th className="text-left py-2 pr-4">Service</th>
                    <th className="text-left py-2 pr-4">Environment</th>
                    <th className="text-left py-2 pr-4">Version</th>
                    <th className="text-left py-2 pr-4">SHA</th>
                    <th className="text-left py-2 pr-4">Status</th>
                    <th className="text-left py-2 pr-4">Source</th>
                    <th className="text-left py-2 pr-4">When</th>
                  </tr>
                </thead>
                <tbody>
                  {deployments.map((d) => (
                    <tr key={d.id} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-medium">{d.service}</td>
                      <td className="py-2 pr-4">
                        <Badge variant="outline" className="text-xs">{d.environment}</Badge>
                      </td>
                      <td className="py-2 pr-4 font-mono text-xs">{d.version}</td>
                      <td className="py-2 pr-4 font-mono text-xs">{d.sha?.slice(0, 7)}</td>
                      <td className="py-2 pr-4">
                        <span className={`text-xs px-2 py-0.5 rounded ${STATUS_COLORS[d.status] || ""}`}>
                          {d.status}
                        </span>
                      </td>
                      <td className="py-2 pr-4">
                        <span className={`text-xs px-2 py-0.5 rounded ${SOURCE_COLORS[d.source] || ""}`}>
                          {d.source}
                        </span>
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">
                        {d.deployed_at ? new Date(d.deployed_at).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Commits</CardTitle>
        </CardHeader>
        <CardContent>
          {commits.length === 0 ? (
            <p className="text-muted-foreground text-sm">No commits yet.</p>
          ) : (
            <div className="space-y-2">
              {commits.slice(0, 15).map((c) => (
                <div key={c.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <code className="text-xs bg-gray-100 px-2 py-0.5 rounded font-mono shrink-0">
                    {c.sha?.slice(0, 7)}
                  </code>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{c.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {c.author} · {c.service} · {c.branch}
                    </p>
                  </div>
                  <Badge className={SOURCE_COLORS[c.source] || ""}>{c.source}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
