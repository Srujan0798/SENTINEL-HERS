"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface Citation {
  incident_id?: string;
  log_id?: string;
  type: string;
  relevance: number;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

interface ChatPanelProps {
  incidentId?: string;
  teamId?: string;
}

export function ChatPanel({ incidentId, teamId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi! I'm SENTINEL AI. Ask me anything about your incidents, logs, or system health.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    // Try streaming first; fall back to regular chat on error
    try {
      const token = localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${base}/api/ai/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question: q, incident_id: incidentId, team_id: teamId }),
      });

      if (!res.ok || !res.body) throw new Error("Stream unavailable");

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.chunk) {
                accumulated += data.chunk;
                setMessages((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { role: "assistant", content: accumulated };
                  return next;
                });
              }
            } catch {
              /* skip */
            }
          }
        }
      }
    } catch {
      // Fallback to non-streaming
      try {
        const res = await api.post<{ answer: string; citations: Citation[] }>("/api/ai/chat", {
          question: q,
          incident_id: incidentId,
          team_id: teamId,
        });
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.answer, citations: res.citations },
        ]);
      } catch (e: unknown) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Error: ${e instanceof Error ? e.message : "AI unavailable"}` },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="flex flex-col h-[500px]">
      <CardHeader className="pb-2 border-b">
        <CardTitle className="text-sm flex items-center gap-2">
          AI Assistant
          <Badge variant="secondary" className="text-xs">RAG</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.citations.slice(0, 3).map((c, ci) => (
                    <span key={ci} className="text-xs opacity-70 bg-background rounded px-1">
                      {c.type} {Math.round(c.relevance * 100)}%
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-3 py-2 text-sm text-muted-foreground animate-pulse">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </CardContent>
      <div className="border-t p-3 flex gap-2">
        <input
          className="flex-1 text-sm border rounded px-3 py-2 bg-background focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="Ask about incidents, logs, anomalies…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          disabled={loading}
        />
        <Button size="sm" onClick={send} disabled={loading || !input.trim()}>
          Send
        </Button>
      </div>
    </Card>
  );
}
