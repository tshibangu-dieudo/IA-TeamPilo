# Glossary: IA TeamPilot

Terms used consistently across `/docs` and code. Use these exact
terms — do not introduce synonyms (e.g., always "workload
percentage," never "load score" or "utilization rate").

| Term | Definition |
|---|---|
| **Workload %** | A user's assigned effort vs. their capacity for the current sprint (BR-1.2). |
| **Risk Score** | 0–100% composite score estimating a project's probability of missing its deadline (BR-4.1). |
| **Recommendation** | An AI-generated, human-approvable suggestion to reassign a task (never auto-applied). |
| **Confidence Level** | High/Medium/Low rating on a recommendation, based on skill match and resulting workload (BR-5.4). |
| **Blocked Task** | A task manually marked Blocked by its assignee, with a required reason. |
| **Waiting on Dependency** | A task automatically flagged because a prerequisite task isn't Done — distinct from Blocked. |
| **Skill Gap** | Alert shown when no valid reassignment candidate exists for an overloaded member's task. |
| **Fallback Template** | A deterministic, rule-based explanation string used when the AI service is unavailable or its output fails validation. |
| **Human-in-the-loop** | Core design principle: the AI proposes, a human (PM) always decides. |
| **Wildcard Challenge** | The specific IBM AI Builders Challenge track this project targets: "Build Intelligent Systems for the Future of Work." |
| **Bob** | IBM's agentic development tool, used during the build process — distinct from Granite/watsonx, the runtime AI model used by the deployed app. |