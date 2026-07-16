04 — User Stories
Version: 1.0
Document Type: User Stories
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document translates the personas from Chapter 3 into concrete user stories, using the standard format:

As a [persona], I want to [action], so that [benefit].

Each story includes acceptance criteria and a priority level (MoSCoW: Must / Should / Could / Won't — for the MVP). These stories are the direct input for Chapter 9 (Database Design) and Chapter 12 (REST API), and are meant to be handed to IBM Bob one epic at a time.

2. Epic Overview
EpicDescriptionPrimary PersonaE1 — Authentication & RolesAccount creation, login, role-based accessAdministratorE2 — Team & Skills ManagementCreating teams, assigning skillsAdministrator, PME3 — Project & Task ManagementCRUD for projects and tasksPM, Team MemberE4 — Workload Analysis (AI)Detecting overload/underloadPM, ExecutiveE5 — Risk & Delay Prediction (AI)Predicting missed deadlinesPM, ExecutiveE6 — Recommendations (AI)Task redistribution suggestionsPME7 — Dashboard & ReportingVisualizing project/team healthPM, ExecutiveE8 — NotificationsAlerting users to relevant eventsAllE9 — AI Chat AssistantNatural language Q&A over project dataPM, Executive

3. Epic E1 — Authentication & Roles
US-1.1 — As a new user, I want to register an account with my email and password, so that I can access the platform.
Acceptance: Email uniqueness enforced; password meets minimum security requirements; user receives a confirmation state. Priority: Must
US-1.2 — As a registered user, I want to log in securely, so that I can access only the data relevant to my role.
Acceptance: JWT-based session; invalid credentials rejected with a clear error. Priority: Must
US-1.3 — As an Administrator, I want to assign a role (Admin, PM, Team Member, Executive) to each user, so that permissions are correctly scoped.
Acceptance: Role changes take effect immediately; unauthorized users cannot access role-restricted views. Priority: Must

4. Epic E2 — Team & Skills Management
US-2.1 — As an Administrator, I want to create a team and add members to it, so that project managers can assign work within a defined group.
Acceptance: A team has a name, a list of members, and is linked to an organization. Priority: Must
US-2.2 — As an Administrator, I want to assign skills to each team member, so that the AI can match tasks to the right people.
Acceptance: Skills are selected from a predefined list or added as free text; each user can have multiple skills. Priority: Must
US-2.3 — As an Administrator, I want to see a data-completeness indicator, so that I know if missing skill data could reduce AI recommendation quality.
Acceptance: Dashboard shows % of users with at least one skill assigned. Priority: Could

5. Epic E3 — Project & Task Management
US-3.1 — As a Project Manager, I want to create a project with a name, description, and deadline, so that I can start assigning tasks to it.
Acceptance: Project requires a name and deadline; PM is automatically set as owner. Priority: Must
US-3.2 — As a Project Manager, I want to create tasks within a project and assign them to team members, so that work is clearly distributed.
Acceptance: Task has title, description, priority, estimated effort, deadline, assignee, and status. Priority: Must
US-3.3 — As a Team Member, I want to update the status of my tasks (To Do / In Progress / Blocked / Done), so that the system reflects real progress.
Acceptance: Status changes are timestamped and visible to the PM in real time. Priority: Must
US-3.4 — As a Team Member, I want to mark a task as blocked and explain why, so that my manager and the AI can react quickly.
Acceptance: A blocked task requires a short reason field; it is flagged distinctly on the dashboard. Priority: Must
US-3.5 — As a Project Manager, I want to define task dependencies, so that the AI can factor them into delay predictions.
Acceptance: A task can list one or more prerequisite tasks; circular dependencies are rejected. Priority: Should

6. Epic E4 — Workload Analysis (AI)
US-4.1 — As a Project Manager, I want the system to show each team member's current workload as a percentage of capacity, so that I can spot imbalance at a glance.
Acceptance: Workload is computed from open tasks, estimated effort, and available working hours; updates automatically as tasks change. Priority: Must
US-4.2 — As a Project Manager, I want to be alerted when a team member exceeds a workload threshold, so that I can intervene before burnout or delay occurs.
Acceptance: Alert triggers above a configurable threshold (default 100%); alert includes the affected person and current load. Priority: Must
US-4.3 — As an Executive Manager, I want to see workload balance aggregated across all teams, so that I can identify systemic staffing issues.
Acceptance: Cross-project view aggregates individual workload data without requiring per-project drill-down. Priority: Should

7. Epic E5 — Risk & Delay Prediction (AI)
US-5.1 — As a Project Manager, I want the system to estimate the probability that a project will miss its deadline, so that I can act early.
Acceptance: Risk score (0–100%) is displayed per project, recalculated when relevant data changes (task delay, blocker, absence). Priority: Must
US-5.2 — As a Project Manager, I want an explanation of why a project is flagged as at-risk, so that I can trust and verify the recommendation.
Acceptance: Risk explanation cites specific contributing factors (e.g., "2 overloaded developers, 1 blocked dependency for 4 days"). Priority: Must
US-5.3 — As an Executive Manager, I want to see all at-risk projects ranked by severity, so that I can prioritize where to intervene first.
Acceptance: Portfolio view sorted by descending risk score. Priority: Should

8. Epic E6 — Recommendations (AI)
US-6.1 — As a Project Manager, I want the AI to suggest reassigning a specific task to a specific person, so that I don't have to manually cross-reference skills and availability.
Acceptance: Recommendation includes: task, current assignee, suggested assignee, justification, and confidence level. Priority: Must
US-6.2 — As a Project Manager, I want to accept or reject an AI recommendation with one click, so that I retain full control over decisions.
Acceptance: Accepting a recommendation automatically updates the task assignment and notifies both parties; rejecting logs the decision without applying changes. Priority: Must
US-6.3 — As a Project Manager, I want to see a history of past AI recommendations and whether I accepted or rejected them, so that I can review decision patterns over time.
Acceptance: A log view lists past recommendations with timestamps and outcomes. Priority: Could

9. Epic E7 — Dashboard & Reporting
US-7.1 — As a Project Manager, I want a dashboard summarizing project health, team workload, and open alerts, so that I can start my day with a clear picture.
Acceptance: Dashboard loads within 2 seconds with current data; shows at least: risk score, workload chart, pending recommendations count. Priority: Must
US-7.2 — As an Executive Manager, I want a portfolio-level dashboard across all projects, so that I don't need to check each project individually.
Acceptance: Aggregated view with filters by project, team, and risk level. Priority: Should

10. Epic E8 — Notifications
US-8.1 — As a Team Member, I want to be notified when a task is reassigned to me, so that I know immediately what to work on.
Acceptance: In-app notification generated at the moment of reassignment. Priority: Must
US-8.2 — As a Project Manager, I want to be notified when a new AI recommendation is generated, so that I don't have to check the dashboard constantly.
Acceptance: Notification includes a summary and a direct link to the recommendation. Priority: Should

11. Epic E9 — AI Chat Assistant
US-9.1 — As a Project Manager, I want to ask the AI natural-language questions about my project ("Who is overloaded this week?"), so that I can get answers without navigating multiple screens.
Acceptance: Chat responds using live project data, not generic answers; responses are grounded in the same data used by the recommendation engine. Priority: Should
US-9.2 — As an Executive Manager, I want to ask the AI for a summary of a project's status, so that I can quickly brief stakeholders.
Acceptance: Chat can generate a short natural-language executive summary on request. Priority: Could

12. MVP Priority Summary
PriorityStory CountNotesMust13Core authentication, task management, workload analysis, risk detection, recommendationsShould6Cross-project views, dependencies, chat assistantCould3History log, data-completeness indicator, executive chat summaries
The Must stories alone are sufficient to demonstrate the full value loop described in Chapter 1: data → analysis → risk detection → recommendation → human decision. This is the minimum needed for a credible July 31 submission; Should/Could items are stretch goals if time allows.

End of Chapter 4