"use client";

import { useUser, useRole } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const user = useUser();
  const role = useRole();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back, {user?.name}. You are signed in as <strong>{role}</strong>.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Incidents</CardTitle>
            <Badge variant="secondary">SEV1-4</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">Active incidents</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SEV1 Active</CardTitle>
            <Badge variant="destructive">Critical</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">2</div>
            <p className="text-xs text-muted-foreground">Requires immediate attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MTTR (24h)</CardTitle>
            <Badge variant="info">Avg</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">47m</div>
            <p className="text-xs text-muted-foreground">Mean time to resolve</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SLA Compliance</CardTitle>
            <Badge variant="success">On Track</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94%</div>
            <p className="text-xs text-muted-foreground">Within target</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Incidents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Database connection pool exhaustion</p>
                <p className="text-sm text-muted-foreground">api-gateway • 15 min ago</p>
              </div>
              <Badge variant="destructive">SEV1</Badge>
            </div>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">High latency on payment service</p>
                <p className="text-sm text-muted-foreground">payment-service • 1 hour ago</p>
              </div>
              <Badge variant="warning">SEV2</Badge>
            </div>
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="font-medium">Log aggregation delayed</p>
                <p className="text-sm text-muted-foreground">logging • 3 hours ago</p>
              </div>
              <Badge variant="info">SEV3</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}