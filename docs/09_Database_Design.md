09 — Database Design
Version: 1.0
Document Type: Data Model Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines the complete relational data model for IA TeamPilot: entities, fields, types, relationships, and constraints. It translates Chapters 5–8 (business rules, functional requirements, use cases) into a concrete PostgreSQL schema, implemented as Django models. Every field here is used by at least one FR or BR — there is no speculative "might need later" data.

2. Entity-Relationship Overview
Organization
   │
   ├── Team ──< TeamMembership >── User
   │                                  │
   │                                  ├── Skill (many-to-many via UserSkill)
   │                                  │
   ├── Project ──< Task >── TaskDependency (self-referencing)
   │       │           │
   │       │           └── Skill (many-to-many via TaskSkill, required skills)
   │       │
   │       ├── RiskScore (one-to-many, historical snapshots)
   │       │
   │       └── Recommendation ──> Task, User (suggested_assignee)
   │
   ├── WorkloadSnapshot (per User, per time)
   │
   └── Notification ──> User

3. Entity: Organization
FieldTypeConstraintsidUUIDPrimary Keynamevarchar(255)Not nullcreated_attimestampAuto
Note: single-organization deployment is sufficient for the MVP (per Chapter 2, §9.1), but the model includes this table from the start to avoid a costly migration if multi-tenant support becomes relevant later.

4. Entity: User
FieldTypeConstraintsidUUIDPrimary Keyorganization_idUUIDForeign Key → Organizationemailvarchar(255)Unique, not nullpassword_hashvarchar(255)Not null (Django auth)full_namevarchar(255)Not nullroleenumADMIN, PROJECT_MANAGER, TEAM_MEMBER, EXECUTIVE — not nullweekly_capacity_hoursintegerDefault 40 (BR-1.1)is_activebooleanDefault truecreated_attimestampAuto
Relates to: FR-AUTH-001–008, BR-1.1

5. Entity: Skill
FieldTypeConstraintsidUUIDPrimary Keynamevarchar(100)Unique, not nullis_predefinedbooleanDefault true (distinguishes seed skills from admin-added free text, FR-TEAM-004)
5.1 Junction Table: UserSkill
FieldTypeConstraintsidUUIDPrimary Keyuser_idUUIDForeign Key → Userskill_idUUIDForeign Key → Skill
Constraint: unique together (user_id, skill_id).
Relates to: FR-TEAM-003, FR-TEAM-004, BR-5.2

6. Entity: Team
FieldTypeConstraintsidUUIDPrimary Keyorganization_idUUIDForeign Key → Organizationnamevarchar(255)Not nulldescriptiontextNullablecreated_attimestampAuto
6.1 Junction Table: TeamMembership
FieldTypeConstraintsidUUIDPrimary Keyteam_idUUIDForeign Key → Teamuser_idUUIDForeign Key → Userjoined_attimestampAuto
Constraint: unique together (team_id, user_id).
Relates to: FR-TEAM-001, FR-TEAM-002

7. Entity: Project
FieldTypeConstraintsidUUIDPrimary Keyorganization_idUUIDForeign Key → Organizationteam_idUUIDForeign Key → Teamowner_idUUIDForeign Key → User (must have role = PROJECT_MANAGER)namevarchar(255)Not nulldescriptiontextNullabledeadlinedateNot nullstatusenumACTIVE, ARCHIVED, COMPLETED — default ACTIVEcreated_attimestampAuto
Relates to: FR-PROJ-001–003

8. Entity: Task
FieldTypeConstraintsidUUIDPrimary Keyproject_idUUIDForeign Key → Projectassignee_idUUIDForeign Key → User, nullabletitlevarchar(255)Not nulldescriptiontextNullablepriorityenumLOW, MEDIUM, HIGH, CRITICAL — not nullstatusenumTODO, IN_PROGRESS, BLOCKED, WAITING_ON_DEPENDENCY, DONE — default TODOestimated_effort_hoursdecimalNot null, > 0deadlinedateNot nullblocked_reasontextNullable (required at application level when status = BLOCKED, per FR-TASK-003)blocked_attimestampNullable (set when status transitions to BLOCKED, used for the 24h check in BR-3.2)unassigned_sincetimestampNullable (set when assignee is null, used for FR-TASK-009)created_attimestampAutoupdated_attimestampAuto
8.1 Junction Table: TaskSkill (required skills for the task)
FieldTypeConstraintsidUUIDPrimary Keytask_idUUIDForeign Key → Taskskill_idUUIDForeign Key → Skill
8.2 Entity: TaskDependency (self-referencing)
FieldTypeConstraintsidUUIDPrimary Keytask_idUUIDForeign Key → Task (the dependent task)depends_on_task_idUUIDForeign Key → Task (the prerequisite)
Constraint: application-level check to reject circular references before insert (BR-8.1); task_id ≠ depends_on_task_id.
8.3 Entity: TaskStatusHistory
FieldTypeConstraintsidUUIDPrimary Keytask_idUUIDForeign Key → Taskprevious_statusenumNullable (null for initial creation)new_statusenumNot nullchanged_attimestampAuto
Purpose: feeds the Historical Velocity Factor (BR-4.1, W4) — actual completion rate over time requires a full history, not just the current status.
Relates to: FR-TASK-001–009, BR-2.2, BR-3.1–3.3, BR-8.1, BR-8.2

9. Entity: WorkloadSnapshot
FieldTypeConstraintsidUUIDPrimary Keyuser_idUUIDForeign Key → Userworkload_percentagedecimalNot nullstatusenumUNDERLOADED, BALANCED, OVERLOADED, CRITICALLY_OVERLOADED (BR-1.3)computed_attimestampAuto
Purpose: storing snapshots (rather than only a live computed value) enables the workload trend line referenced in Persona Grace's KPIs (Chapter 3, §4.4) and avoids recomputing history on every dashboard load.
Relates to: FR-WORK-001–005, BR-1.2–1.4

10. Entity: RiskScore
FieldTypeConstraintsidUUIDPrimary Keyproject_idUUIDForeign Key → Projectscoredecimal0–100, not nulllevelenumLOW, MODERATE, HIGH, CRITICAL (BR-4.2)overload_factordecimalSub-score component (BR-4.1)blocked_task_factordecimalSub-score componentdeadline_proximity_factordecimalSub-score componenthistorical_velocity_factordecimalSub-score componentexplanation_texttextNatural-language explanation (FR-RISK-003)computed_attimestampAuto
Relates to: FR-RISK-001–006, BR-4.1–4.3

11. Entity: Recommendation
FieldTypeConstraintsidUUIDPrimary Keyproject_idUUIDForeign Key → Projecttask_idUUIDForeign Key → Taskcurrent_assignee_idUUIDForeign Key → User, nullablesuggested_assignee_idUUIDForeign Key → Userjustification_texttextNot null (BR-5.4)confidence_levelenumHIGH, MEDIUM, LOW (BR-5.4)statusenumPENDING, ACCEPTED, REJECTED — default PENDINGdecided_by_idUUIDForeign Key → User, nullable (set on accept/reject)decided_attimestampNullablecreated_attimestampAuto
Relates to: FR-RECO-001–008, BR-5.1–5.5

12. Entity: Notification
FieldTypeConstraintsidUUIDPrimary Keyuser_idUUIDForeign Key → User (recipient)typeenumTASK_REASSIGNED, NEW_RECOMMENDATION, TASK_BLOCKED_24H, PROJECT_RISK_CRITICALrelated_object_idUUIDGeneric reference (task, recommendation, or project id depending on type)messagevarchar(500)Not nullis_readbooleanDefault falsecreated_attimestampAuto
Constraint: throttling (BR-6.2) enforced at the application/service layer, not the database — a duplicate within 1 hour is prevented before insert, not via a DB constraint.
Relates to: FR-NOTIF-001–005, BR-6.1, BR-6.2

13. Indexing Strategy
TableIndexReasonTask(project_id, status)Frequent filtering by project + status for dashboardsTask(assignee_id, status)Team Member's task list queryWorkloadSnapshot(user_id, computed_at DESC)Trend queries need latest-first orderingRiskScore(project_id, computed_at DESC)Same pattern for risk trendRecommendation(project_id, status)PM's pending recommendations viewNotification(user_id, is_read, created_at DESC)Unread notification feed

14. Seed Data Plan (for Demo/Judging)
Per Chapter 2, §5, the seed dataset will simulate:

1 Organization
~20 Users (mix of roles: 1 Admin, 3 PMs, 14 Team Members, 2 Executives)
~4 Teams
~10 Projects (varying risk profiles: some healthy, some intentionally overloaded to demonstrate AI detection)
~150 Tasks (with realistic distribution of status, priority, and at least a few intentionally blocked >24h and intentionally overloaded assignees, so the AI has something meaningful to detect on first run)
~15–20 Skills (a realistic software team skill list: Backend, Frontend, DevOps, UI/UX, QA, Django, React, etc.)


15. Django App Mapping
Model(s)Django AppOrganization, User, UserSkillaccountsTeam, TeamMembership, SkillteamsProjectprojectsTask, TaskSkill, TaskDependency, TaskStatusHistorytasksWorkloadSnapshot, RiskScoreanalyticsRecommendationrecommendationsNotificationnotifications
(Chat is stateless relative to this schema — no dedicated model needed beyond referencing live data at query time, per FR-CHAT-002; this is detailed further in Chapter 11 — AI Architecture.)

End of Chapter 9