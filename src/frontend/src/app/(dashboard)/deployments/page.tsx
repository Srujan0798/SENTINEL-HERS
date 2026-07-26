"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import {
  Copy,
  Check,
  XCircle,
  GitBranch,
  GitMerge,
  Gitlab,
  Github,
  Rocket,
  Clock,
  Activity,
} from "lucide-react";

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
  rollback: "bg-[color:var(--sev1)]/15 text-[color:var(--sev1)]",
};

const SOURCE_COLORS: Record<string, string> = {
  github: "bg-[color:var(--panel-elevated)] text-[color:var(--ink)] border border-[color:var(--line)]",
  gitlab: "bg-[color:var(--phosphor)]/20 text-[color:var(--phosphor)]",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  success: <Check className="h-3 w-3" />,
  failed: <XCircle className="h-3 w-3" />,
  rollback: <XCircle className="h-3 w-3" />,
  running: <Activity className="h-3 w-3" />,
  pending: <Clock className="h-3 w-3" />,
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  github: <Github className="h-3 w-3" />,
  gitlab: <Gitlab className="h-3 w-3" />,
};

function copySha(sha: string) {
  navigator.clipboard.writeText(sha).then(() => {
    toast("Copied", "success", 2000);
  }).catch(() => {
    toast("Failed to copy", "destructive", 2000);
  });
}

function getRelativeTime(dateStr: string): string {
  if (!dateStr) return "\u2014";
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

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

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48" />
          <Skeleton className="h-5 w-72 mt-2" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-28" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-40" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) return <div className="text-red-600 p-4">Error: {error}</div>;

  const successRate = deployments.length
    ? Math.round((deployments.filter((d) => d.status === "success").length / deployments.length) * 100)
    : 0;

  const isFailed = (status: string) => status === "failed" || status === "rollback";

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
            <div className="text-3xl font-bold flex items-center gap-2">
              <Rocket className="h-5 w-5 text-muted-foreground" />
              {deployments.length}
            </div>
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
            <div className="text-3xl font-bold flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-muted-foreground" />
              {commits.length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mt-1">
              <Badge className={SOURCE_COLORS.github}>
                <Github className="h-3 w-3 mr-1" /> GitHub
              </Badge>
              <Badge className={SOURCE_COLORS.gitlab}>
                <Gitlab className="h-3 w-3 mr-1" /> GitLab
              </Badge>
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
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Rocket className="h-12 w-12 text-muted-foreground/40 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">No deployments yet</p>
              <p className="text-sm text-muted-foreground/60 mt-1 max-w-sm">
                Connect GitHub or GitLab webhooks to start tracking deployments automatically.
              </p>
            </div>
          ) : (
            <>
              {/* Desktop table */}
              <div className="hidden md:block overflow-x-auto">
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
                      <tr
                        key={d.id}
                        className={`border-b last:border-0 transition-colors ${
                          isFailed(d.status)
                            ? "bg-red-500/5 border-red-500/20"
                            : ""
                        }`}
                      >
                        <td className="py-2 pr-4 font-medium">{d.service}</td>
                        <td className="py-2 pr-4">
                          <Badge variant="outline" className="text-xs">{d.environment}</Badge>
                        </td>
                        <td className="py-2 pr-4 font-mono text-xs">{d.version}</td>
                        <td className="py-2 pr-4">
                          <div className="flex items-center gap-1">
                            <code className="font-mono text-xs">{d.sha?.slice(0, 7)}</code>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5"
                              onClick={() => copySha(d.sha)}
                              aria-label="Copy SHA"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </td>
                        <td className="py-2 pr-4">
                          <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${STATUS_COLORS[d.status] || ""}`}>
                            {STATUS_ICONS[d.status] || null}
                            {d.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4">
                          <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${SOURCE_COLORS[d.source] || ""}`}>
                            {SOURCE_ICONS[d.source] || null}
                            {d.source}
                          </span>
                        </td>
                        <td className="py-2 text-xs text-muted-foreground whitespace-nowrap">
                          {getRelativeTime(d.deployed_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile cards */}
              <div className="md:hidden space-y-3">
                {deployments.map((d) => (
                  <Card
                    key={d.id}
                    className={`${
                      isFailed(d.status)
                        ? "border-red-500/40 bg-red-500/5"
                        : ""
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-medium text-sm">{d.service}</p>
                          <p className="text-xs text-muted-foreground">{getRelativeTime(d.deployed_at)}</p>
                        </div>
                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded shrink-0 ${STATUS_COLORS[d.status] || ""}`}>
                          {STATUS_ICONS[d.status] || null}
                          {d.status}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2 items-center text-xs">
                        <Badge variant="outline" className="text-xs">{d.environment}</Badge>
                        <span className="font-mono text-xs text-muted-foreground">{d.version}</span>
                        <div className="flex items-center gap-1">
                          <code className="font-mono text-xs text-muted-foreground">{d.sha?.slice(0, 7)}</code>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-5 w-5"
                            onClick={() => copySha(d.sha)}
                            aria-label="Copy SHA"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded ${SOURCE_COLORS[d.source] || ""}`}>
                          {SOURCE_ICONS[d.source] || null}
                          {d.source}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Commits</CardTitle>
        </CardHeader>
        <CardContent>
          {commits.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <GitMerge className="h-12 w-12 text-muted-foreground/40 mb-4" />
              <p className="text-lg font-medium text-muted-foreground">No commits yet</p>
              <p className="text-sm text-muted-foreground/60 mt-1 max-w-sm">
                Commits will appear here once deployments are tracked.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {commits.slice(0, 15).map((c) => (
                <div key={c.id} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <div className="flex items-center gap-1 shrink-0">
                    <code className="text-xs bg-[color:var(--panel-elevated)] px-2 py-0.5 rounded font-mono">
                      {c.sha?.slice(0, 7)}
                    </code>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5"
                      onClick={() => copySha(c.sha)}
                      aria-label="Copy SHA"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{c.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {c.author} &middot; {c.service} &middot; {c.branch}
                    </p>
                  </div>
                  <Badge className={`inline-flex items-center gap-1 shrink-0 ${SOURCE_COLORS[c.source] || ""}`}>
                    {SOURCE_ICONS[c.source] || null}
                    {c.source}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
