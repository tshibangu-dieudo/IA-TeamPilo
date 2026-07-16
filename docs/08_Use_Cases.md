
08 — Use Cases
Version: 1.0
Document Type: Detailed Use Case Specifications
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document details the most critical use cases as full scenarios — actors, preconditions, main flow, alternate/exception flows, and postconditions. Unlike Chapter 4 (short user stories), these use cases describe exactly how the system behaves step by step, including edge cases. This is the direct input for API design (Chapter 12) and for writing integration tests (Chapter 18).

2. Use Case Selection Criteria
Not every FR from Chapter 6 needs a full use case. We detail only the use cases that are either (a) core to the AI value loop, or (b) have non-trivial branching logic. Simple CRUD (e.g., "edit project name") is considered self-explanatory and is not detailed here.

3. UC-01 — Create and Assign a Task
Actor: Project Manager
Preconditions: PM is logged in; a project and team already exist.
Main Flow:

PM navigates to the project's task list and selects "New Task."
PM enters title, description, priority, estimated effort, deadline, and required skill(s).
PM selects an assignee from the team, or leaves unassigned.
System validates required fields and saves the task with status "To Do."
System recalculates the assignee's workload percentage (FR-WORK-005).
If the new workload pushes the assignee into Overloaded status, system triggers FR-WORK-003.

Alternate Flow — No Assignee Selected:
3a. PM leaves the task unassigned. Task is created with status "To Do" and assignee = null.
3b. If still unassigned after 48 hours, system flags it per FR-TASK-009.
Postconditions: Task exists in the system; workload and risk calculations reflect the new task.

4. UC-02 — Team Member Reports a Blocker
Actor: Team Member
Preconditions: User is logged in and has at least one task assigned with status "In Progress."
Main Flow:

Team Member opens their task list and selects a task.
Team Member changes status to "Blocked."
System requires a reason (FR-TASK-003); Team Member enters a short text explanation.
System timestamps the change and updates the task status.
System notifies the Project Manager immediately that a task is newly blocked (informational, not yet risk-triggering).

Alternate Flow — Blocker Not Resolved Within 24 Hours:
5a. System detects the task is still Blocked after 24 hours (background check).
5b. System flags the task as a risk contributor (BR-3.2) and recalculates the project's risk score.
5c. System sends a distinct, higher-priority notification to the PM (FR-NOTIF-003).
Postconditions: Task status reflects the blocker; PM is aware; risk score is updated if the 24h threshold is passed.

5. UC-03 — System Detects Overload and Generates a Recommendation
Actor: System (AI Engine), observed by Project Manager
Preconditions: At least one active project with assigned tasks and workload data.
Main Flow:

A triggering event occurs (task created, reassigned, or completed) that changes a user's workload.
System recalculates workload percentage for the affected user (BR-1.2).
System classifies the new workload into a status band (BR-1.3).
If status becomes Overloaded or Critically Overloaded, system checks the alert throttle (BR-1.4) and, if eligible, generates an overload alert.
System evaluates recommendation trigger conditions (BR-5.1): is there an underloaded/balanced teammate with a matching skill for at least one of the overloaded user's reassignable tasks?
If conditions are met, system (via LangChain-orchestrated Granite call) generates a recommendation with justification and confidence level (BR-5.4).
System stores the recommendation as "Pending" and notifies the PM (FR-NOTIF-002).

Alternate Flow — No Valid Candidate:
5a. No teammate has a matching skill or sufficient free capacity.
5b. System does not generate a reassignment recommendation; instead, it surfaces a "skill gap" alert to the PM (FR-RECO-004).
Alternate Flow — AI Service Unavailable:
6a. The Granite/watsonx call times out or fails.
6b. System falls back gracefully per NFR-REL-001: shows the last-known workload alert without a redistribution suggestion, and flags "AI temporarily unavailable."
Postconditions: A recommendation exists in "Pending" state (or a skill-gap alert is shown), and the PM has been notified.

6. UC-04 — Project Manager Reviews and Acts on a Recommendation
Actor: Project Manager
Preconditions: At least one recommendation exists with status "Pending" (from UC-03).
Main Flow:

PM opens the recommendation from the dashboard or notification.
System displays: affected task, current assignee, suggested assignee, justification text, and confidence level.
PM reviews the reasoning and clicks "Accept."
System reassigns the task to the suggested candidate (FR-RECO-005).
System notifies both the previous and new assignee (FR-NOTIF-001).
System logs the recommendation as "Accepted" with a timestamp (FR-RECO-007).
System recalculates workload for both affected users.

Alternate Flow — PM Rejects the Recommendation:
3a. PM clicks "Reject" instead.
3b. System logs the recommendation as "Rejected" (FR-RECO-006, FR-RECO-007); no task change is applied.
3c. System will not reissue the identical task/candidate pairing within the same sprint (FR-RECO-008).
Postconditions: Recommendation is resolved (Accepted or Rejected); task assignment reflects the decision if accepted; decision is permanently logged.

7. UC-05 — Project Risk Score Reaches Critical
Actor: System (AI Engine), observed by Project Manager and Executive Manager
Preconditions: An active project with ongoing task activity.
Main Flow:

A triggering event occurs (task change) or the scheduled 6-hour recalculation runs (BR-4.3).
System recomputes the four risk factors: Overload, Blocked Task, Deadline Proximity, Historical Velocity (BR-4.1).
System computes the weighted composite risk score and classifies it into a band (BR-4.2).
If the new score falls into the "Critical" band (80–100%), system generates a natural-language explanation citing the specific contributing factors (FR-RISK-003).
System notifies both the Project Manager and the Executive Manager (FR-NOTIF-004).

Alternate Flow — Risk Score Decreases Below Critical:
4a. A previously Critical project drops to High or below after corrective action (e.g., an accepted recommendation resolved an overload).
4b. System updates the displayed risk level; no new "Critical" notification is sent (only sent on entry into Critical, not on every recalculation).
Postconditions: Risk score and explanation are current; relevant stakeholders are informed only on meaningful state transitions (not on every recalculation), consistent with the throttling philosophy in BR-6.2.

8. UC-06 — Project Manager Queries the AI Chat Assistant
Actor: Project Manager
Preconditions: PM is logged in and viewing an active project.
Main Flow:

PM opens the chat panel and types a natural-language question (e.g., "Who is overloaded this week?").
System (via LangChain) constructs a prompt combining the question with live project data (workload, tasks, risk scores) — not static training knowledge (FR-CHAT-002).
Granite generates a response grounded in that data.
System displays the response in the chat panel, in plain language.

Alternate Flow — Question Requires Data Outside the PM's Scope:
2a. PM asks about a project they don't manage.
2b. System restricts the data passed to the AI to only projects the PM has access to (BR-7.1), so the response cannot leak unauthorized data.
Postconditions: PM receives a data-grounded answer without needing to manually navigate the dashboard.

9. UC-07 — Executive Manager Reviews Portfolio Risk
Actor: Executive Manager
Preconditions: Multiple active projects exist across one or more teams.
Main Flow:

Executive Manager opens the portfolio dashboard.
System displays all projects the Executive has visibility into, ranked by descending risk score (FR-RISK-005).
Executive Manager filters by team or risk level as needed (FR-DASH-003).
Executive Manager drills into a specific high-risk project to see its explanation (from UC-05).

Postconditions: Executive Manager has an up-to-date, prioritized view of organizational risk without needing per-project manual reporting from each PM.

10. Use Case Traceability Matrix
Use CaseRelated FRsRelated BRsUC-01FR-TASK-001, FR-WORK-005, FR-TASK-009BR-1.2, BR-8.2UC-02FR-TASK-002, FR-TASK-003, FR-NOTIF-003BR-3.1, BR-3.2UC-03FR-WORK-001–003, FR-RECO-001–004BR-1.3, BR-1.4, BR-5.1, BR-5.2UC-04FR-RECO-005–008BR-5.3, BR-5.4, BR-5.5UC-05FR-RISK-001–004, FR-NOTIF-004BR-4.1, BR-4.2, BR-4.3UC-06FR-CHAT-001, FR-CHAT-002BR-7.1UC-07FR-RISK-005, FR-DASH-003BR-7.1

End of Chapter 8
