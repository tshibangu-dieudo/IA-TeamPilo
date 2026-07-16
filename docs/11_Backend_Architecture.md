11 — Backend Architecture
Version: 1.0
Document Type: Backend Architecture Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document details the Django backend structure: app organization, service layer design, models-to-app mapping, background tasks, and testing strategy. It turns Chapter 9 (Database) and Chapter 10 (System Architecture) into a concrete, buildable Django project structure — the direct blueprint for IBM Bob to scaffold from.

2. Project Structure
teampilot_backend/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   │   ├── models.py        # User, UserSkill
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   ├── teams/
│   │   ├── models.py        # Team, TeamMembership, Skill
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   │
│   ├── projects/
│   │   ├── models.py        # Project
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   │
│   ├── tasks/
│   │   ├── models.py        # Task, TaskSkill, TaskDependency, TaskStatusHistory
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py      # dependency validation (BR-8.1), status transitions
│   │   ├── signals.py       # triggers workload/risk recalculation on save
│   │   └── tests/
│   │
│   ├── analytics/
│   │   ├── models.py        # WorkloadSnapshot, RiskScore
│   │   ├── services/
│   │   │   ├── workload_service.py     # BR-1.1–1.4
│   │   │   └── risk_service.py         # BR-4.1–4.3
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   │
│   ├── recommendations/
│   │   ├── models.py        # Recommendation
│   │   ├── services.py      # trigger logic (BR-5.1–5.5), candidate ranking
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   │
│   ├── notifications/
│   │   ├── models.py        # Notification
│   │   ├── services.py      # throttling logic (BR-6.2)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests/
│   │
│   └── chat/
│       ├── services.py      # context assembly, scoping (BR-7.1)
│       ├── serializers.py
│       ├── views.py
│       └── tests/
│
├── ai_engine/
│   ├── langchain_client.py   # watsonx/Granite connection setup
│   ├── prompts/               # versioned prompt templates (NFR-MAINT-003)
│   │   ├── recommendation_prompt.txt
│   │   ├── risk_explanation_prompt.txt
│   │   └── chat_prompt.txt
│   ├── chains.py              # LangChain chain definitions
│   └── tests/
│
└── seed/
    └── generate_seed_data.py  # Chapter 9 §14 seed dataset generator

3. App Responsibility Summary
AppOwnsDoes NOT OwnaccountsAuth, roles, users, skills-per-userTeam membership logicteamsTeams, team membership, skill catalogUser authenticationprojectsProject CRUD, ownershipTask-level logictasksTask CRUD, dependencies, status historyWorkload/risk computation (delegates to analytics)analyticsWorkload & risk score computation and storageRecommendation generation (delegates to recommendations)recommendationsRecommendation trigger, candidate ranking, accept/reject logicAI prompt construction (delegates to ai_engine)notificationsNotification creation, throttling, read stateBusiness logic that triggers notifications (called by other apps)chatChat request handling, scopingAI prompt construction (delegates to ai_engine)ai_engineLangChain orchestration, Granite calls, prompt templatesAny Django model or business rule — stays framework-agnostic
Design rationale: ai_engine is deliberately decoupled from Django models. It receives plain Python dicts from calling services and returns plain Python dicts back. This keeps NFR-MAINT-003 real (prompts can be iterated on without touching business logic) and makes ai_engine independently testable/mockable.

4. Service Layer Pattern
Every business rule from Chapter 5 lives in a services.py (or services/ package for larger apps), never directly in a view. Example shape:
python# apps/analytics/services/workload_service.py

class WorkloadCalculationService:
    def calculate_workload_percentage(self, user, sprint_window) -> Decimal:
        # Implements BR-1.2
        ...

    def classify_status(self, workload_percentage) -> str:
        # Implements BR-1.3
        ...

    def recalculate_for_user(self, user):
        # Orchestrates the above, saves a WorkloadSnapshot,
        # triggers alert check (BR-1.4) via notifications app
        ...
Views call services; services call the database and, where needed, ai_engine. This mirrors NFR-MAINT-002 directly.

5. Triggering Recalculation (Signals vs. Explicit Calls)
Given the traceability required by NFR-EXP-001, we use explicit service calls from views, not implicit Django signals, for the primary recalculation path (task create/update/reassign → WorkloadCalculationService.recalculate_for_user() → RiskScoreService.recalculate_for_project()). This keeps the trigger chain visible in the view/service code rather than hidden in a signal handler, which matters when a judge or teammate is reading the code to understand why something happened.
The one exception is the scheduled 6-hour recalculation (BR-4.3), which runs via a periodic task (Celery beat, or a simpler management command + cron for MVP scope, to avoid adding Celery/Redis infrastructure complexity under the July 31 deadline unless needed).

6. Permissions Layer
Each app defines DRF permission classes implementing the role-based rules from BR-7.1:
python# apps/projects/permissions.py

class IsProjectManagerOwner(BasePermission):
    # PM can only act on projects they own

class IsExecutiveReadOnly(BasePermission):
    # Executive Managers get read-only cross-project access
Permission checks happen at the DRF view level (permission_classes), enforced server-side per NFR-SEC-003 — never trusted from the frontend alone.

7. Testing Strategy (Backend)
Test TypeScopeToolingUnit testsService functions (workload formula, risk formula, recommendation ranking) — pure logic, no AI callspytest / Django TestCaseIntegration testsAPI endpoints with DRF test client, using seed-like fixturesDjango REST Framework test clientAI mockingai_engine calls mocked in tests outside ai_engine/tests/ itself, so business logic tests don't depend on live watsonx availability or costunittest.mock
This aligns with Chapter 18 (Testing Strategy), detailed later, but the mocking boundary is defined here because it directly shapes how ai_engine was isolated in Section 3.

8. Configuration & Secrets
Per NFR-SEC-005, all sensitive values are loaded from environment variables via .env (not committed), with .env.example documenting required keys:
DATABASE_URL=
SECRET_KEY=
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=

End of Chapter 11