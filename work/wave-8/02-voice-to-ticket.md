# TASK — wave-8 / 02-voice-to-ticket

## Goal
Voice-to-ticket: SRE speaks a description of an incident, the system transcribes it
(Wisper API or local faster-whisper), parses the text via LLM into a structured
incident, and creates it. The killer demo moment.

## Context
- Wave: 8. Uses existing AI layer (`src/backend/ai/provider.py`).
- Audio input via multipart/form-data upload (POST /api/voice/incidents).
- Falls back to mock transcription when no API key (deterministic, for tests).

## Write-set (ONLY these)
- src/backend/voice/
- src/frontend/src/components/voice/
- tests/integration/test_voice.py

## Forbid-set
- src/backend/ai/** (existing AI layer), src/frontend/src/app/dashboard/**

## Blast radius
r1.

## Steps
1. `voice/transcribe.py`: `class Transcriber` abstract with two impls:
   - `OpenAITranscriber` (uses openai.audio.transcriptions.create with whisper-1)
   - `MockTranscriber` (returns canned text from a fixed WAV — for tests)
   Factory reads `TRANSCRIBER_PROVIDER` env.
2. `voice/parse.py`: takes transcribed text + AI provider, returns:
   ```python
   class ParsedIncident:
       title: str
       description: str
       severity: Literal["SEV1","SEV2","SEV3","SEV4"]
       affected_services: list[str]
   ```
   Uses Claude/Gemini with system prompt: "Parse this SRE voice note into a structured incident."
3. `voice/routes.py`:
   - `POST /api/voice/incidents` — accepts multipart file (.wav/.mp3/.webm).
     Pipeline: transcribe → parse → create incident via existing service.
     Returns 201 with the new incident ID.
   - `GET /api/voice/sample` — returns a small pre-generated .wav for demo.
4. `<VoiceRecorder>` (frontend): button + waveform animation while recording.
   On stop: POST to `/api/voice/incidents`, show the new incident.
5. `tests/integration/test_voice.py` with `MockTranscriber` (no real audio needed).
   Tests: upload → transcribe → parse → incident created.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_voice.py -v
# Mock transcription, no real API needed
# Expected: 201 with valid incident_id, severity in [SEV1..SEV4]
```

## Report to
`work/reports/wave-8/02-voice-to-ticket.report.md`
