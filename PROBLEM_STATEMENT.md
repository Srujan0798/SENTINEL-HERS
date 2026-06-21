# Problem Statement: SENTINEL — AI-Native Engineering Operations Platform

## Overview
Modern engineering teams lose significant time during production incidents, deployment failures, and infrastructure debugging. The toolchain is fragmented across Slack, Grafana, Jira, GitHub, Notion, and monitoring dashboards, making incident response reactive, slow, and manual-intensive.

**Build SENTINEL:** an AI-native DevOps and Incident Management platform that serves as the single operational workspace for engineering teams. The system should unify log monitoring, deployment tracking, incident summarisation, task assignment, and AI-assisted debugging into one coherent product.

## Functional Requirements
- Team-based authentication with role-based access control (RBAC)
- Real-time incident dashboard with severity classification and triage
- Centralised log and alert monitoring interface
- AI-generated incident summaries and root-cause suggestions
- GitHub / GitLab integration for deployment and commit tracking
- Service health monitoring with uptime visualisation
- Integrated team communication channels per incident
- Incident timeline generation with full event provenance
- Task assignment, escalation, and SLA-aware workflow
- Analytics dashboard for deployment stability and incident frequency trends

## Exceptional Features (Optional but Recommended)
- Conversational AI chatbot for querying logs and incidents in natural language
- Kubernetes and Docker deployment monitoring integration
- Auto-generated postmortem reports from incident data
- Voice-to-ticket incident creation via speech recognition
- Predictive anomaly detection using machine learning pipelines

## Judging Criteria

| Criterion | Weight |
|-----------|--------|
| System Design & Scalability | 25% |
| Real-Time Features & Reliability | 20% |
| AI Integration & Automation | 20% |
| Security & Access Control | 15% |
| UI/UX & Product Quality | 10% |
| Deployment & DevOps Practices | 10% |

## Recommended Tech Stack

| Layer | Recommended Technologies |
|-------|-------------------------|
| Frontend | React / Next.js with Tailwind CSS or Shadcn UI |
| Backend | FastAPI (Python) or Node.js + Express |
| Database | PostgreSQL (Supabase) or Firebase Firestore |
| Monitoring | Prometheus / Grafana APIs for metrics ingestion |
| Real-Time | WebSockets or Server-Sent Events (SSE) |
| Deployment | Docker + Kubernetes (or Docker Compose for MVP) |
| AI Layer | OpenAI API, Gemini, or open-source LLMs (LLaMA, Mistral) |