"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type Alert } from "@/lib/api";

interface Container {
  name: string;
  image: string;
  status: string;
  health: string;
  cpu_pct: number;
  mem_mb: number;
  source: "docker" | "kubernetes";
}

export default function MonitoringPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [containers, setContainers] = useState<{ docker: Container[]; kubernetes: Container[] }>({
    docker: [],
    kubernetes: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.get<Alert[]>("/api/logs/alerts"),
      api.get<{ docker: Container[]; kubernetes: Container[] }>("/api/integrations/containers"),
    ]).then(([a, c]) => {
      if (a.status === "fulfilled") setAlerts(a.value);
      if (c.status === "fulfilled") setContainers(c.value);
      setLoading(false);
    });
  }, []);

  const allContainers = [...containers.docker, ...containers.kubernetes];

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Monitoring</h1>
        <p className="text-muted-foreground">Alerts and container health</p>
      </div>

      {/* Active Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts ({alerts.filter((a) => a.status !== "resolved").length})</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-muted-foreground text-sm">No alerts.</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 rounded border">
                  <div>
                    <p className="text-sm font-medium">{alert.name}</p>
                    <p className="text-xs text-muted-foreground">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">{alert.source} · {new Date(alert.fired_at).toLocaleString()}</p>
                  </div>
                  <Badge variant={alert.severity === "critical" ? "destructive" : "secondary"}>
                    {alert.severity}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Containers */}
      <Card>
        <CardHeader>
          <CardTitle>Containers ({allContainers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {allContainers.length === 0 ? (
            <p className="text-muted-foreground text-sm">No containers detected. Docker or Kubernetes not connected.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground text-xs uppercase">
                    <th className="text-left py-2 pr-4">Name</th>
                    <th className="text-left py-2 pr-4">Source</th>
                    <th className="text-left py-2 pr-4">Status</th>
                    <th className="text-left py-2 pr-4">Health</th>
                    <th className="text-right py-2">CPU%</th>
                  </tr>
                </thead>
                <tbody>
                  {allContainers.map((c) => (
                    <tr key={`${c.source}-${c.name}`} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-mono text-xs">{c.name}</td>
                      <td className="py-2 pr-4">
                        <Badge variant="outline" className="text-xs">{c.source}</Badge>
                      </td>
                      <td className="py-2 pr-4">{c.status}</td>
                      <td className="py-2 pr-4">
                        <span className={c.health === "healthy" ? "text-green-600" : "text-red-600"}>
                          {c.health}
                        </span>
                      </td>
                      <td className="py-2 text-right">{c.cpu_pct?.toFixed(1) ?? "—"}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
