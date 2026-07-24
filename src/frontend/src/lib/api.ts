"use client";

// Prefer NEXT_PUBLIC_API_BASE_URL (prod); fall back to legacy names for local dev.
const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: "SEV1" | "SEV2" | "SEV3" | "SEV4";
  status: "open" | "investigating" | "mitigating" | "resolved" | "closed";
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
}

export interface LogEntry {
  id: string;
  service: string;
  level: string;
  message: string;
  timestamp: string;
}

export interface Alert {
  id: string;
  name: string;
  source: string;
  severity: string;
  message: string;
  service?: string;
  status: string;
  fired_at: string;
}

export interface AnalyticsSummary {
  total_incidents: number;
  open_incidents: number;
  resolved_incidents: number;
  mttr_minutes: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
}

export interface AnomalyResult {
  service: string;
  score: number;
  is_anomaly: boolean;
  threshold: number;
}

export interface AnomalySeriesEntry {
  service: string;
  score: number;
  is_anomaly: boolean;
  threshold: number;
}

export interface AnomalySeriesData {
  series: AnomalySeriesEntry[];
  risk_level: "low" | "medium" | "high";
  anomaly_alerts_count: number;
}
