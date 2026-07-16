10 — System Architecture
Version: 1.0
Document Type: System Architecture Overview
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document provides the high-level technical architecture of IA TeamPilot — how the frontend, backend, AI layer, and database interact. It is the bridge between the functional/data specifications (Chapters 6–9) and the implementation-level chapters that follow (Backend Architecture, Frontend Architecture, AI Architecture, REST API).

2. Architecture Style
IA TeamPilot follows a layered client-server architecture with a clearly isolated AI reasoning layer:
┌─────────────────────────────────────────┐
│              React Frontend               │
│   (Dashboard, Task Board, Chat, Alerts)    │
└───────────────────┬─────────────────────┘
                     │ HTTPS / REST (JSON)
                     ▼
┌─────────────────────────────────────────┐
│           Django REST API Layer            │
│  (Auth, Serializers, Views, Permissions)   │
└───────────────────┬─────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│           Business Logic Layer             │
│  (Services: Workload, Risk, Recommendation) │
└─────────┬───────────────────┬─────────────┘
          │                   │
          ▼                   ▼
┌───────────────────┐ ┌─────────────────────────┐
│   PostgreSQL DB    │ │      AI Engine Layer       │
│ (Users, Tasks,      │ │  LangChain Orchestration →  │
│  Projects, ...)     │ │  IBM Granite (via watsonx) │
└───────────────────┘ └─────────────────────────┘
Key principle: the Business Logic Layer computes deterministic values (workload %, risk sub-factors) directly from the database using the formulas in Chapter 5. The AI Engine Layer is invoked specifically to (a) generate natural-language justifications/explanations and (b) reason over ambiguous candidate selection when multiple valid options exist. This separation is what keeps the system explainable (NFR-EXP-001) rather than a black box — the numbers come from rules, the narrative comes from Granite.

3. Component Responsibilities
3.1 React Frontend

Renders dashboard, task board, recommendation review UI, chat panel.
Consumes the REST API exclusively — no direct database or AI access.
Manages local UI state; does not duplicate business logic (e.g., does not recompute workload client-side).

3.2 Django REST API Layer

Exposes versioned REST endpoints (Chapter 12).
Handles authentication (JWT), permission checks (BR-7.1), request validation.
Delegates all computation to the Business Logic Layer — views stay thin (NFR-MAINT-002).

3.3 Business Logic Layer (Services)

Implements Chapter 5's business rules as isolated Python service functions/classes.
Examples: WorkloadCalculationService, RiskScoreService, RecommendationService.
Decides when to call the AI Engine Layer (e.g., only when recommendation trigger conditions in BR-5.1 are met — not on every request, to control cost and latency).

3.4 AI Engine Layer

LangChain orchestrates the call: assembles a prompt from the Business Logic Layer's structured data, sends it to Granite via the watsonx endpoint, parses the structured response.
Never queries the database directly — it only receives what the Business Logic Layer explicitly passes to it, enforcing NFR-SEC-004 (no unnecessary sensitive data in prompts) and the access-scoping rule in UC-06.

3.5 PostgreSQL Database

Single source of truth for all entities defined in Chapter 9.
No business logic in the database itself (no complex triggers/stored procedures) — keeps logic centralized in Python for maintainability (NFR-MAINT-001).


4. Data Flow — Recommendation Generation (Reference Flow)
This is the system's core value loop (Chapter 1, introduced originally as Data → Analysis → Understanding → Decision → Suggestion → Action), traced through actual components:
1. Task status/assignment change occurs
        ↓ (Django signal or service call)
2. WorkloadCalculationService recalculates affected user's workload %
        ↓
3. If Overloaded/Critically Overloaded → RecommendationService checks
   trigger conditions (BR-5.1): candidate search in PostgreSQL
   (skill match, workload, blocked count — BR-5.3)
        ↓
4. If valid candidate(s) found → LangChain assembles prompt with:
   - overloaded user's tasks
   - candidate's profile and current load
   - business rule constraints
        ↓
5. Granite (via watsonx) returns structured output:
   { suggested_task, justification, confidence }
        ↓
6. RecommendationService validates/parses the AI response,
   saves it as a Recommendation record (status: PENDING)
        ↓
7. NotificationService creates a Notification for the PM
        ↓
8. React frontend polls/fetches and displays the pending recommendation
        ↓
9. PM accepts/rejects → Django applies the decision → loop closes

5. Why This Architecture Fits the Challenge

IBM Bob usage (NFR-COMP-001): IBM Bob is used throughout the development workflow (scaffolding Django apps, generating serializers/tests, reviewing service-layer code) — separate from the runtime AI (Granite/watsonx), which is what the deployed application uses. This distinction is intentional and will be made explicit in the README (Chapter 20) and demo video (Chapter 19), since judges evaluate technical execution partly on visible IBM Bob usage.
Explainability by design (NFR-EXP-001, NFR-EXP-002): because deterministic scores are computed in the Business Logic Layer and only the narrative is generated by Granite, a broken or hallucinated AI response can never silently corrupt a risk score — worst case, the explanation text falls back to a rule-based template (see NFR-REL-001).
Human-in-the-loop by architecture, not just UI convention: the Recommendation entity's PENDING/ACCEPTED/REJECTED state machine (Chapter 9, §11) makes it structurally impossible for a recommendation to change data without passing through an explicit PM action.


6. Environments
EnvironmentPurposeLocal developmentDjango runserver + React dev server (Vite), SQLite or local PostgreSQLDemo/submissionDeployed instance (exact host TBD in Chapter 19 — Deployment) with seed data loaded (Chapter 9, §14)

7. Technology Stack Summary
LayerTechnologyFrontendReact, Tailwind CSSBackendDjango, Django REST FrameworkDatabasePostgreSQLAI OrchestrationLangChainAI ModelIBM Granite via watsonxAuthJWT (djangorestframework-simplejwt or equivalent)Dev workflowIBM Bob (scaffolding, code review, test generation)

8. What This Chapter Deliberately Does Not Cover
Detailed backend app structure → Chapter 11 (Backend Architecture).
Component tree and screens → Chapter 12 (Frontend Architecture) — note: numbering will be finalized once all remaining chapters are drafted; see Chapter 20 for the final table of contents.
Exact prompt templates and LangChain chain design → Chapter 14 (AI Architecture).
Endpoint-by-endpoint REST spec → Chapter 15 (REST API).

End of Chapter 10