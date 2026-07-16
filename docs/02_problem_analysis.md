02 — Problem Analysis
Version: 1.0
Document Type: Problem Analysis
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document provides a detailed analysis of the business problem that IA TeamPilot addresses. While Chapter 1 (Project Vision) introduced the problem at a high level, this chapter breaks it down into its root causes, quantifies its impact, examines how teams currently work without AI assistance, and justifies why an AI-based approach is the right solution — not just a convenient one.

2. Current State: How Teams Work Today
Before introducing AI, it is necessary to understand the actual workflow most software teams follow without an intelligent coordination layer.
2.1 Typical Workflow Without AI Assistance

The Project Manager creates tasks manually in a tool such as Jira, Trello, or Asana.
Tasks are assigned based on the manager's memory of who is available and who has the right skills.
Team members update task status manually, often inconsistently.
The Project Manager reviews the board periodically (daily standup, weekly review) to identify problems.
Overload, blockers, or delays are usually discovered after they have already affected the schedule.
The Project Manager manually decides how to redistribute work, often based on incomplete or outdated information.
Communication about the change happens informally (chat, verbal, email).

2.2 Key Observation
Every step above depends on human attention and memory. The system stores data, but does not interpret it. The cognitive workload of cross-referencing deadlines, skills, availability, and current load falls entirely on the manager, and it grows non-linearly as team size and project count increase.

3. Root Cause Analysis
We identify four root causes that explain why project coordination remains inefficient even with modern tools.
3.1 Root Cause 1 — Data Without Interpretation
Existing tools (Jira, Trello, Asana, Monday.com) are excellent at storing structured data but provide no reasoning layer. A task board can show that a developer has 11 open tasks, but it will not say "this developer is overloaded relative to the sprint deadline and their historical velocity."
3.2 Root Cause 2 — Reactive, Not Predictive, Monitoring
Most reporting in project management tools is retrospective: burndown charts, sprint reports, and velocity charts describe what already happened. They rarely warn a manager about a risk before it materializes.
3.3 Root Cause 3 — Manual Cross-Referencing at Scale
Balancing workload requires cross-referencing multiple variables simultaneously: skill match, current load, deadlines, dependencies, and absences. A human can do this reliably for 5–6 people. Beyond that, mental cross-referencing becomes error-prone and slow.
3.4 Root Cause 4 — No Standardized Decision Support
When a manager does identify a problem, there is no structured recommendation to act on — no ranked options, no justification, no confidence level. Every redistribution decision is improvised.

4. Stakeholder Pain Points
4.1 Project Manager
Pain PointConsequenceCannot monitor multiple projects simultaneously with confidenceRisks are discovered lateNo early warning for overload or delayFirefighting instead of planningManual task redistributionTime-consuming, inconsistent, sometimes unfairNo historical basis for decisionsDecisions rely on intuition rather than data
4.2 Team Member
Pain PointConsequenceUnclear prioritization when workload shiftsConfusion, reduced focusOverload not recognized until burnout symptoms appearReduced well-being, lower quality outputBlockers not escalated quicklyWasted time waiting for unblocking
4.3 Executive Manager
Pain PointConsequenceNo real-time cross-project visibilityStrategic decisions based on outdated reportsRisk only visible after it becomes a missed deadlineReduced trust from clients/stakeholders

5. Quantifying the Problem
While IA TeamPilot is a prototype and not a production deployment with live customer data, the scale of the problem is well documented in the industry:

Frequent context-switching and unmanaged workload imbalance are widely cited as top contributors to reduced developer productivity and burnout in software teams.
Late detection of schedule risk is consistently identified as a leading cause of missed software delivery deadlines.
Manual status reporting and cross-referencing of task data consume a measurable share of a project manager's working week in teams without automated analysis tools.

For the purpose of this challenge, IA TeamPilot's seed data (Chapter 5 — Data Model, to be defined) will simulate a realistic team of ~20 employees across ~10 projects and ~150 tasks, large enough to make manual balancing genuinely difficult — and therefore large enough to demonstrate the value of automated analysis.

6. Competitive / Existing Solutions Landscape
CategoryExamplesStrengthLimitationTask boardsTrello, AsanaSimple, visualNo reasoning layerEnterprise PM suitesJira, Monday.comRich data, reportingReactive reporting onlyAI-augmented add-onsVarious Jira AI pluginsSome automationNarrow scope, not holistic workload reasoningGeneral-purpose chatbotsGeneric AI assistantsConversationalNo persistent understanding of team state, no proactive alerts
Gap identified: No mainstream tool combines continuous data monitoring, predictive risk detection, and explainable, actionable recommendations in one coordinated system that keeps the human in the loop.

7. Why AI Is the Right Approach (and Not Just a Trend)
AI is justified here specifically because the problem requires:

Pattern recognition across many variables at once (skills, load, deadlines, dependencies) — a task well-suited to machine reasoning, poorly suited to manual tracking at scale.
Natural language explanation of why a recommendation is made — which builds trust and allows human override, rather than a black-box automated reassignment.
Continuous evaluation rather than on-demand queries — the system should notice a risk before the manager asks about it.

This is precisely the reasoning underpinning IBM Bob's approach to embedding orchestration, execution, and governance directly into development workflows — the same principle IA TeamPilot applies to team coordination rather than to code generation alone.

8. Refined Problem Statement

Software team managers lack a system that continuously interprets project data to detect overload, predict delays, and recommend fair, justified task redistribution — forcing them to rely on manual, reactive, and error-prone judgment as team size and project complexity grow.


9. Assumptions and Constraints
9.1 Assumptions

Seed/demo data will realistically simulate a mid-sized software team (not live production data).
The MVP targets a single organization context (multi-tenant architecture is a possible future extension, not required for the Wildcard submission).
Users are already familiar with basic project management concepts (tasks, sprints, deadlines).

9.2 Constraints

Submission deadline: July 31, 2026.
Must visibly integrate IBM Bob in the development workflow (judging criterion: Technical Execution).
Must use at least one IBM AI-supported technology (Granite, LangFlow, Docling, or related).
Prototype must be a functioning proof of concept with a public GitHub repository — not a purely conceptual design.


10. How This Maps to the MVP Scope (Chapter 1, Section 14)
ProblemMVP Feature Addressing ItData without interpretationAI Workload Analysis moduleReactive monitoringContinuous risk/delay detectionManual cross-referencingAutomated task redistribution suggestionsNo decision supportRecommendation engine with explanation + confidence levelNo cross-project visibilityDashboard with KPIs and alerts

End of Chapter 2