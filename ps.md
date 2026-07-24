Stakeholders: Yuvraj Rathod, Mitesh Chauhan

METIS
DEVELOPMENT CLUB

Web / App Development Track

Document Structure
Each problem statement in this document follows a consistent
structure to help participants plan, build, and evaluate their work
effectively:

• Problem Statement - A clear description of the real-world
problem being solved and the product to be built.
• Functional Requirements - Specific, scoped features broken
into categories; the minimum bar for evaluation.
• Brownie Point Features - Optional advanced features that can
elevate a submission from good to exceptional.

• Judging Criteria - A weighted rubric used by evaluators;
participants should optimise accordingly.
• Recommended Tech Stack - Suggested technologies;
participants are free to use any stack they prefer.

Rules & Guidelines

General
• Each participant or team must choose exactly one problem
statement to work on.
• The project duration is two months from the official start date.
• Projects must be submitted with a working deployment link
and a GitHub repository.
• The repository must include a README.md with setup
instructions and a brief project description.

Use of AI & Online Tools
• Use of AI coding assistants (GitHub Copilot, Cursor,
ChatGPT, Claude, etc.) is permitted.
• Use of open-source libraries, UI component libraries, and
third-party APIs is permitted.
• Participants are encouraged to write core logic themselves to
maximise learning.
• Copying entire projects from GitHub or online tutorials
without significant modification is not permitted.

Submission Requirements
• Live deployment URL (Vercel, Render, Railway, or
equivalent).
• Public GitHub repository with meaningful commit history -
judges will review commit logs.
• A brief write-up (1 - 2 pages) on technical decisions,
challenges faced, and what you would do with more time. ( You
may create WRITEUP.md in your GitHub repository)


SENTINEL - AI Native Engineering Operations

Platform(Hard)

Modern engineering teams lose significant time during
production incidents, deployment failures, and infrastructure
debugging. The toolchain is fragmented across Slack, Grafana,
Jira, GitHub, Notion, and monitoring dashboards, making
incident response reactive, slow, and manual-intensive.
Build SENTINEL: an AI-native DevOps and Incident
Management platform that serves as the single operational
workspace for engineering teams. The system should unify log
monitoring, deployment tracking, incident summarisation, task
assignment, and AI-assisted debugging into one coherent
product.

Functional Requirements

Team-based authentication with role-based access
control (RBAC)
Real-time incident dashboard with severity classification
and triage

Centralised log and alert monitoring interfaceAI-
generated incident summaries and root-cause

suggestions
GitHub / GitLab integration for deployment and commit
tracking
Service health monitoring with uptime visualisation
Integrated team communication channels per incident
Incident timeline generation with full event provenance
Task assignment, escalation, and SLA-aware workflow
Analytics dashboard for deployment stability and
incident frequency trends

Exceptional submissions may choose to implement any of the
following:
Conversational AI chatbot for querying logs and incidents in
natural language
Kubernetes and Docker deployment monitoring integration
Auto-generated postmortem reports from incident data
Voice-to-ticket incident creation via speech recognition
Predictive anomaly detection using machine learning
pipelines

Judging Criteria

Criterion Weight

System Design & Scalability 25%

Real-Time Features & Reliability 20%

AI Integration & Automation 20%

Security & Access Control 15%

UI/UX & Product Quality 10%

Deployment & DevOps Practices 10%

Recommended Tech Stack

Layer Recommended Technologies

Frontend React / Next.js with Tailwind CSS or Shadcn UI

Backend FastAPI (Python) or Node.js + Express

Database PostgreSQL (Supabase) or Firebase Firestore

Monitoring Prometheus / Grafana APIs for metrics ingestion

Real-Time WebSockets or Server-Sent Events (SSE)

Deployment Docker + Kubernetes (or Docker Compose for MVP)

AI Layer

OpenAI API, Gemini, or open-source LLMs (LLaMA,

Mistral)