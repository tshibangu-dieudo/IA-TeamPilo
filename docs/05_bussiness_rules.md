05 — Business Rules
Version: 1.0
Document Type: Business Rules Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines the precise, testable rules that govern IA TeamPilot's behavior — especially the logic behind AI-driven calculations (workload, risk, recommendations). These rules remove ambiguity between "the AI decides" and "the system applies a documented formula." Every rule here must be implementable as deterministic code that the AI reasoning layer draws on, so that recommendations remain explainable rather than a black box.

2. Workload Calculation Rules
BR-1.1 — Capacity Definition
Each team member has a default working capacity of 40 hours/week (configurable per user by the Administrator, to allow for part-time members).
BR-1.2 — Workload Percentage Formula
Workload % = (Sum of estimated effort hours of all open tasks assigned to the user
              that fall within the current sprint window)
              / (User's weekly capacity × sprint length in weeks)
              × 100
BR-1.3 — Workload Status Thresholds
Workload %StatusColor Code0–60%UnderloadedBlue61–99%BalancedGreen100–120%OverloadedOrange>120%Critically OverloadedRed
BR-1.4 — Overload Alert Trigger
An alert is generated when a user's workload status changes to Overloaded or Critically Overloaded, and is not re-triggered again for the same user within a 24-hour window unless workload increases by an additional 15 percentage points.

3. Task Priority Rules
BR-2.1 — Priority Levels
Every task has one of four priority levels: Critical, High, Medium, Low.
BR-2.2 — Priority Auto-Escalation
If a task's due date is within 48 hours and its status is not "Done," its priority is automatically escalated by one level (e.g., Medium → High), unless it is already Critical.

4. Blocked Task Rules
BR-3.1 — Blocked Task Definition
A task is "Blocked" when its status is explicitly set to Blocked by the assignee, with a mandatory reason field.
BR-3.2 — Blocked Task Escalation
If a task remains Blocked for more than 24 hours, the system automatically flags it as a risk contributor in the parent project's risk calculation (see Section 5) and notifies the Project Manager.
BR-3.3 — Dependency Blocking
If Task B depends on Task A (per US-3.5) and Task A is not Done, Task B is automatically flagged as "Waiting on Dependency" — a distinct state from manually-set "Blocked," used differently in risk scoring (lower initial severity, since it is expected/planned).

5. Project Risk Score Rules
BR-4.1 — Risk Score Formula (0–100%)
The project risk score is a weighted composite of four factors:
Risk Score = (W1 × Overload Factor)
           + (W2 × Blocked Task Factor)
           + (W3 × Deadline Proximity Factor)
           + (W4 × Historical Velocity Factor)
FactorWeightDescriptionOverload FactorW1 = 35%% of assigned team members currently Overloaded or Critically OverloadedBlocked Task FactorW2 = 30%% of open tasks currently Blocked, weighted by how long they've been blockedDeadline Proximity FactorW3 = 20%Ratio of remaining work (effort hours) to remaining time until project deadlineHistorical Velocity FactorW4 = 15%Comparison of actual task completion rate vs. planned rate over the last 2 weeks
(Exact factor sub-formulas are defined in Chapter 11 — AI Architecture, since they depend on the specific Granite prompt/analysis design.)
BR-4.2 — Risk Level Bands
Risk ScoreLevel0–29%Low30–59%Moderate60–79%High80–100%Critical
BR-4.3 — Risk Recalculation Trigger
Risk score is recalculated whenever any of the following occur: a task status changes, a task is reassigned, a new task is added, a deadline is modified, or once every 6 hours as a scheduled background refresh (to catch time-based drift like deadline proximity even with no manual changes).

6. Recommendation Generation Rules
BR-5.1 — Recommendation Trigger Conditions
A task-redistribution recommendation is generated when all of the following are true:

At least one team member on the project is Overloaded or Critically Overloaded (BR-1.3).
At least one other team member on the same project/team is Underloaded or Balanced with capacity to spare.
The candidate receiving task has a skill match with at least one of the overloaded member's reassignable tasks (see BR-5.2).

BR-5.2 — Skill Match Requirement
A task is only recommended for reassignment to a user who has at least one matching skill tag with the task's required skill(s). Tasks with no matching candidate anywhere on the team are not included in a recommendation; instead, the system surfaces a "skill gap" alert to the Project Manager.
BR-5.3 — Reassignment Candidate Selection
When multiple valid candidates exist, the system ranks them by:

Highest skill match score.
Lowest current workload %.
Fewest currently blocked tasks (proxy for reliability/availability).

BR-5.4 — Recommendation Confidence Level
ConfidenceConditionHighSkill match is exact; candidate workload < 80% after reassignmentMediumSkill match is partial; candidate workload < 100% after reassignmentLowNo ideal candidate; best available option shown with explicit caveat
BR-5.5 — Human Override Rule
No recommendation is ever applied automatically. A recommendation only changes task assignment after explicit Project Manager approval (US-6.2). Rejected recommendations are logged but never reissued for the identical task/candidate pair within the same sprint.

7. Notification Rules
BR-6.1 — Notification Triggers
EventRecipientChannelTask reassigned to userTeam MemberIn-app (Must), Email (Should)New AI recommendation generatedProject ManagerIn-appTask blocked >24hProject ManagerIn-appProject risk level reaches CriticalProject Manager + Executive ManagerIn-app
BR-6.2 — Notification Throttling
No user receives more than one notification of the same type for the same object within a 1-hour window, to avoid alert fatigue.

8. Role-Based Access Rules
BR-7.1 — Data Visibility Scope
RoleCan ViewAdministratorAll organizational data (configuration only, not task content by default)Project ManagerAll projects they own or are assigned to manageTeam MemberOnly their own tasks and their team's aggregate (non-individual) workloadExecutive ManagerRead-only cross-project view of all projects in the organization
BR-7.2 — Recommendation Visibility
Only the Project Manager who owns the affected project can accept or reject a recommendation. Executive Managers can view recommendation history but cannot act on it (BR-5.5 stays a PM-level decision by design).

9. Data Integrity Rules
BR-8.1 — Circular Dependency Prevention
The system must reject any task dependency configuration that would create a circular reference (Task A depends on B, B depends on A).
BR-8.2 — Orphaned Task Prevention
A task cannot exist without an assigned project. A task can temporarily have no assignee (status: "Unassigned"), but this state itself contributes to the Blocked Task Factor (BR-4.1) if unresolved for more than 48 hours.

10. Traceability to User Stories
Business Rule GroupRelated User StoriesWorkload CalculationUS-4.1, US-4.2, US-4.3Blocked Task RulesUS-3.4, US-5.2Risk ScoreUS-5.1, US-5.2, US-5.3RecommendationsUS-6.1, US-6.2, US-6.3NotificationsUS-8.1, US-8.2

End of Chapter 5
