"use client";

// Prefer NEXT_PUBLIC_API_BASE_URL (prod); fall back to legacy names for local dev.
const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
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
    const detail = err?.detail;
    let message = `HTTP ${res.status}`;
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail)) {
      message = detail
        .map((d: unknown) =>
          typeof d === "string"
            ? d
            : d && typeof d === "object" && "msg" in d
              ? String((d as { msg: string }).msg)
              : JSON.stringify(d)
        )
        .join("; ");
    } else if (detail != null) {
      try {
        message = JSON.stringify(detail);
      } catch {
        message = String(detail);
      }
    }
    throw new Error(message);
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
  status: "detected" | "triaging" | "investigating" | "mitigating" | "resolved" | "closed";
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
  escalated_to?: string;
  detected_at?: string;
  team_id?: string;
  ai_summary?: string;
}

export interface TimelineEvent {
  id: string;
  incident_id: string;
  event_type: string;
  source: string;
  actor: string;
  ts: string;
  description?: string | null;
}

export interface IncidentTask {
  id: string;
  incident_id: string;
  title: string;
  status: string;
  priority: string;
  assigned_to?: string | null;
  created_at: string;
}

export interface SlaStatus {
  incident_id: string;
  title: string;
  severity: string;
  sla_minutes: number;
  remaining_minutes: number;
  breached: boolean;
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
  team_id?: string;
  source: string;
  alert_type?: string;
  title: string;
  description?: string | null;
  severity: string;
  is_resolved: boolean;
  fired_at: string;
  created_at?: string;
  /** Legacy aliases some older UI paths used */
  name?: string;
  message?: string;
  status?: string;
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
