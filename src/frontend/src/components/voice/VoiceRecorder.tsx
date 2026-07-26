"use client";

import React, { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface VoiceRecorderProps {
  teamId: string;
  onIncidentCreated?: (incident: Record<string, unknown>) => void;
  apiBase?: string;
}

type RecordingState = "idle" | "recording" | "uploading" | "processing" | "done" | "error" | "text-fallback" | "transcription-failed" | "confidence-low";

export function VoiceRecorder({
  teamId,
  onIncidentCreated,
  apiBase = "",
}: VoiceRecorderProps) {
  const [state, setState] = useState<RecordingState>("idle");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [incident, setIncident] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fallbackText, setFallbackText] = useState<string>("");
  const [fallbackTitle, setFallbackTitle] = useState<string>("");
  const [confidenceScore, setConfidenceScore] = useState<number | null>(null);
  const [detectedCommands, setDetectedCommands] = useState<string[]>([]);
  const [recordingDuration, setRecordingDuration] = useState<number>(0);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const authHeaders = (): Record<string, string> => {
    if (typeof window === "undefined") return {};
    const token =
      localStorage.getItem("access_token") || localStorage.getItem("sentinel_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const resolvedBase =
    apiBase ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";

  const detectVoiceCommands = useCallback((text: string): string[] => {
    const commands: string[] = [];
    const lowerText = text.toLowerCase();
    
    // Severity detection
    if (lowerText.includes("sev 1") || lowerText.includes("critical") || lowerText.includes("major")) {
      commands.push("SEV1");
    } else if (lowerText.includes("sev 2") || lowerText.includes("high")) {
      commands.push("SEV2");
    } else if (lowerText.includes("sev 3") || lowerText.includes("medium")) {
      commands.push("SEV3");
    } else if (lowerText.includes("sev 4") || lowerText.includes("low")) {
      commands.push("SEV4");
    }
    
    // Action detection
    if (lowerText.includes("create incident") || lowerText.includes("new incident")) {
      commands.push("CREATE_INCIDENT");
    }
    if (lowerText.includes("urgent") || lowerText.includes("asap")) {
      commands.push("URGENT");
    }
    
    return commands;
  }, []);

  const analyzeAudioQuality = useCallback(() => {
    if (!analyserRef.current) return 0;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
    return Math.min(100, Math.max(0, average / 2.55)); // Convert to 0-100 scale
  }, []);

  const uploadAudio = useCallback(async (blob: Blob) => {
    setState("uploading");
    try {
      const form = new FormData();
      form.append("file", blob, "recording.webm");

      const res = await fetch(
        `${resolvedBase}/api/voice/incidents?team_id=${teamId}&actor=voice`,
        { method: "POST", body: form, headers: authHeaders() }
      );

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail || `HTTP ${res.status}`;
        if (res.status === 502 || res.status === 500) {
          throw new Error(`Transcription service error: ${detail}`);
        }
        throw new Error(detail);
      }

      const data = await res.json();
      setIncident(data);
      setTranscript(data.metadata?.transcript ?? null);
      
      // Calculate confidence score and detect commands
      const confidence = data.metadata?.confidence ? Number(data.metadata.confidence) : 85;
      setConfidenceScore(confidence);
      
      const commands = detectVoiceCommands(data.metadata?.transcript || "");
      setDetectedCommands(commands);
      
      if (confidence < 70) {
        setState("confidence-low");
      } else {
        setState("done");
      }
      
      onIncidentCreated?.(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      if (message.includes("Transcription service error") || message.includes("Transcription rejected")) {
        setState("transcription-failed");
        setError(`Transcription failed: ${message}. You can try again or type your report instead.`);
      } else {
        setState("error");
        setError(message);
      }
    }
  }, [teamId, onIncidentCreated, resolvedBase, detectVoiceCommands]);

  const startRecording = useCallback(async () => {
    setError(null);
    setTranscript(null);
    setIncident(null);
    setConfidenceScore(null);
    setDetectedCommands([]);
    setRecordingDuration(0);
    setState("recording");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Setup audio analysis for visual feedback
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Start recording timer
      setRecordingDuration(0);
      timerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);

      // Audio level monitoring
      const monitorInterval = setInterval(() => {
        const level = analyzeAudioQuality();
        setAudioLevel(level);
      }, 100);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        clearInterval(timerRef.current!);
        clearInterval(monitorInterval);
        stream.getTracks().forEach((t) => t.stop());
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await uploadAudio(blob);
      };

      mediaRecorder.start();
    } catch {
      setState("text-fallback");
      setError("Microphone access denied. You can type your incident report below instead.");
    }
  }, [uploadAudio, analyzeAudioQuality]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    mediaRecorderRef.current?.stop();
  }, []);

  const submitTextFallback = async () => {
    if (!fallbackTitle.trim() && !fallbackText.trim()) {
      setError("Please enter at least a title or description.");
      return;
    }
    setState("uploading");
    setError(null);
    try {
      const res = await fetch(
        `${resolvedBase}/api/incidents?team_id=${teamId}&actor=voice-text`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({
            title: fallbackTitle.trim() || fallbackText.trim().slice(0, 100),
            description: fallbackText.trim(),
            severity: "SEV3",
          }),
        }
      );

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setIncident(data);
      setTranscript(fallbackText || fallbackTitle);
      setState("done");
      onIncidentCreated?.(data);
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Failed to create incident from text");
    }
  };

  const retryRecording = () => {
    setState("idle");
    setError(null);
    setTranscript(null);
    setIncident(null);
    setConfidenceScore(null);
    setDetectedCommands([]);
    setRecordingDuration(0);
    setAudioLevel(0);
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
              <Waveform audioLevel={audioLevel} />
            </div>
            <div className="text-center text-xs text-muted-foreground">
              Recording... speak now ({recordingDuration}s)
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Audio Quality</div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    audioLevel > 70 ? 'bg-green-500' : 
                    audioLevel > 40 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${audioLevel}%` }}
                />
              </div>
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
            <div className="flex items-center justify-center gap-2">
              <TranscribingSpinner />
              Processing audio &amp; creating incident...
            </div>
            <div className="text-xs mt-2 text-muted-foreground">
              Analyzing speech quality and detecting commands...
            </div>
          </div>
        )}

        {state === "processing" && (
          <div className="text-center text-sm text-muted-foreground py-4">
            <div className="flex items-center justify-center gap-2">
              <ConfidenceSpinner />
              Analyzing transcription confidence...
            </div>
          </div>
        )}

        {state === "done" && incident && (
          <div className="space-y-3 text-sm">
            <div className="font-medium">Incident Created Successfully</div>
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
            
            {confidenceScore !== null && (
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Confidence:</span>
                <div className="flex items-center gap-1">
                  <ConfidenceBar score={confidenceScore} />
                  <span className="text-xs font-medium">{confidenceScore}%</span>
                </div>
              </div>
            )}
            
            {detectedCommands.length > 0 && (
              <div>
                <span className="text-muted-foreground">Detected Commands:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {detectedCommands.map((cmd, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {cmd}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            
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
                setConfidenceScore(null);
                setDetectedCommands([]);
              }}
              variant="outline"
              className="w-full mt-2"
            >
              Record Another
            </Button>
          </div>
        )}

        {state === "confidence-low" && incident && (
          <div className="space-y-3 text-sm">
            <div className="font-medium text-yellow-600">Low Confidence Detected</div>
            <div className="text-sm text-muted-foreground">
              The transcription confidence is low ({confidenceScore}%). Please review and confirm or re-record.
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Title:</span>
                <span className="font-medium">{String(incident.title)}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Severity:</span>
                <Badge variant={severityColor[String(incident.severity)] as "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info"}>
                  {String(incident.severity)}
                </Badge>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  setState("done");
                  setConfidenceScore(85); // Assume user confirms
                }}
                className="flex-1"
              >
                Confirm Anyway
              </Button>
              <Button
                onClick={retryRecording}
                variant="outline"
                className="flex-1"
              >
                Re-record
              </Button>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="space-y-2">
            <div className="text-sm text-destructive">{error}</div>
            <Button onClick={retryRecording} variant="outline" className="w-full">
              Try Again
            </Button>
          </div>
        )}

        {state === "transcription-failed" && (
          <div className="space-y-3">
            <div className="text-sm text-destructive">{error}</div>
            <div className="space-y-2">
              <Button onClick={retryRecording} variant="outline" className="w-full">
                Try Microphone Again
              </Button>
              <Button
                onClick={() => setState("text-fallback")}
                variant="secondary"
                className="w-full"
              >
                Type Incident Instead
              </Button>
            </div>
          </div>
        )}

        {state === "text-fallback" && (
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              Microphone was denied. Enter your incident details below.
            </div>
            <div className="space-y-2">
              <Label htmlFor="fallback-title">Title</Label>
              <Input
                id="fallback-title"
                placeholder="Brief incident title"
                value={fallbackTitle}
                onChange={(e) => setFallbackTitle(e.target.value)}
              />
              <Label htmlFor="fallback-desc">Description</Label>
              <Textarea
                id="fallback-desc"
                placeholder="Describe what happened..."
                value={fallbackText}
                onChange={(e) => setFallbackText(e.target.value)}
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={submitTextFallback} className="flex-1" size="lg">
                Create Incident
              </Button>
              <Button onClick={retryRecording} variant="outline" className="flex-1">
                Try Mic Again
              </Button>
            </div>
            {error && <div className="text-sm text-destructive">{error}</div>}
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

function Waveform({ audioLevel = 0 }: { audioLevel?: number }) {
  return (
    <div className="flex items-end gap-1 h-8">
      {Array.from({ length: 12 }).map((_, i) => {
        const height = 8 + Math.random() * 20;
        const isActive = audioLevel > 30;
        return (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-100 ${
              isActive ? 'bg-[color:var(--sev1)]' : 'bg-gray-300'
            }`}
            style={{
              height: `${height}px`,
              animationDelay: `${i * 0.08}s`,
              opacity: isActive ? 1 : 0.5,
            }}
          />
        );
      })}
    </div>
  );
}

function ConfidenceBar({ score }: { score: number }) {
  const color = score >= 80 ? 'text-green-500' : score >= 60 ? 'text-yellow-500' : 'text-red-500';
  return (
    <div className={`w-16 h-2 bg-gray-200 rounded-full overflow-hidden ${color}`}>
      <div 
        className={`h-full ${color}`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function ConfidenceSpinner() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="animate-spin"
    >
      <circle cx="12" cy="12" r="10" className="opacity-25" />
      <path d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.364-6.364l-2.828 2.828M7.464 16.95l-2.828 2.828m12.728-12.728l-2.828 2.828M7.464 7.464l-2.828-2.828" />
    </svg>
  );
}



function TranscribingSpinner() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="animate-spin"
    >
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  );
}