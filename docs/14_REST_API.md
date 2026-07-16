14 — REST API Specification
Version: 1.0
Document Type: REST API Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document lists every REST endpoint IA TeamPilot exposes: method, URL, request payload, response shape, and permissions. This is the direct spec to hand IBM Bob when generating Django REST Framework serializers and views — each endpoint traces back to an FR from Chapter 6.

2. Conventions

Base path: /api/v1/
Auth: Authorization: Bearer <JWT> header on all endpoints except /auth/register and /auth/login.
Standard error shape: { "error": "string", "details": {} }
Pagination: ?page=&page_size= on all list endpoints, default page_size = 20.
Timestamps: ISO 8601 UTC.


3. Auth & Accounts (/api/v1/auth/, /api/v1/users/)
MethodEndpointDescriptionPermissionsFRPOST/auth/registerRegister a new userPublicFR-AUTH-001–003POST/auth/loginLogin, returns JWTPublicFR-AUTH-004POST/auth/refreshRefresh JWT tokenAuthenticatedFR-AUTH-005GET/users/meCurrent user profileAuthenticated—GET/users/List users in organizationAdminFR-TEAM-002PATCH/users/{id}/roleChange a user's roleAdminFR-AUTH-007PATCH/users/{id}/capacitySet weekly capacity hoursAdminFR-TEAM-006POST/users/{id}/skillsAssign skill(s) to a userAdminFR-TEAM-003DELETE/users/{id}/skills/{skill_id}Remove a skill from a userAdminFR-TEAM-003
Example — POST /auth/login
Request: { "email": "alice@teampilot.io", "password": "••••••••" }
Response: { "access_token": "eyJ...", "user": { "id": "uuid", "role": "PROJECT_MANAGER", "full_name": "Alice Kamana" } }

4. Teams & Skills (/api/v1/teams/, /api/v1/skills/)
MethodEndpointDescriptionPermissionsFRGET/teams/List teamsAuthenticated (scoped)—POST/teams/Create a teamAdminFR-TEAM-001POST/teams/{id}/membersAdd member to teamAdminFR-TEAM-002DELETE/teams/{id}/members/{user_id}Remove member from teamAdminFR-TEAM-002GET/skills/List all skills (predefined + custom)AuthenticatedFR-TEAM-004POST/skills/Create a custom skillAdminFR-TEAM-004GET/teams/{id}/data-completeness% of members with skills assignedAdminFR-TEAM-005

5. Projects (/api/v1/projects/)
MethodEndpointDescriptionPermissionsFRGET/projects/List projects (scoped: PM sees own, Executive sees all, Team Member sees their team's)Authenticated (scoped, BR-7.1)—POST/projects/Create a projectProject ManagerFR-PROJ-001, FR-PROJ-002GET/projects/{id}/Project detailScoped—PATCH/projects/{id}/Edit projectPM (owner only)FR-PROJ-003PATCH/projects/{id}/archiveArchive projectPM (owner only)FR-PROJ-003
Example — Response /projects/{id}/
json{
  "id": "uuid",
  "name": "CRM Redesign",
  "deadline": "2026-08-15",
  "status": "ACTIVE",
  "owner": { "id": "uuid", "full_name": "Alice Kamana" },
  "team": { "id": "uuid", "name": "Backend Squad" },
  "risk_score": { "score": 82, "level": "CRITICAL" }
}

6. Tasks (/api/v1/tasks/)
MethodEndpointDescriptionPermissionsFRGET/projects/{project_id}/tasks/List tasks for a projectScoped—POST/projects/{project_id}/tasks/Create a taskProject ManagerFR-TASK-001GET/tasks/{id}/Task detailScoped—PATCH/tasks/{id}/Edit task fieldsPMFR-TASK-001PATCH/tasks/{id}/statusUpdate task statusAssignee, PMFR-TASK-002POST/tasks/{id}/dependenciesAdd a prerequisite taskPMFR-TASK-005GET/tasks/{id}/historyStatus change historyScoped—GET/users/me/tasksCurrent user's assigned tasksTeam MemberUS-3.3
Example — PATCH /tasks/{id}/status
Request: { "status": "BLOCKED", "blocked_reason": "Waiting on staging API credentials" }
Validation: blocked_reason required when status == "BLOCKED" (FR-TASK-003).
Response: { "id": "uuid", "status": "BLOCKED", "blocked_at": "2026-07-16T10:32:00Z" }

7. Analytics — Workload & Risk (/api/v1/analytics/)
MethodEndpointDescriptionPermissionsFRGET/analytics/workload/{user_id}Current workload % + statusSelf, PM (own team), AdminFR-WORK-001, FR-WORK-002GET/analytics/workload/{user_id}/historyWorkload trend snapshotsSelf, PM, ExecutiveFR-WORK-004GET/analytics/workload/team/{team_id}Aggregated team workloadPM, ExecutiveFR-WORK-004GET/analytics/risk/{project_id}Current risk score + explanationScoped (BR-7.1)FR-RISK-001–003GET/analytics/risk/{project_id}/historyRisk score trendPM, Executive—GET/analytics/risk/portfolioAll projects ranked by riskExecutiveFR-RISK-005
Example — Response /analytics/risk/{project_id}
json{
  "score": 82,
  "level": "CRITICAL",
  "explanation": "Risk level CRITICAL (82%), driven primarily by: 2 of 5 team members overloaded, 1 task blocked for 4 days.",
  "computed_at": "2026-07-16T09:00:00Z"
}

8. Recommendations (/api/v1/recommendations/)
MethodEndpointDescriptionPermissionsFRGET/recommendations/List recommendations (default: pending) for scoped projectsProject ManagerFR-RECO-001GET/recommendations/{id}/Recommendation detailPM (owner of project)FR-RECO-002POST/recommendations/{id}/acceptAccept and apply reassignmentPM (owner of project)FR-RECO-005POST/recommendations/{id}/rejectReject recommendationPM (owner of project)FR-RECO-006GET/recommendations/historyPast decisions (accepted/rejected)PMFR-RECO-007
Example — Response /recommendations/{id}/
json{
  "id": "uuid",
  "task": { "id": "uuid", "title": "API Payment Integration" },
  "current_assignee": { "id": "uuid", "full_name": "David N." },
  "suggested_assignee": { "id": "uuid", "full_name": "Marie T." },
  "justification": "David is currently at 135% capacity while Marie has both matching skills and only 55% capacity...",
  "confidence_level": "HIGH",
  "status": "PENDING"
}

9. Notifications (/api/v1/notifications/)
MethodEndpointDescriptionPermissionsFRGET/notifications/List current user's notificationsAuthenticated (self only)FR-NOTIF-001–004PATCH/notifications/{id}/readMark as readSelf only—PATCH/notifications/read-allMark all as readSelf only—

10. Chat (/api/v1/chat/)
MethodEndpointDescriptionPermissionsFRPOST/chat/queryAsk a natural-language questionPM, ExecutiveFR-CHAT-001POST/chat/summary/{project_id}Request executive summaryExecutiveFR-CHAT-003
Example — POST /chat/query
Request: { "question": "Who is overloaded this week?", "project_id": "uuid" }
Response: { "answer": "David N. is currently overloaded at 135% capacity; no one else on this project exceeds 80%." }

11. Dashboard (/api/v1/dashboard/)
MethodEndpointDescriptionPermissionsFRGET/dashboard/pmAggregated PM dashboard payload (risk, workload, pending recs)Project ManagerFR-DASH-001GET/dashboard/executiveAggregated portfolio dashboard payloadExecutive ManagerFR-DASH-003
These are intentionally aggregated "composite" endpoints (rather than forcing the frontend to make 4-5 separate calls on dashboard load) to help meet the 2-second load budget in NFR-PERF-001.

12. Error Response Examples
StatusScenario401Missing/invalid/expired JWT403Valid user, insufficient role/ownership (e.g., PM trying to access another PM's project)404Resource not found or outside user's scope (scope violations return 404, not 403, to avoid leaking existence of data the user shouldn't know about)422Validation error (e.g., missing blocked_reason, circular dependency)

13. Endpoint-to-Chapter Traceability Summary
ModuleEndpoint CountPrimary Source ChaptersAuth/Accounts96 (AUTH, TEAM)Teams/Skills76 (TEAM)Projects56 (PROJ)Tasks86 (TASK)Analytics66 (WORK, RISK)Recommendations56 (RECO)Notifications36 (NOTIF)Chat26 (CHAT)Dashboard26 (DASH)

End of Chapter 14