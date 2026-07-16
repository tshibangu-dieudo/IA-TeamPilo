18 — GitHub Submission
Version: 1.0
Document Type: Repository & Submission Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines the exact structure of the public GitHub repository, the README content judges will read first, and how IBM Bob's usage is made visible and verifiable — since Technical Execution (a stated judging criterion) is partly assessed on demonstrated tool usage, not just the final code.

2. Repository Structure
IA-TeamPilot/
├── README.md                    ← judges read this first
├── LICENSE
├── .gitignore
│
├── docs/
│   ├── 01_Project_Vision.md
│   ├── 02_Problem_Analysis.md
│   ├── 03_Personas.md
│   ├── 04_User_Stories.md
│   ├── 05_Business_Rules.md
│   ├── 06_Functional_Requirements.md
│   ├── 07_Non_Functional_Requirements.md
│   ├── 08_Use_Cases.md
│   ├── 09_Database_Design.md
│   ├── 10_System_Architecture.md
│   ├── 11_Backend_Architecture.md
│   ├── 12_Frontend_Architecture.md
│   ├── 13_AI_Architecture.md
│   ├── 14_REST_API.md
│   ├── 15_UI_UX.md
│   ├── 16_Testing.md
│   ├── 17_Deployment.md
│   ├── 18_GitHub_Submission.md
│   └── 19_Pitch.md
│
├── backend/                     ← Django project (Chapter 11)
├── frontend/                    ← React project (Chapter 12)
│
├── diagrams/                    ← exported architecture/ER diagrams (images)
├── prompts/                     ← Bob/ChatGPT/Claude prompt files used during dev
│   ├── prompt_bob.md
│   └── prompt_claude.md
│
├── meeting_notes/                ← decision log, including ai_smoke_test_log.md (Chapter 16 §5.2)
│
└── demo/
    ├── demo_video_link.md
    └── screenshots/

3. README.md — Required Sections
The README is the single most important file for a judge skimming dozens of submissions. Structure:
markdown# IA TeamPilot

> AI-powered team coordination assistant for the IBM AI Builders
> Challenge 2026 — Wildcard: Build Intelligent Systems for the
> Future of Work.

🔗 **Live Demo:** [link]
🎥 **Demo Video:** [link]

## The Problem
[2-3 sentences from Chapter 2 §8 — Refined Problem Statement]

## What IA TeamPilot Does
[2-3 sentences from Chapter 1 §1 — Executive Summary]

## Demo Accounts
| Role | Email | Password |
|---|---|---|
| Project Manager | alice@demo.teampilot.io | ... |
| Team Member | david@demo.teampilot.io | ... |
| Executive Manager | grace@demo.teampilot.io | ... |
| Administrator | samuel@demo.teampilot.io | ... |

## Architecture
[System diagram from Chapter 10 §2, embedded as an image from /diagrams]

## Tech Stack
React · Django REST Framework · PostgreSQL · IBM Granite (watsonx) ·
LangChain · IBM Bob

## How IBM Bob Was Used
[See Section 4 below — this subsection is judged directly]

## Documentation
Full design documentation (20 chapters) is available in [`/docs`](./docs) —
start with [`01_Project_Vision.md`](./docs/01_Project_Vision.md).

## Local Setup
[Backend + frontend setup steps, pulled from Chapter 17 §5]

## Known Limitations
[From Chapter 17 §8 — stated transparently]

## License
[MIT or chosen license]

4. "How IBM Bob Was Used" — Section Content Strategy
This subsection is deliberately called out because it directly addresses NFR-COMP-001 (Chapter 7 §8) and the Technical Execution judging criterion. It should be specific, not a vague claim:
markdown## How IBM Bob Was Used

IBM Bob was used throughout the development workflow, distinct from
the runtime AI (Granite/watsonx) used by the deployed application:

- Scaffolded the initial Django app structure (`accounts`, `teams`,
  `projects`, `tasks`) from the specifications in docs/11_Backend_Architecture.md
- Generated DRF serializers and views from docs/14_REST_API.md
- Reviewed the business rule services (workload_service.py,
  risk_service.py) against docs/05_Business_Rules.md for correctness
- Generated unit test scaffolding for the business rule test cases
  listed in docs/16_Testing.md §3
Rationale: listing specific files/chapters Bob worked from (rather than "we used Bob a lot") gives judges something concrete and verifiable — they can open the referenced doc and the referenced code side by side.

5. Commit History as Evidence
Following the working method already agreed at the start of the project (small, chapter-scoped commits), the commit history itself becomes evidence of process quality:
Complete Project Vision documentation
Design database architecture
Implement authentication module
Implement task management module (Bob-assisted)
Implement workload calculation service
Add AI recommendation chain (LangChain + Granite)
Add fallback templates for AI outage handling
Frontend: recommendation inbox screen
Deploy: backend to Render, frontend to Vercel
Add demo seed data and demo accounts
Guidance: commit messages that reference which chapter/spec they implement (as shown above) make the repo self-documenting for a judge scanning the history — this is a small effort with disproportionate credibility payoff.

6. What Judges Are Likely to Check (Checklist Mirrored From Their Criteria)
Judging CriterionWhat to Make Easy to FindTechnical Execution"How IBM Bob Was Used" section; clean commit history; working live demoInnovationClear articulation of the "AI proposes, human decides" differentiator (Chapter 1 §13)Challenge FitExplicit Wildcard theme framing in README's first paragraphImplementation & FeasibilityWorking prototype link; Known Limitations section (honesty signal, Chapter 17 §8)

7. Pre-Submission Repository Checklist

 Repository set to Public.
 README renders correctly on GitHub (preview before submitting — broken image links are a common last-minute issue).
 All 19 doc chapters present and linked from README.
 .env / .env.local confirmed absent from git history (git log --all --full-history -- .env should return nothing).
 LICENSE file present.
 Live demo link and video link both work when tested in an incognito window (no cached login).


End of Chapter 18