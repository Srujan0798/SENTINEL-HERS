"use client";

import { useEffect, useState } from "react";
import { useUser, useRole } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

interface DemoStatus {
  ready?: boolean;
  demo_email?: string;
  incident_count?: number;
  sev1_count?: number;
  resolved_count?: number;
  frontend?: string;
  login_hint?: string;
  reason?: string;
}

export default function SettingsPage() {
  const user = useUser();
  const role = useRole();
  const [demo, setDemo] = useState<DemoStatus | null>(null);
  const [health, setHealth] = useState<"ok" | "down" | "checking">("checking");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    setHealth("checking");
    try {
      const h = await fetch(`${API_BASE}/healthz`);
      setHealth(h.ok ? "ok" : "down");
    } catch {
      setHealth("down");
    }
    try {
      const res = await fetch(`${API_BASE}/api/demo-status`);
      if (!res.ok) throw new Error(`demo-status HTTP ${res.status}`);
      setDemo(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load demo status");
      setDemo(null);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Team, session, and demo readiness</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Name</span>
            <span className="font-medium">{user?.name ?? "—"}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email ?? "—"}</span>
          </div>
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Role</span>
            <Badge variant="secondary">{role ?? "—"}</Badge>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Team ID</span>
            <code className="text-xs truncate max-w-[240px]">{user?.team_id ?? "—"}</code>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">User ID</span>
            <code className="text-xs truncate max-w-[240px]">{user?.id ?? "—"}</code>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">API &amp; demo readiness</CardTitle>
          <Button variant="outline" size="sm" onClick={refresh}>
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">API base</span>
            <code className="text-xs break-all text-right">{API_BASE}</code>
          </div>
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Health</span>
            <Badge variant={health === "ok" ? "default" : health === "checking" ? "secondary" : "destructive"}>
              {health === "ok" ? "healthy" : health === "checking" ? "checking…" : "down"}
            </Badge>
          </div>
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Demo ready</span>
            <Badge variant={demo?.ready ? "default" : "destructive"}>
              {demo?.ready ? "ready" : demo ? "not ready" : "unknown"}
            </Badge>
          </div>
          {demo?.incident_count != null && (
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Seeded incidents</span>
              <span>
                {demo.incident_count} total · {demo.sev1_count ?? 0} SEV1 · {demo.resolved_count ?? 0} resolved
              </span>
            </div>
          )}
          {demo?.login_hint && (
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Judge login</span>
              <code className="text-xs">{demo.login_hint}</code>
            </div>
          )}
          {error && <p className="text-destructive text-xs">{error}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Integrations</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>GitHub / GitLab webhooks: <code className="text-xs">POST /api/integrations/github/webhook</code></p>
          <p>Deployments appear under <strong>Deployments</strong> after webhooks or demo seed.</p>
          <p>Realtime SSE uses your session token automatically from the nav status indicator.</p>
        </CardContent>
      </Card>
    </div>
  );
}
