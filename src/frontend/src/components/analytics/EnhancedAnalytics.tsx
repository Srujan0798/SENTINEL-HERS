"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type Incident } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";
import { TrendingUp, AlertTriangle, Clock, Users } from "lucide-react";

interface EnhancedAnalyticsProps {
  teamId: string;
}

const SEV_COLORS = {
  SEV1: "#ef4444",
  SEV2: "#f59e0b", 
  SEV3: "#3b82f6",
  SEV4: "#6b7280",
};

const SEV_LABELS = {
  SEV1: "Critical",
  SEV2: "High",
  SEV3: "Medium",
  SEV4: "Low",
};

export function EnhancedAnalytics({ teamId }: EnhancedAnalyticsProps) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d">("7d");

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/incidents?team_id=${teamId}&limit=100`);
        setIncidents(response.data || []);
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
  }, [teamId, timeRange]);

  // Calculate incident trends
  const getIncidentTrends = () => {
    const now = new Date();
    const ranges = {
      "24h": 24,
      "7d": 7 * 24,
      "30d": 30 * 24,
    };

    const hours = ranges[timeRange];
    const labels = [];
    const data = [];

    for (let i = hours; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const label = timeRange === "24h" 
        ? time.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
        : time.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      
      labels.push(label);
      
      // Count incidents in this time bucket
      const bucketStart = new Date(time.getTime() - (timeRange === "24h" ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000));
      const bucketEnd = new Date(time.getTime());
      
      const count = incidents.filter(incident => {
        const incidentTime = new Date(incident.created_at);
        return incidentTime >= bucketStart && incidentTime < bucketEnd;
      }).length;
      
      data.push(count);
    }

    return { labels, data };
  };

  // Severity distribution
  const getSeverityDistribution = () => {
    const distribution = incidents.reduce((acc, incident) => {
      acc[incident.severity] = (acc[incident.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(distribution).map(([severity, count]) => ({
      name: SEV_LABELS[severity as keyof typeof SEV_LABELS],
      value: count,
      color: SEV_COLORS[severity as keyof typeof SEV_COLORS],
    }));
  };

  // MTTR analysis
  const getMTTRAnalysis = () => {
    const resolvedIncidents = incidents
      .filter(i => i.status === "resolved" || i.status === "closed")
      .filter(i => i.created_at && i.resolved_at);

    if (resolvedIncidents.length === 0) return null;

    const mttrs = resolvedIncidents.map(incident => {
      const created = new Date(incident.created_at);
      const resolved = new Date(incident.resolved_at!);
      return (resolved.getTime() - created.getTime()) / (1000 * 60); // minutes
    });

    const avgMTTR = mttrs.reduce((sum, mttr) => sum + mttr, 0) / mttrs.length;
    const maxMTTR = Math.max(...mttrs);
    const minMTTR = Math.min(...mttrs);

    return {
      average: Math.round(avgMTTR),
      max: Math.round(maxMTTR),
      min: Math.round(minMTTR),
      total: resolvedIncidents.length,
    };
  };

  const trends = getIncidentTrends();
  const severityData = getSeverityDistribution();
  const mttrData = getMTTRAnalysis();

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map(i => (
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
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex gap-2">
        {(["24h", "7d", "30d"] as const).map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              timeRange === range
                ? "bg-blue-500 text-white"
                : "bg-gray-100 hover:bg-gray-200"
            }`}
          >
            {range === "24h" ? "Last 24h" : range === "7d" ? "Last 7d" : "Last 30d"}
          </button>
        ))}
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Incidents</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{incidents.length}</div>
            <p className="text-xs text-muted-foreground">
              Across {timeRange}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active SEV1</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">
              {incidents.filter(i => i.severity === "SEV1" && i.status !== "closed").length}
            </div>
            <p className="text-xs text-muted-foreground">
              Requiring immediate attention
            </p>
          </CardContent>
        </Card>

        {mttrData && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg MTTR</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(mttrData.average)}</div>
              <p className="text-xs text-muted-foreground">
                Range: {formatDuration(mttrData.min)} - {formatDuration(mttrData.max)}
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Teams Involved</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(incidents.map(i => i.team_id)).size}
            </div>
            <p className="text-xs text-muted-foreground">
              Cross-team incidents
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Incident Trend Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Incident Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Severity Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Severity Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Incidents */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Incidents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {incidents.slice(0, 5).map(incident => (
              <div key={incident.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Badge 
                    variant={incident.severity === "SEV1" ? "destructive" : 
                            incident.severity === "SEV2" ? "warning" : "secondary"}
                  >
                    {incident.severity}
                  </Badge>
                  <div>
                    <div className="font-medium">{incident.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(incident.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <Badge 
                  variant={incident.status === "resolved" ? "outline" : "destructive"}
                >
                  {incident.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function formatDuration(minutes: number): string {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }
  return `${minutes}m`;
}