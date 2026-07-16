
markdown# Project: IA TeamPilot

## What This Is
AI-powered team coordination assistant for the IBM AI Builders
Challenge 2026 — Wildcard Challenge: "Build Intelligent Systems
for the Future of Work."

Full specification lives in `/docs` (18 chapters). This file is a
condensed entry point for AI assistants (Bob, Claude, ChatGPT) —
read this first, then consult the specific `/docs` chapter for the
task at hand. Never invent architecture or business rules not
documented in `/docs` — if something is missing, ask, don't assume.

## One-Sentence Pitch
IA TeamPilot continuously analyzes team workload and project data,
detects risks before they become delays, and recommends task
redistribution with a clear justification — the AI proposes, the
human decides.

## Problem It Solves
Project managers discover overload, blockers, and delays reactively
(during standups, or after a deadline is missed) because existing
tools (Jira, Trello, Asana) store data but don't interpret it. See
`docs/02_Problem_Analysis.md` for the full analysis.

## Users
| Role | Primary Need |
|---|---|
| Project Manager | Review and act on AI recommendations |
| Team Member | See tasks, report blockers |
| Executive Manager | Cross-project risk visibility |
| Administrator | Manage users, teams, skills |

Full personas: `docs/03_Personas.md`

## Core Value Loop
Data → Analysis → Risk Detection → Recommendation → Human Decision → Action
The AI never applies a change automatically. Every recommendation
requires explicit Project Manager approval. This is a hard
architectural constraint, not a UX preference — see
`docs/05_Business_Rules.md` (BR-5.5).

## MVP Scope (what to build)
Included: authentication/roles, team & skills management, project &
task management, workload analysis, risk prediction, AI
recommendations, dashboard, notifications, AI chat assistant.

Excluded: payroll, accounting, HR recruitment, video conferencing,
file storage, ERP, CRM.

Full scope: `docs/01_Project_Vision.md` (§14).

## Deadline
July 31, 2026 — IBM AI Builders Challenge Wildcard submission.

## Where to Look for What

| Need to know... | Read... |
|---|---|
| Product vision, MVP scope | `docs/01_Project_Vision.md` |
| Why this problem matters | `docs/02_Problem_Analysis.md` |
| Who the users are | `docs/03_Personas.md` |
| What to build (feature-level) | `docs/04_User_Stories.md`, `docs/06_Functional_Requirements.md` |
| Exact formulas & thresholds | `docs/05_Business_Rules.md` |
| Step-by-step system behavior | `docs/08_Use_Cases.md` |
| Database schema | `docs/09_Database_Design.md` |
| How layers connect | `docs/10_System_Architecture.md` |
| Django app structure | `docs/11_Backend_Architecture.md` |
| React structure | `docs/12_Frontend_Architecture.md` |
| AI prompts & chains | `docs/13_AI_Architecture.md` |
| Every endpoint | `docs/14_REST_API.md` |
| Screen layouts | `docs/15_UI_UX.md` |
| Test strategy | `docs/16_Testing.md` |
| Deployment steps | `docs/17_Deployment.md` |
| Repo/README structure | `docs/18_GitHub_Submission.md` |

Also see `.ai/architecture.md`, `.ai/tech-stack.md`,
`.ai/coding-rules.md`, `.ai/business-rules.md` for the condensed,
always-relevant versions of the above.

## Non-Negotiable Constraints
- No AI-driven change to data without explicit human approval (BR-5.5).
- Deterministic values (workload %, risk score) are computed by
  Python business rules, never by the AI model — the AI only
  generates the natural-language explanation. See
  `docs/13_AI_Architecture.md` §2.
- If the AI service is unavailable, the system must degrade
  gracefully (fallback templates), never crash or block core CRUD.