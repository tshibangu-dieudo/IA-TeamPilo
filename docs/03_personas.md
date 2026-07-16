D'accord, je pars sur l'option qui garde la cohérence avec le plan initial : je développe un Chapitre 3 — Personas plus détaillé que le résumé de la section 10 (avec objectifs, frustrations, journée type, KPIs suivis par persona), plutôt que de sauter directement aux User Stories. C'est plus utile pour rédiger ensuite des User Stories précises au Chapitre 4.
Voici 03_Personas.md :

03 — Personas
Version: 1.0
Document Type: User Personas
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document expands the four user roles introduced in Chapter 1 (Section 10) into detailed personas. Each persona describes goals, frustrations, a typical day, and the specific KPIs or signals that matter to them. These personas guide every subsequent design decision — user stories, UI/UX, and AI recommendation logic must serve at least one of these four people.

2. Persona 1 — Alice Kamana, Project Manager
Role: Primary user of IA TeamPilot
Experience: 5 years managing software teams
Team size managed: 8–12 developers across 2–3 concurrent projects
2.1 Goals

Deliver projects on time without last-minute surprises.
Keep workload fair across the team to avoid burnout and attrition.
Spend less time manually cross-checking task boards.
Justify decisions to executives with data, not intuition.

2.2 Frustrations

Discovers overload or delays during standup — too late to prevent impact.
Spends hours each week manually comparing task lists across team members.
Has no consistent way to explain why she reassigned a task when challenged.
Existing tools show data but never tell her what to actually do about it.

2.3 Typical Day (Without IA TeamPilot)
Morning standup reveals a blocked task. Alice manually checks who else has the required skill and enough free capacity, interrupting two other developers to ask. She updates the sprint board by hand and sends a Slack message explaining the change, hoping no one else is silently overloaded.
2.4 Typical Day (With IA TeamPilot)
Alice opens her dashboard and sees an alert: "Developer B is at 135% capacity for this sprint; Developer D has matching skills and 40% free capacity — recommend reassigning Task #482 (confidence: high)." She reviews the reasoning, accepts it in one click, and the system logs the decision and notifies both developers automatically.
2.5 Key Signals She Cares About

Workload percentage per team member.
Days until a risk becomes a missed deadline.
Number of pending AI recommendations awaiting her review.


3. Persona 2 — David Niyonzima, Team Member (Developer)
Role: Individual contributor, backend developer
Experience: 2 years
3.1 Goals

Know exactly what to work on without ambiguity.
Get help quickly when blocked, instead of waiting for the next standup.
Have his actual workload recognized before it becomes unmanageable.

3.2 Frustrations

Gets assigned new tasks without visibility into how full his plate already is.
Blockers sometimes go unnoticed for a day or more.
Feels reassignments happen "by whoever the manager remembers first," not fairly.

3.3 Typical Day
David marks a task as blocked in the system. Without IA TeamPilot, this sits unnoticed until the next standup. With IA TeamPilot, the system detects the blocker immediately, flags it to Alice, and suggests David could pick up a smaller, unblocked task in the meantime — keeping him productive rather than idle.
3.4 Key Signals He Cares About

His current task list, ranked by priority.
Whether his workload is flagged as balanced, light, or overloaded.
How quickly a reported blocker gets a response.


4. Persona 3 — Grace Uwimana, Executive Manager
Role: Head of Engineering / Delivery Director
Scope: Oversees multiple project managers and 5–8 concurrent projects
4.1 Goals

Get a real-time, high-level view of organizational health without asking each PM individually.
Spot systemic risk (e.g., one team chronically overloaded) early enough to act.
Make staffing and hiring decisions based on data trends, not anecdotes.

4.2 Frustrations

Status reports are stitched together manually by each PM, often outdated by the time she reads them.
Cannot easily compare workload balance or risk levels across different teams.
Learns about a missed deadline from a client complaint rather than an internal signal.

4.3 Typical Day
Grace opens a cross-project dashboard showing risk scores for every active project, sorted by severity. One project shows an 82% probability of missing its deadline. She drills in, sees the AI's explanation (two key developers overloaded, one dependency blocked for 4 days), and decides whether to allocate an additional contractor — a decision made in minutes instead of days.
4.4 Key Signals She Cares About

Portfolio-level risk ranking across all projects.
Trend lines (is overall team workload balance improving or worsening month over month).
Number of AI recommendations accepted vs. overridden by PMs (a trust signal).


5. Persona 4 — Samuel Bizimana, System Administrator
Role: IT/Platform administrator
Scope: Manages accounts, permissions, and system configuration
5.1 Goals

Onboard new team members quickly with correct roles and permissions.
Keep organizational data structured and accurate (skills, teams, projects).
Ensure the AI has access to clean, reliable input data — since bad data means bad recommendations.

5.2 Frustrations

Manually re-entering skills and team structures when they change.
No visibility into whether the AI's underlying data is stale or incomplete.

5.3 Typical Day
Samuel adds three new hires to the platform, assigns their skills and team, and sets role-based permissions so they only see their own tasks, not the full organizational dashboard. He checks a data-health indicator confirming all active users have up-to-date skill profiles.
5.4 Key Signals He Cares About

Number of users/teams/projects correctly configured.
Data completeness (e.g., % of users missing a skill profile).


6. Persona Priority for the MVP
Given the July 31 deadline, not all personas receive equal feature depth in the MVP:
PersonaMVP PriorityJustificationProject Manager (Alice)HighestPrimary decision-maker; most AI value is delivered hereTeam Member (David)HighNeeded to generate realistic workload/blocker data the AI reasons overExecutive Manager (Grace)MediumCross-project dashboard is valuable but can use a simplified view in MVPSystem Administrator (Samuel)LowerBasic account/role management only; not a judging-critical feature

7. How Personas Map to AI Capabilities (Chapter 1, Section 11)
AI CapabilityPrimary Persona ServedWorkflow AnalysisProject Manager, Executive ManagerBottleneck DetectionProject Manager, Team MemberIntelligent RecommendationsProject ManagerDynamic SchedulingProject Manager, Executive Manager

End of Chapter 3
