07 — Non-Functional Requirements
Version: 1.0
Document Type: Non-Functional Requirements Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines the quality attributes IA TeamPilot must satisfy — performance, security, usability, reliability, and maintainability — as opposed to Chapter 6, which defines what the system does. Each NFR is numbered (NFR-XXX) and, where possible, measurable, so it can actually be verified rather than treated as an aspiration.

2. Performance
IDRequirementNFR-PERF-001Dashboard views shall load within 2 seconds under seed-data volume (~20 users, ~10 projects, ~150 tasks).NFR-PERF-002Workload and risk score recalculation shall complete within 3 seconds of a triggering event (task update, reassignment).NFR-PERF-003AI recommendation generation (Granite call via watsonx/LangChain) shall return within 8 seconds; the UI shall show a loading state beyond 1 second.NFR-PERF-004REST API endpoints shall respond within 500ms for non-AI operations (CRUD on tasks, projects, teams) under seed-data volume.

3. Security
IDRequirementNFR-SEC-001All API endpoints except registration/login shall require a valid JWT token.NFR-SEC-002Passwords shall be hashed (never stored in plaintext), using Django's default password hashing (PBKDF2 or stronger).NFR-SEC-003Role-based access control (BR-7.1) shall be enforced at the API level, not only hidden in the UI.NFR-SEC-004All AI prompts sent to Granite/watsonx shall exclude sensitive personal data beyond what is functionally necessary (name, skills, task data — no passwords, no private messages).NFR-SEC-005API keys and credentials (watsonx, IBM Bob integrations) shall be stored in environment variables, never committed to the GitHub repository.

4. Usability
IDRequirementNFR-USE-001The dashboard shall be understandable by a Project Manager within their first session, without requiring a manual (validated informally via a walkthrough during the demo video).NFR-USE-002Every AI recommendation shall display its justification in plain language, not raw scores alone (per BR-5.4, Transparency principle from Chapter 1 §9).NFR-USE-003The interface shall be responsive and usable on both desktop and tablet screen sizes (mobile is out of scope for MVP).

5. Reliability & Availability
IDRequirementNFR-REL-001If the AI service (Granite/watsonx) is unavailable, the system shall degrade gracefully — showing cached/last-known recommendations and a clear "AI temporarily unavailable" state, rather than crashing the dashboard.NFR-REL-002Core CRUD functionality (tasks, projects, teams) shall remain fully usable even if AI features are down.

6. Maintainability
IDRequirementNFR-MAINT-001Backend code shall follow Django app-per-domain structure (accounts, teams, projects, tasks, analytics, recommendations, notifications, chat), as defined in Chapter 1's architecture.NFR-MAINT-002Business rules (Chapter 5) shall be implemented as isolated, testable functions/services — not embedded directly in views — so AI logic can be updated without touching API routing.NFR-MAINT-003All AI prompts (for Granite via LangChain) shall be stored as versioned template files, not hardcoded inline strings, to allow iteration without code changes.

7. Explainability (AI-Specific — Core to the Wildcard Theme)
IDRequirementNFR-EXP-001Every AI-generated recommendation or risk score shall be traceable to the specific business rule(s) and data points that produced it (per BR-4.1, BR-5.4).NFR-EXP-002The system shall never apply an AI suggestion automatically without explicit human approval (hard constraint, per BR-5.5 — not just a UX preference).

8. Compliance with Challenge Constraints
IDRequirementNFR-COMP-001The development workflow shall visibly and demonstrably use IBM Bob (judging criterion: Technical Execution).NFR-COMP-002The solution shall use at least one IBM AI-supported technology (Granite via watsonx, and/or LangFlow).NFR-COMP-003The final submission shall include a public GitHub repository with a functioning prototype, not a purely conceptual design.NFR-COMP-004The project shall be submitted before the deadline (July 31, 2026, 11:59 PM ET, to be reconfirmed on the official platform).

9. Out of Scope for MVP (Explicitly Deferred)
To avoid scope creep under the July 31 deadline, the following are explicitly not NFR targets for this submission:

Horizontal scalability / multi-tenant load testing.
Full accessibility (WCAG) compliance.
Mobile-native apps.
Formal penetration testing (basic security hygiene only, per Section 3).
Multi-language i18n support.


End of Chapter 7