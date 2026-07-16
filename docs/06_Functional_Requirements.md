06 — Functional Requirements
Version: 1.0
Document Type: Functional Requirements Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document lists every functional requirement of IA TeamPilot in a numbered, traceable format (FR-XXX). Each requirement is atomic, testable, and mapped back to the user stories in Chapter 4. This is the document you hand to IBM Bob, chapter by chapter, to generate development tickets directly.

2. FR Numbering Convention
FR-[Module]-[Number] — e.g., FR-AUTH-001. Modules: AUTH, TEAM, PROJ, TASK, WORK (workload), RISK, RECO (recommendations), DASH, NOTIF, CHAT.

3. Module: Authentication & Roles (AUTH)
IDRequirementSourceFR-AUTH-001System shall allow a user to register with email, password, and full name.US-1.1FR-AUTH-002System shall enforce unique email addresses at registration.US-1.1FR-AUTH-003System shall enforce a minimum password strength (min. 8 characters, 1 number).US-1.1FR-AUTH-004System shall authenticate users via email/password and issue a JWT session token.US-1.2FR-AUTH-005System shall reject expired or invalid tokens on protected endpoints.US-1.2FR-AUTH-006System shall support four roles: Administrator, Project Manager, Team Member, Executive Manager.US-1.3FR-AUTH-007Only Administrators shall be able to assign or change a user's role.US-1.3FR-AUTH-008System shall restrict access to endpoints/views based on role (see BR-7.1).US-1.3

4. Module: Team & Skills Management (TEAM)
IDRequirementSourceFR-TEAM-001Administrator shall be able to create a team with a name and description.US-2.1FR-TEAM-002Administrator shall be able to add or remove members from a team.US-2.1FR-TEAM-003Administrator shall be able to assign one or more skill tags to a user.US-2.2FR-TEAM-004System shall maintain a predefined list of common skill tags, extensible with free text.US-2.2FR-TEAM-005System shall display the percentage of users missing a skill profile.US-2.3FR-TEAM-006Administrator shall be able to set a custom weekly capacity (hours) per user, overriding the 40h default.BR-1.1

5. Module: Project & Task Management (PROJ / TASK)
IDRequirementSourceFR-PROJ-001Project Manager shall be able to create a project with name, description, deadline, and assigned team.US-3.1FR-PROJ-002System shall automatically set the creating Project Manager as project owner.US-3.1FR-PROJ-003Project Manager shall be able to edit or archive a project.US-3.1FR-TASK-001Project Manager shall be able to create a task with title, description, priority, estimated effort (hours), deadline, required skill(s), and assignee.US-3.2FR-TASK-002Team Member shall be able to update the status of a task assigned to them (To Do, In Progress, Blocked, Done).US-3.3FR-TASK-003System shall require a reason field when a task is set to Blocked.US-3.4, BR-3.1FR-TASK-004System shall timestamp every task status change.US-3.3FR-TASK-005Project Manager shall be able to define one or more prerequisite tasks (dependencies) for a task.US-3.5FR-TASK-006System shall reject circular task dependencies.BR-8.1FR-TASK-007System shall auto-escalate task priority when due date is within 48 hours and status ≠ Done.BR-2.2FR-TASK-008System shall flag a task as "Waiting on Dependency" if a prerequisite task is not Done.BR-3.3FR-TASK-009System shall flag a task as "Unassigned risk contributor" if it has no assignee for more than 48 hours.BR-8.2

6. Module: Workload Analysis (WORK)
IDRequirementSourceFR-WORK-001System shall calculate each user's workload percentage using the formula in BR-1.2.US-4.1FR-WORK-002System shall classify workload into status bands (Underloaded, Balanced, Overloaded, Critically Overloaded) per BR-1.3.US-4.1FR-WORK-003System shall generate an alert when a user's workload status changes to Overloaded or Critically Overloaded, subject to the throttling rule in BR-1.4.US-4.2FR-WORK-004System shall provide an aggregated workload view across all teams for Executive Managers.US-4.3FR-WORK-005System shall recalculate workload whenever a task is created, reassigned, completed, or its status changes.BR-1.2

7. Module: Risk & Delay Prediction (RISK)
IDRequirementSourceFR-RISK-001System shall calculate a project risk score (0–100%) using the weighted formula in BR-4.1.US-5.1FR-RISK-002System shall classify risk score into bands (Low, Moderate, High, Critical) per BR-4.2.US-5.1FR-RISK-003System shall generate a natural-language explanation listing the specific contributing factors behind a risk score.US-5.2FR-RISK-004System shall recalculate risk score on relevant data changes and at minimum every 6 hours.BR-4.3FR-RISK-005System shall provide a portfolio-level view ranking all projects by descending risk score for Executive Managers.US-5.3FR-RISK-006System shall flag a task as a risk contributor if it remains Blocked for more than 24 hours.BR-3.2

8. Module: Recommendations (RECO)
IDRequirementSourceFR-RECO-001System shall generate a task-reassignment recommendation when the trigger conditions in BR-5.1 are met.US-6.1FR-RECO-002Recommendation shall include task, current assignee, suggested assignee, justification text, and confidence level.US-6.1, BR-5.4FR-RECO-003System shall rank candidate reassignees per BR-5.3 (skill match, workload, blocked task count).BR-5.3FR-RECO-004System shall surface a "skill gap" alert when no valid reassignment candidate exists.BR-5.2FR-RECO-005Project Manager shall be able to accept a recommendation, automatically applying the task reassignment.US-6.2, BR-5.5FR-RECO-006Project Manager shall be able to reject a recommendation without applying any change.US-6.2, BR-5.5FR-RECO-007System shall log every recommendation and its outcome (accepted/rejected/pending) with a timestamp.US-6.3FR-RECO-008System shall not reissue an identical rejected recommendation (same task/candidate) within the same sprint.BR-5.5

9. Module: Dashboard & Reporting (DASH)
IDRequirementSourceFR-DASH-001System shall display a Project Manager dashboard with risk score, workload chart, and pending recommendation count.US-7.1FR-DASH-002Dashboard shall load within 2 seconds under normal seed-data volume.US-7.1FR-DASH-003System shall provide an Executive Manager portfolio dashboard aggregating all projects, filterable by project, team, and risk level.US-7.2

10. Module: Notifications (NOTIF)
IDRequirementSourceFR-NOTIF-001System shall notify a Team Member in-app when a task is reassigned to them.US-8.1FR-NOTIF-002System shall notify a Project Manager in-app when a new recommendation is generated.US-8.2FR-NOTIF-003System shall notify a Project Manager when a task has been Blocked for more than 24 hours.BR-6.1FR-NOTIF-004System shall notify Project Manager and Executive Manager when a project's risk level reaches Critical.BR-6.1FR-NOTIF-005System shall not send duplicate notifications of the same type for the same object within a 1-hour window.BR-6.2

11. Module: AI Chat Assistant (CHAT)
IDRequirementSourceFR-CHAT-001System shall allow a Project Manager to ask natural-language questions about their project's live data.US-9.1FR-CHAT-002Chat responses shall be grounded in the same underlying data used by the recommendation and risk engines (no hallucinated figures).US-9.1FR-CHAT-003System shall allow an Executive Manager to request a natural-language executive summary of a project.US-9.2

12. Requirements Summary by Priority
PriorityCountModules Most RepresentedMust (MVP-critical)30AUTH, TASK, WORK, RISK, RECOShould6Dependencies, cross-project views, chatCould3Recommendation history, data completeness, executive summaries

End of Chapter 6