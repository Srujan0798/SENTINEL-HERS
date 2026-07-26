"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { 
  Container, 
  Server, 
  Activity, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Zap,
  MemoryStick
} from "lucide-react";

interface Alert {
  id: string;
  title?: string;
  description?: string;
  message: string;
  severity: "low" | "medium" | "high" | "critical" | "warning" | "info";
  timestamp: string;
  created_at?: string;
  container_id?: string;
}

interface ContainerMetrics {
  id: string;
  name: string;
  status: "running" | "stopped" | "error";
  health: "healthy" | "warning" | "critical";
  cpu: {
    current: number;
    limit: number;
    usage: number;
  };
  memory: {
    current: number;
    limit: number;
    usage: number;
  };
  restarts: number;
  uptime: string;
  lastRestart?: string;
  source: "docker" | "kubernetes";
}

interface ContainerHealthOverview {
  total: number;
  healthy: number;
  warning: number;
  critical: number;
  cpuAvg: number;
  memoryAvg: number;
}

export function EnhancedContainerMonitoring() {
  const [containers, setContainers] = useState<ContainerMetrics[]>([]);
  const [overview, setOverview] = useState<ContainerHealthOverview | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration - in real implementation, this would come from backend
      const mockContainers: ContainerMetrics[] = [
        {
          id: "web-1",
          name: "web-server",
          status: "running",
          health: "healthy",
          cpu: { current: 45, limit: 100, usage: 45 },
          memory: { current: 512, limit: 1024, usage: 50 },
          restarts: 2,
          uptime: "15d 3h",
          lastRestart: "2024-01-15T10:30:00Z",
          source: "docker"
        },
        {
          id: "api-1",
          name: "api-gateway",
          status: "running",
          health: "warning",
          cpu: { current: 78, limit: 100, usage: 78 },
          memory: { current: 768, limit: 1024, usage: 75 },
          restarts: 5,
          uptime: "8d 12h",
          lastRestart: "2024-01-16T14:20:00Z",
          source: "kubernetes"
        },
        {
          id: "db-1",
          name: "database",
          status: "running",
          health: "critical",
          cpu: { current: 95, limit: 100, usage: 95 },
          memory: { current: 2048, limit: 2048, usage: 100 },
          restarts: 1,
          uptime: "30d 5h",
          lastRestart: "2024-01-10T09:15:00Z",
          source: "docker"
        }
      ];

      const mockAlerts: Alert[] = [
        {
          id: "alert-1",
          message: "Database container CPU usage at 95%",
          title: "High CPU Usage",
          description: "Database container CPU usage at 95%",
          severity: "warning",
          timestamp: "2024-01-17T10:30:00Z",
          created_at: "2024-01-17T10:30:00Z"
        },
        {
          id: "alert-2", 
          message: "API Gateway memory usage at 75%",
          title: "Memory Pressure",
          description: "API Gateway memory usage at 75%",
          severity: "info",
          timestamp: "2024-01-17T09:15:00Z",
          created_at: "2024-01-17T09:15:00Z"
        }
      ];

      setContainers(mockContainers);
      
      const overview: ContainerHealthOverview = {
        total: mockContainers.length,
        healthy: mockContainers.filter(c => c.health === "healthy").length,
        warning: mockContainers.filter(c => c.health === "warning").length,
        critical: mockContainers.filter(c => c.health === "critical").length,
        cpuAvg: mockContainers.reduce((sum, c) => sum + c.cpu.usage, 0) / mockContainers.length,
        memoryAvg: mockContainers.reduce((sum, c) => sum + c.memory.usage, 0) / mockContainers.length
      };
      
      setOverview(overview);
      setAlerts(mockAlerts);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Failed to fetch container data:", error);
    } finally {
      setLoading(false);
    }
  };



  const getHealthColor = (health: string) => {
    switch (health) {
      case "healthy": return "bg-green-100 text-green-800";
      case "warning": return "bg-yellow-100 text-yellow-800";
      case "critical": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-20" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map(i => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-32 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Container Monitoring</h2>
          <p className="text-muted-foreground">
            Real-time container health and resource utilization
            {lastUpdate && (
              <span className="ml-2 text-xs">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Health Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Containers</CardTitle>
            <Container className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total}</div>
            <p className="text-xs text-muted-foreground">
              Across all sources
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Healthy</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{overview?.healthy}</div>
            <Progress value={(overview?.healthy || 0) / (overview?.total || 1) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{overview?.warning}</div>
            <Progress value={(overview?.warning || 0) / (overview?.total || 1) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{overview?.critical}</div>
            <Progress value={(overview?.critical || 0) / (overview?.total || 1) * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Resource Utilization Overview */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              CPU Utilization
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Average</span>
                <span className="text-sm">{overview?.cpuAvg.toFixed(1)}%</span>
              </div>
              <Progress value={overview?.cpuAvg} className="h-2" />
              <div className="grid grid-cols-3 gap-4 text-center text-xs">
                <div>
                  <div className="font-medium">Low</div>
                  <div className="text-green-600">&lt; 50%</div>
                </div>
                <div>
                  <div className="font-medium">Medium</div>
                  <div className="text-yellow-600">50-80%</div>
                </div>
                <div>
                  <div className="font-medium">High</div>
                  <div className="text-red-600">&gt; 80%</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MemoryStick className="h-5 w-5" />
              Memory Utilization
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Average</span>
                <span className="text-sm">{overview?.memoryAvg.toFixed(1)}%</span>
              </div>
              <Progress value={overview?.memoryAvg} className="h-2" />
              <div className="grid grid-cols-3 gap-4 text-center text-xs">
                <div>
                  <div className="font-medium">Low</div>
                  <div className="text-green-600">&lt; 50%</div>
                </div>
                <div>
                  <div className="font-medium">Medium</div>
                  <div className="text-yellow-600">50-80%</div>
                </div>
                <div>
                  <div className="font-medium">High</div>
                  <div className="text-red-600">&gt; 80%</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Container List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Container Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {containers.map(container => (
              <div key={container.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Container className="h-5 w-5" />
                    <div>
                      <div className="font-medium">{container.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {container.source} • {container.uptime} uptime
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getHealthColor(container.health)}>
                      {container.health}
                    </Badge>
                    <Badge variant={container.status === "running" ? "default" : "secondary"}>
                      {container.status}
                    </Badge>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      <span className="text-sm font-medium">CPU</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Usage</span>
                        <span>{container.cpu.usage}%</span>
                      </div>
                      <Progress value={container.cpu.usage} className="h-2" />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <MemoryStick className="h-4 w-4" />
                      <span className="text-sm font-medium">Memory</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span>Usage</span>
                        <span>{container.memory.usage}%</span>
                      </div>
                      <Progress value={container.memory.usage} className="h-2" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Activity className="h-4 w-4" />
                      <span>Restarts: {container.restarts}</span>
                    </div>
                    {container.lastRestart && (
                      <div className="flex items-center gap-1">
                        <RefreshCw className="h-4 w-4" />
                        <span>Last: {new Date(container.lastRestart).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                  <Button variant="outline" size="sm">
                    View Logs
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.map(alert => (
                <div key={alert.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    <div>
                      <div className="font-medium">{alert.title}</div>
                      <div className="text-sm text-muted-foreground">{alert.description}</div>
                    </div>
                  </div>
                  <Badge variant={alert.severity === "warning" ? "destructive" : "secondary"}>
                    {alert.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}