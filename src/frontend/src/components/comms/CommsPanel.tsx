"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

interface Message {
  id: string;
  team_id: string;
  channel_id: string;
  incident_id: string;
  author_id: string | null;
  author_name: string | null;
  author_type: "user" | "ai" | "system";
  body: string;
  mentions: Array<{ user_id: string; user_name?: string | null }>;
  metadata: Record<string, unknown>;
  created_at: string;
  edited_at: string | null;
}

interface Channel {
  id: string;
  team_id: string;
  incident_id: string;
  name: string;
  topic: string | null;
  is_archived: boolean;
  member_count: number;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface CommsPanelProps {
  incidentId: string;
  teamId?: string;
  /** Current viewer id (used to highlight own messages). */
  currentUserId?: string;
  /** If true the panel renders expanded; collapsed shows a button to open it. */
  defaultOpen?: boolean;
  /** Show the toggle button. Defaults to true. */
  showToggle?: boolean;
  /** Optional override for the SSE endpoint (mainly for testing). */
  sseUrl?: string;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("sentinel_token")
  );
}

async function apiGet<T>(path: string): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function formatTime(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function renderBody(body: string, mentions: Message["mentions"]): React.ReactNode {
  // Highlight @mentions in the rendered text.
  if (!mentions || mentions.length === 0) return body;
  const parts: React.ReactNode[] = [];
  let remaining = body;
  let key = 0;
  for (const m of mentions) {
    const token = m.user_name || m.user_id;
    if (!token) continue;
    const at = `@${token}`;
    const idx = remaining.indexOf(at);
    if (idx === -1) continue;
    if (idx > 0) parts.push(remaining.slice(0, idx));
    parts.push(
      <span
        key={`m-${key++}`}
        className="font-semibold text-primary"
        title={`Mention: ${token}`}
      >
        {at}
      </span>
    );
    remaining = remaining.slice(idx + at.length);
  }
  if (remaining) parts.push(remaining);
  return <>{parts}</>;
}

export function CommsPanel({
  incidentId,
  currentUserId,
  defaultOpen = true,
  showToggle = true,
  sseUrl,
}: CommsPanelProps) {
  const [open, setOpen] = useState<boolean>(defaultOpen);
  const [channel, setChannel] = useState<Channel | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [autocomplete, setAutocomplete] = useState<{
    open: boolean;
    query: string;
    idx: number;
  }>({ open: false, query: "", idx: 0 });
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  // Load channel first (auto-creates), then messages. Parallel load races a 404
  // when the incident has no channel yet (seeded SEV1 before comms hook).
  useEffect(() => {
    if (!open || !incidentId) return;
    let cancelled = false;
    setError(null);
    setLoading(true);
    (async () => {
      try {
        const ch = await apiGet<Channel>(`/api/incidents/${incidentId}/channel`);
        if (cancelled) return;
        setChannel(ch);
        const msgs = await apiGet<{ data: Message[]; pagination: Pagination }>(
          `/api/incidents/${incidentId}/messages?page=1&per_page=50`
        );
        if (cancelled) return;
        setMessages(msgs.data);
        setPagination(msgs.pagination);
        setPage(1);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load channel");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, incidentId]);

  // Load team members for @mention autocomplete.
  useEffect(() => {
    if (!open || !incidentId) return;
    apiGet<{ data: TeamMember[] }>(`/api/incidents/${incidentId}/team-members`)
      .then((r) => setTeamMembers(r.data || []))
      .catch(() => setTeamMembers([]));
  }, [open, incidentId]);

  // Subscribe to SSE for live channel.message events.
  useEffect(() => {
    if (!open) return;
    const token = getToken();
    if (!token) return; // can't subscribe without a token
    const url =
      sseUrl || `${API_BASE}/api/realtime/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;
    es.addEventListener("connected", () => setConnected(true));
    const onChannelMessage = (e: MessageEvent) => {
      try {
        const evt = JSON.parse(e.data);
        if (evt.event_type !== "channel.message") return;
        const m = evt.payload as Message;
        if (m.incident_id !== incidentId) return;
        setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]));
      } catch {
        /* ignore */
      }
    };
    es.addEventListener("channel.message", onChannelMessage as EventListener);
    es.onerror = () => setConnected(false);
    return () => {
      es.close();
      esRef.current = null;
      setConnected(false);
    };
  }, [open, incidentId, sseUrl]);

  // Autoscroll on new message.
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages.length]);

  // Detect @mention autocomplete from the textarea.
  useEffect(() => {
    const text = draft;
    const cursor = inputRef.current?.selectionStart ?? text.length;
    const before = text.slice(0, cursor);
    const at = before.match(/(^|\s)@([a-zA-Z0-9_.\-]{0,64})$/);
    if (at) {
      setAutocomplete({ open: true, query: at[2], idx: 0 });
    } else {
      setAutocomplete((a) => (a.open ? { open: false, query: "", idx: 0 } : a));
    }
  }, [draft]);

  const filteredMembers = useMemo(() => {
    if (!autocomplete.open) return [];
    const q = autocomplete.query.toLowerCase();
    if (!q) return teamMembers.slice(0, 6);
    return teamMembers
      .filter(
        (m) =>
          m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
      )
      .slice(0, 6);
  }, [autocomplete, teamMembers]);

  const insertMention = useCallback(
    (member: TeamMember) => {
      const text = draft;
      const cursor = inputRef.current?.selectionStart ?? text.length;
      const before = text.slice(0, cursor);
      const after = text.slice(cursor);
      const m = before.match(/(^|\s)@([a-zA-Z0-9_.\-]{0,64})$/);
      if (!m) return;
      const replacement = `${m[1]}@${member.name} `;
      const newText = before.replace(/(^|\s)@([a-zA-Z0-9_.\-]{0,64})$/, replacement) + after;
      setDraft(newText);
      setAutocomplete({ open: false, query: "", idx: 0 });
      setTimeout(() => inputRef.current?.focus(), 0);
    },
    [draft]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (autocomplete.open && filteredMembers.length > 0) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setAutocomplete((a) => ({
            ...a,
            idx: Math.min(a.idx + 1, filteredMembers.length - 1),
          }));
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setAutocomplete((a) => ({ ...a, idx: Math.max(a.idx - 1, 0) }));
          return;
        }
        if (e.key === "Enter" || e.key === "Tab") {
          e.preventDefault();
          insertMention(filteredMembers[autocomplete.idx]);
          return;
        }
        if (e.key === "Escape") {
          setAutocomplete({ open: false, query: "", idx: 0 });
          return;
        }
      }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void sendMessage();
      }
    },
    [autocomplete, filteredMembers, insertMention]
  );

  const sendMessage = useCallback(async () => {
    const body = draft.trim();
    if (!body) return;
    setError(null);
    try {
      const m = await apiPost<Message>(`/api/incidents/${incidentId}/messages`, {
        body,
        author_type: "user",
        metadata: {},
      });
      setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]));
      setDraft("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send");
    }
  }, [draft, incidentId]);

  const loadMore = useCallback(async () => {
    if (!pagination || page >= pagination.total_pages) return;
    const next = page + 1;
    try {
      const msgs = await apiGet<{ data: Message[]; pagination: Pagination }>(
        `/api/incidents/${incidentId}/messages?page=${next}&per_page=50`
      );
      setMessages((prev) => [...msgs.data, ...prev]);
      setPagination(msgs.pagination);
      setPage(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load more");
    }
  }, [incidentId, page, pagination]);

  if (!open && showToggle) {
    return (
      <div className="fixed right-4 top-24 z-40">
        <Button onClick={() => setOpen(true)} size="sm" variant="default">
          💬 Open Comms
        </Button>
      </div>
    );
  }

  if (!open) return null;

  return (
    <Card className="w-full lg:w-96 flex flex-col h-[600px] shadow-lg border-l-4 border-l-primary">
      <CardHeader className="pb-2 flex flex-row items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <CardTitle className="text-base flex items-center gap-2">
            <span>💬 Incident Comms</span>
            {connected ? (
              <Badge variant="success" className="text-[10px]">live</Badge>
            ) : (
              <Badge variant="secondary" className="text-[10px]">offline</Badge>
            )}
          </CardTitle>
          {channel && (
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {channel.name} · {channel.message_count} messages
            </p>
          )}
        </div>
        {showToggle && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setOpen(false)}
            aria-label="Collapse comms panel"
          >
            ✕
          </Button>
        )}
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-2 p-3 pt-0 min-h-0">
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 px-2 py-1 rounded">
            {error}
          </div>
        )}

        <div
          ref={listRef}
          className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-0"
        >
          {pagination && page < pagination.total_pages && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full"
              onClick={loadMore}
            >
              Load earlier ({pagination.total - messages.length} more)
            </Button>
          )}

          {loading && (
            <p className="text-xs text-muted-foreground text-center py-4">
              Loading…
            </p>
          )}

          {!loading && messages.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-6">
              No messages yet. Start the conversation.
            </p>
          )}

          {messages.map((m) => {
            const isAi = m.author_type === "ai";
            const isSystem = m.author_type === "system";
            const isMine =
              currentUserId && m.author_id && m.author_id === currentUserId;
            return (
              <div
                key={m.id}
                className={`text-sm rounded-md px-2 py-1.5 ${
                  isAi
                    ? "bg-[color:var(--phosphor)]/10 border border-[color:var(--phosphor)]/30"
                    : isSystem
                    ? "bg-muted text-muted-foreground italic"
                    : isMine
                    ? "bg-primary/10"
                    : "bg-muted/40"
                }`}
              >
                <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {m.author_name || (isAi ? "SENTINEL AI" : "anon")}
                  </span>
                  {isAi && (
                    <Badge variant="info" className="text-[10px]">
                      AI
                    </Badge>
                  )}
                  {isSystem && (
                    <Badge variant="secondary" className="text-[10px]">
                      system
                    </Badge>
                  )}
                  <span className="ml-auto">{formatTime(m.created_at)}</span>
                </div>
                <div className="whitespace-pre-wrap break-words mt-0.5">
                  {renderBody(m.body, m.mentions)}
                </div>
              </div>
            );
          })}
        </div>

        <div className="relative border-t pt-2">
          {autocomplete.open && filteredMembers.length > 0 && (
            <div className="absolute bottom-full left-0 right-0 mb-1 bg-popover border rounded shadow-md max-h-40 overflow-y-auto z-10">
              {filteredMembers.map((m, i) => (
                <button
                  key={m.id}
                  onClick={() => insertMention(m)}
                  className={`w-full text-left text-xs px-2 py-1 hover:bg-accent ${
                    i === autocomplete.idx ? "bg-accent" : ""
                  }`}
                >
                  <span className="font-medium">@{m.name}</span>{" "}
                  <span className="text-muted-foreground">— {m.email}</span>
                </button>
              ))}
            </div>
          )}
          <textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message… use @ to mention a teammate"
            rows={2}
            className="w-full text-sm border rounded-md px-2 py-1.5 resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            data-testid="comms-input"
          />
          <div className="flex items-center justify-between mt-1">
            <span className="text-[10px] text-muted-foreground">
              Enter to send · Shift+Enter for newline
            </span>
            <Button size="sm" onClick={sendMessage} disabled={!draft.trim()}>
              Send
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default CommsPanel;
