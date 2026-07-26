"use client";

import { useEffect, useState } from "react";
import { useUser, useRole } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { Skeleton } from "@/components/ui/skeleton";
import { Sun, Moon, Key, Bell, User as UserIcon, Mail, Slack, UserPlus, Shield, Clock, CalendarDays } from "lucide-react";

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

function ToggleSwitch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer group">
      <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
          checked ? "bg-primary" : "bg-input"
        }`}
      >
        <span
          className={`pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform ${
            checked ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </button>
    </label>
  );
}

function SettingsSkeleton() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="space-y-2">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-4 w-56" />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-5 w-28" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="flex justify-between gap-4">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

export default function SettingsPage() {
  const user = useUser();
  const role = useRole();
  const [demo, setDemo] = useState<DemoStatus | null>(null);
  const [health, setHealth] = useState<"ok" | "down" | "checking">("checking");
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Dark mode
  const [darkMode, setDarkMode] = useState(false);

  // Notification toggles
  const [notifEmail, setNotifEmail] = useState(true);
  const [notifSlack, setNotifSlack] = useState(false);
  const [notifPagerDuty, setNotifPagerDuty] = useState(false);

  // API keys
  const [apiKey] = useState("sk-" + "•".repeat(40));

  useEffect(() => {
    const stored = localStorage.getItem("sentinel-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored ? stored === "dark" : prefersDark;
    setDarkMode(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("sentinel-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

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
    } finally {
      setLoaded(true);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  if (!loaded) return <SettingsSkeleton />;

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your account, team, and preferences</p>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UserIcon className="h-4 w-4" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center gap-4 pb-3 border-b">
            <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center text-lg font-semibold text-muted-foreground">
              {user?.name?.charAt(0)?.toUpperCase() ?? "?"}
            </div>
            <div className="space-y-0.5">
              <p className="font-medium text-base">{user?.name ?? "—"}</p>
              <p className="text-muted-foreground text-xs">{user?.email ?? "—"}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground flex items-center gap-1.5">
                <Shield className="h-3.5 w-3.5" />
                Role
              </span>
              <Badge variant="secondary">{role ?? "—"}</Badge>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground flex items-center gap-1.5">
                <CalendarDays className="h-3.5 w-3.5" />
                Member since
              </span>
              <span className="font-medium text-xs sm:text-sm">{formatDate(user?.created_at)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                Last active
              </span>
              <span className="font-medium text-xs sm:text-sm">{formatDate(user?.last_login_at)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Team ID</span>
              <code className="text-xs truncate max-w-[180px]">{user?.team_id ?? "—"}</code>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">User ID</span>
              <code className="text-xs truncate max-w-[180px]">{user?.id ?? "—"}</code>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Status</span>
              <Badge variant={user?.is_active ? "default" : "secondary"}>
                {user?.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            {darkMode ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Dark mode</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDarkMode((prev) => !prev)}
              className="gap-2"
            >
              {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {darkMode ? "Light" : "Dark"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Team Management */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UserPlus className="h-4 w-4" />
            Team Management
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Team name</span>
            <span className="font-medium">Engineering</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Members</span>
            <span className="font-medium">8 active</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Team ID</span>
            <code className="text-xs truncate max-w-[200px]">{user?.team_id ?? "—"}</code>
          </div>
          <div className="pt-2 flex flex-col sm:flex-row gap-2">
            <Button variant="default" size="sm" className="gap-1.5">
              <UserPlus className="h-3.5 w-3.5" />
              Invite member
            </Button>
            <Button variant="outline" size="sm">
              Manage team
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Production key</span>
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono tracking-wider select-all">{apiKey.slice(0, 12)}••••••••••••••••</code>
              <Badge variant="secondary" className="text-[10px]">read / write</Badge>
            </div>
          </div>
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Read-only key</span>
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono tracking-wider select-all">sor••••••••••••••••••••••••</code>
              <Badge variant="secondary" className="text-[10px]">read only</Badge>
            </div>
          </div>
          <div className="pt-2">
            <p className="text-muted-foreground text-xs">
              Manage API keys in the{" "}
              <span className="font-medium text-foreground cursor-pointer hover:underline">
                Developer Console
              </span>
              . Keys inherit your team permissions and can be rotated at any time.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <ToggleSwitch checked={notifEmail} onChange={setNotifEmail} label="Email notifications" />
          <div className="flex items-center gap-3">
            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">{user?.email ?? "—"}</span>
          </div>
          <div className="border-t" />
          <ToggleSwitch checked={notifSlack} onChange={setNotifSlack} label="Slack alerts" />
          <div className="flex items-center gap-3">
            <Slack className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">#incidents channel</span>
          </div>
          <div className="border-t" />
          <ToggleSwitch checked={notifPagerDuty} onChange={setNotifPagerDuty} label="PagerDuty escalation" />
          <div className="flex items-center gap-3">
            <Bell className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">SEV1 / SEV2 only</span>
          </div>
        </CardContent>
      </Card>

      {/* API & demo readiness */}
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
            <code className="text-xs break-all text-right max-w-[280px]">{API_BASE}</code>
          </div>
          <div className="flex justify-between gap-4 items-center">
            <span className="text-muted-foreground">Health</span>
            <Badge variant={health === "ok" ? "default" : health === "checking" ? "secondary" : "destructive"}>
              {health === "ok" ? "healthy" : health === "checking" ? "checking\u2026" : "down"}
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
                {demo.incident_count} total \u00B7 {demo.sev1_count ?? 0} SEV1 \u00B7 {demo.resolved_count ?? 0} resolved
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

      {/* Integrations */}
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
