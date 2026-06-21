"use client";

import React, { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface VoiceRecorderProps {
  teamId: string;
  onIncidentCreated?: (incident: Record<string, unknown>) => void;
  apiBase?: string;
}

type RecordingState = "idle" | "recording" | "uploading" | "done" | "error";

export function VoiceRecorder({
  teamId,
  onIncidentCreated,
  apiBase = "",
}: VoiceRecorderProps) {
  const [state, setState] = useState<RecordingState>("idle");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [incident, setIncident] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    setError(null);
    setTranscript(null);
    setIncident(null);
    setState("recording");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await uploadAudio(blob);
      };

      mediaRecorder.start();
    } catch {
      setState("error");
      setError("Microphone access denied");
    }
  }, []);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const uploadAudio = async (blob: Blob) => {
    setState("uploading");
    try {
      const form = new FormData();
      form.append("file", blob, "recording.webm");

      const res = await fetch(
        `${apiBase}/api/voice/incidents?team_id=${teamId}&actor=voice`,
        { method: "POST", body: form }
      );

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setIncident(data);
      setTranscript(data.metadata?.transcript ?? null);
      setState("done");
      onIncidentCreated?.(data);
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  const severityColor: Record<string, string> = {
    SEV1: "destructive",
    SEV2: "warning",
    SEV3: "info",
    SEV4: "secondary",
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MicIcon active={state === "recording"} />
          Voice-to-Ticket
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {state === "idle" && (
          <Button onClick={startRecording} className="w-full" size="lg">
            Start Recording
          </Button>
        )}

        {state === "recording" && (
          <div className="space-y-3">
            <div className="flex justify-center">
              <Waveform />
            </div>
            <Button
              onClick={stopRecording}
              variant="destructive"
              className="w-full"
              size="lg"
            >
              Stop &amp; Submit
            </Button>
          </div>
        )}

        {state === "uploading" && (
          <div className="text-center text-sm text-muted-foreground py-4">
            Transcribing &amp; creating incident...
          </div>
        )}

        {state === "done" && incident && (
          <div className="space-y-2 text-sm">
            <div className="font-medium">Incident Created</div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">ID:</span>
              <code className="text-xs">{String(incident.id)}</code>
            </div>
            <div>
              <span className="text-muted-foreground">Title:</span>{" "}
              {String(incident.title)}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Severity:</span>
              <Badge variant={severityColor[String(incident.severity)] as "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info"}>
                {String(incident.severity)}
              </Badge>
            </div>
            {transcript && (
              <div>
                <span className="text-muted-foreground">Transcript:</span>{" "}
                <span className="italic">{transcript}</span>
              </div>
            )}
            <Button
              onClick={() => {
                setState("idle");
                setIncident(null);
                setTranscript(null);
              }}
              variant="outline"
              className="w-full mt-2"
            >
              Record Another
            </Button>
          </div>
        )}

        {state === "error" && (
          <div className="space-y-2">
            <div className="text-sm text-destructive">{error}</div>
            <Button
              onClick={() => setState("idle")}
              variant="outline"
              className="w-full"
            >
              Try Again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MicIcon({ active }: { active: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill={active ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth={2}
      className={`h-5 w-5 ${active ? "text-red-500 animate-pulse" : ""}`}
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
    </svg>
  );
}

function Waveform() {
  return (
    <div className="flex items-end gap-1 h-8">
      {Array.from({ length: 12 }).map((_, i) => (
        <div
          key={i}
          className="w-1 bg-red-500 rounded-full animate-pulse"
          style={{
            height: `${8 + Math.random() * 20}px`,
            animationDelay: `${i * 0.08}s`,
          }}
        />
      ))}
    </div>
  );
}
