12 — Frontend Architecture
Version: 1.0
Document Type: Frontend Architecture Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines the React frontend structure: folder organization, component hierarchy, state management strategy, routing, and how each screen maps to the personas (Chapter 3) and user stories (Chapter 4). It is the direct blueprint for scaffolding the React app with IBM Bob.

2. Project Structure
teampilot_frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── .env.example
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── router.jsx
│   │
│   ├── api/
│   │   ├── client.js              # Axios/fetch wrapper, JWT header injection
│   │   ├── authApi.js
│   │   ├── projectsApi.js
│   │   ├── tasksApi.js
│   │   ├── analyticsApi.js        # workload, risk
│   │   ├── recommendationsApi.js
│   │   ├── notificationsApi.js
│   │   └── chatApi.js
│   │
│   ├── auth/
│   │   ├── AuthContext.jsx        # current user, role, token
│   │   ├── ProtectedRoute.jsx     # role-based route guarding (mirrors BR-7.1)
│   │   └── LoginPage.jsx
│   │
│   ├── pages/
│   │   ├── Dashboard/
│   │   │   ├── PMDashboard.jsx        # US-7.1
│   │   │   └── ExecutiveDashboard.jsx # US-7.2
│   │   ├── Projects/
│   │   │   ├── ProjectList.jsx
│   │   │   ├── ProjectDetail.jsx
│   │   │   └── ProjectForm.jsx
│   │   ├── Tasks/
│   │   │   ├── TaskBoard.jsx          # Kanban-style, US-3.2–3.4
│   │   │   ├── TaskDetail.jsx
│   │   │   └── TaskForm.jsx
│   │   ├── Team/
│   │   │   ├── TeamList.jsx
│   │   │   └── MemberProfile.jsx      # skills, workload (FR-TEAM-003)
│   │   ├── Recommendations/
│   │   │   └── RecommendationInbox.jsx # US-6.1–6.3
│   │   ├── Chat/
│   │   │   └── ChatPanel.jsx           # US-9.1–9.2
│   │   └── Admin/
│   │       ├── UserManagement.jsx
│   │       └── TeamManagement.jsx
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.jsx, Modal.jsx, Badge.jsx, Spinner.jsx
│   │   ├── workload/
│   │   │   ├── WorkloadBar.jsx         # visual % + status color (BR-1.3)
│   │   │   └── WorkloadTrendChart.jsx
│   │   ├── risk/
│   │   │   ├── RiskScoreCard.jsx       # score + level badge (BR-4.2)
│   │   │   └── RiskExplanation.jsx     # renders explanation_text
│   │   ├── recommendations/
│   │   │   ├── RecommendationCard.jsx  # task, candidate, justification, confidence
│   │   │   └── AcceptRejectButtons.jsx
│   │   ├── tasks/
│   │   │   ├── TaskCard.jsx
│   │   │   └── BlockedTaskBadge.jsx
│   │   └── notifications/
│   │       └── NotificationBell.jsx
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useWorkload.js
│   │   ├── useRiskScore.js
│   │   └── useNotifications.js       # polling or WebSocket, TBD in §6
│   │
│   ├── context/
│   │   └── OrganizationContext.jsx    # current org/project scope
│   │
│   └── styles/
│       └── index.css                  # Tailwind entrypoint

3. Screen-to-Persona Mapping
ScreenPrimary PersonaRelated User StoriesPMDashboardProject Manager (Alice)US-7.1ExecutiveDashboardExecutive Manager (Grace)US-7.2, US-5.3, US-4.3TaskBoardTeam Member (David), PMUS-3.2–3.4RecommendationInboxProject Manager (Alice)US-6.1–6.3ChatPanelPM, ExecutiveUS-9.1–9.2TeamManagement / UserManagementAdministrator (Samuel)US-2.1–2.3, US-1.3
This table exists specifically to keep every screen traceable back to a real persona need — no screen is built "because it seems useful" without a documented justification (consistent with the Simplicity principle, Chapter 1 §9).

4. State Management Strategy
Given the MVP scope and July 31 deadline, we deliberately avoid introducing Redux or a heavy global state library. Instead:

Server state (projects, tasks, workload, risk, recommendations) is managed via lightweight data-fetching hooks (useWorkload, useRiskScore, etc.) built on top of the api/ layer, with simple local caching — not a full client-side cache library, to keep dependencies minimal.
Auth state (current user, role, JWT token) lives in AuthContext, since it's genuinely global and needed by ProtectedRoute everywhere.
UI-only state (modal open/closed, form inputs) stays local to components via useState.

Rationale: most of the "state" in this app is really server state that changes based on backend events (AI recalculation, other users' actions) — over-engineering a client-side store for data that must be refetched anyway adds complexity without benefit at this scale (NFR-MAINT-001 philosophy applied to frontend too).

5. Routing & Access Control
RouteComponentAllowed Roles/loginLoginPagePublic/dashboardPMDashboardProject Manager/dashboard/executiveExecutiveDashboardExecutive Manager/projects/:idProjectDetailPM (own projects), Executive (read-only)/projects/:id/tasksTaskBoardPM, Team Member (own tasks only)/recommendationsRecommendationInboxProject Manager/chatChatPanelPM, Executive/admin/usersUserManagementAdministrator/admin/teamsTeamManagementAdministrator
ProtectedRoute checks AuthContext's role against the route's allowed roles and redirects otherwise — a UX convenience only. The real enforcement is server-side (BR-7.1, NFR-SEC-003, Chapter 11 §6); frontend routing must never be treated as a security boundary.

6. Real-Time-ish Updates: Polling vs. WebSockets
For the MVP, useNotifications and dashboard refresh use polling (e.g., every 15–30 seconds) rather than WebSockets. WebSocket infrastructure (Django Channels) adds real deployment complexity that isn't justified for a hackathon-scale prototype with seed data — polling is sufficient to demonstrate the "proactive alert" behavior described in Chapter 1 (e.g., "Attention: risk 82%") without the added infrastructure risk this close to the deadline. This can be revisited post-submission (noted as a future improvement in Chapter 20).

7. Design System Notes

Tailwind CSS utility classes only, no custom CSS framework, to keep styling fast and consistent (per Chapter 1's stated stack).
Color coding for workload/risk status follows the exact bands defined in Chapter 5 (BR-1.3, BR-4.2) — e.g., Overloaded = orange, Critical risk = red — so the visual language matches the business rules 1:1, reinforcing NFR-EXP-001 (explainability) at the UI level, not just in text.


8. Component Reuse Example — RecommendationCard
This component is worth calling out because it directly renders the core AI value loop (UC-04) and will likely be the centerpiece of the demo video (Chapter 19):
jsx<RecommendationCard
  task={rec.task}
  currentAssignee={rec.currentAssignee}
  suggestedAssignee={rec.suggestedAssignee}
  justification={rec.justificationText}
  confidence={rec.confidenceLevel}   // HIGH / MEDIUM / LOW badge
  onAccept={() => acceptRecommendation(rec.id)}
  onReject={() => rejectRecommendation(rec.id)}
/>
It must visually surface the justification text prominently (NFR-USE-002) — not hide it behind a tooltip — since "explainable AI" is a core judging angle for the Wildcard theme.

End of Chapter 12