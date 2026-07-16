16 — Testing Strategy
Version: 1.0
Document Type: Testing Strategy
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines how IA TeamPilot is tested end to end: unit tests for business rules, integration tests for the API, AI-specific validation testing, and manual test scenarios used to rehearse the live demo. It builds directly on the testing boundary already established in Chapter 11 §7 (AI calls mocked outside ai_engine).

2. Testing Layers Overview
LayerWhat It VerifiesToolingUnit testsBusiness rule formulas (Chapter 5) in isolationpytest / Django TestCaseIntegration testsAPI endpoints, permissions, request/response shapeDRF test clientAI validation testsPrompt output parsing, guardrails, fallback behaviorunittest.mock + fixturesManual scenario testsFull user flows across frontend + backend, used as demo rehearsalManual, scripted checklist

3. Unit Tests — Business Rules (Chapter 5 Coverage)
Each rule gets at least one test asserting the exact formula/threshold, not just "it returns something":
RuleTest CaseExpected ResultBR-1.2 (Workload %)User with 44h estimated effort, 40h capacity, 1-week sprint110%BR-1.3 (Status bands)Workload = 100%Status = "Overloaded" (boundary case)BR-1.4 (Alert throttle)Second overload event for same user within 24h, workload +10ppNo new alert (below 15pp re-trigger threshold)BR-4.2 (Risk bands)Score = 80Level = "Critical" (boundary case)BR-5.2 (Skill match)Candidate has 0 matching skillsExcluded from recommendation candidatesBR-5.5 (Human override)Recommendation createdstatus defaults to "PENDING", never auto-appliesBR-8.1 (Circular dependency)Task A depends on B, attempt B depends on ARejected with validation error
Rationale: boundary values (exactly 100%, exactly 80) are tested explicitly because off-by-one errors in threshold logic are the most common bug class in this kind of system, and they're also the easiest thing for a judge to spot-check live.

4. Integration Tests — API (Chapter 14 Coverage)
For each endpoint group, at minimum:
Test TypeExampleHappy pathPM creates a task with valid data → 201, task appears in project's task listPermission denialTeam Member attempts to create a project → 403Scope violationPM A requests PM B's project detail → 404 (not 403, per Chapter 14 §12)Validation errorTask set to BLOCKED without blocked_reason → 422Cascading effectTask reassigned → workload recalculated for both old and new assignee (verifies FR-WORK-005 fires correctly through the API, not just the service in isolation)

5. AI Validation Testing (Chapter 13 Coverage)
Since Granite/watsonx calls are non-deterministic and cost money/time, they are tested at two levels:
5.1 Mocked Chain Tests (run in CI, every commit)

Feed the validator (ai_engine/validators.py, Chapter 13 §5) a set of hand-crafted bad outputs — a justification referencing a name not in the input, an empty response, a response exceeding expected length — and assert each is correctly rejected and triggers the fallback template.
Feed it valid, well-formed outputs and assert they pass through unchanged.

5.2 Live Smoke Tests (run manually, not in CI, limited quota)

A small number of real calls to watsonx/Granite, run before key milestones (not on every commit, since Bob/watsonx quotas are limited — see Chapter 2 §9 constraints already noted by the developer directly), to confirm the actual model output still matches the expected shape and tone the prompts were designed for.
Results logged in meeting_notes/ai_smoke_test_log.md so prompt drift is tracked instead of tested tacitly.


6. Seed-Data-Driven Demo Test Scenarios
These are the scripted, repeatable scenarios used to rehearse the live demo (and to write the video script in Chapter 19). Each is designed to visibly trigger one part of the AI value loop using the seed data from Chapter 9 §14.
ScenarioDemonstratesChapter ReferenceOpen PM Dashboard → see CRM Redesign at 82% Critical riskContinuous risk monitoringUC-05Click into risk explanation → see the 3 contributing factors in plain languageExplainability (NFR-EXP-001)Chapter 13 §3.2Open Recommendation Inbox → see the David→Marie suggestion with justificationCore recommendation loopUC-03, UC-04Click Accept → task reassigns, both users notifiedHuman-in-the-loop controlBR-5.5Mark a task Blocked, wait (or fast-forward seed timestamp) past 24h → see it escalateReactive risk escalationUC-02Ask chat "Who is overloaded this week?" → get a grounded answerChat assistant, data-groundednessUC-06Kill the watsonx connection (simulate outage) → recommendation screen still shows fallback text, not an error pageGraceful degradationNFR-REL-001
The outage scenario is deliberately included as a demo moment, not just a technical safeguard — showing a judge that the system degrades gracefully rather than crashing is itself a credibility signal ("this team thought about failure modes").

7. What Is Explicitly Not Automated for the MVP
Per NFR out-of-scope items (Chapter 7 §9), the following are manually verified only, not covered by automated tests, given the July 31 deadline:

Cross-browser UI testing (manual check in Chrome only).
Load/performance testing beyond the seed-data scale.
Full end-to-end (Cypress/Playwright) test suite — manual scenario walkthroughs (Section 6) substitute for this in the MVP.


8. Test Coverage Target
Given the timeline, coverage effort is prioritized, not maximized uniformly:
PriorityCoverage TargetBusiness rule services (analytics, recommendations)High — these are the "brain" of the system and the most likely source of a demo-breaking bugAPI permission/scope logic (BR-7.1 enforcement)High — a visible security gap would undermine trust in front of judgesAI validators and fallback pathsHigh — directly protects the live demo from an AI outage or bad responseCRUD-only endpoints (basic create/edit)Medium — lower risk, well-trodden Django patternsFrontend componentsLow/manual — visual correctness checked by eye, not unit-tested, given the timeline

End of Chapter 16