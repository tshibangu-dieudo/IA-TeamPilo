17 — Deployment
Version: 1.0
Document Type: Deployment Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document defines how IA TeamPilot is deployed for judging: hosting choices, environment configuration, database setup, and the deployment checklist to run before submission. The goal is a reliable, always-accessible demo instance — judges may access the link at any time before the deadline, not just during a live presentation.

2. Deployment Requirements (Driven by the Challenge Constraints)
Per NFR-COMP-003 (Chapter 7 §8), the submission must include a public GitHub repository with a functioning prototype, not just a conceptual design. This implies two deliverables:

A public GitHub repo (source code + documentation).
A live, reachable deployment judges can open in a browser without setup.


3. Hosting Choices
Given the July 31 deadline and a solo developer, we prioritize simplicity and reliability over scalability — this is a demo instance, not a production system (per Chapter 7 §9, scalability testing is explicitly out of scope).
ComponentRecommended OptionWhyDjango backend + PostgreSQLRailway or Render (free/low-cost tier, both support PostgreSQL + Django out of the box)One-click deploy from GitHub, minimal DevOps overheadReact frontendVercel or NetlifyZero-config static/SPA hosting, automatic deploy on pushwatsonx / Granite accessIBM Cloud (watsonx.ai)Required — this is the actual model endpoint, not swappable
Note: exact platform choice (Railway vs. Render) should be finalized based on whichever offers the simplest PostgreSQL + Django deploy path when the developer is ready to deploy — both are equally valid options at this stage of planning.

4. Environment Variables (Production)
Mirrors the .env.example from Chapter 11 §8, with production values set in the hosting platform's dashboard (never committed):
DATABASE_URL=<provided by hosting platform>
SECRET_KEY=<generated, unique per environment>
DEBUG=False
ALLOWED_HOSTS=<production domain>
CORS_ALLOWED_ORIGINS=<frontend production URL>
WATSONX_API_KEY=<IBM Cloud API key>
WATSONX_PROJECT_ID=<watsonx project ID>
WATSONX_URL=<watsonx endpoint URL>

5. Deployment Steps (Checklist)
5.1 Backend

Provision PostgreSQL instance on hosting platform.
Set environment variables (Section 4).
Run migrations: python manage.py migrate.
Run seed data script (Chapter 9 §14): python seed/generate_seed_data.py.
Create a demo admin account for judges (documented in README, Chapter 20).
Verify /api/v1/auth/login responds correctly.

5.2 Frontend

Set VITE_API_BASE_URL to the deployed backend URL.
Build: npm run build.
Deploy build output to Vercel/Netlify.
Verify login flow works end-to-end against the live backend.

5.3 AI Layer

Confirm watsonx credentials are valid in the production environment (not just local .env).
Run one live smoke test per chain (Chapter 16 §5.2) against the deployed instance specifically — a working local AI call does not guarantee the deployed environment's network/credentials are correctly configured.


6. Demo Account Strategy
To let judges explore without needing to register, the seed data (Chapter 9 §14) includes pre-created accounts covering each persona:
RoleEmail (example)PurposeProject Manageralice@demo.teampilot.ioPrimary judging account — full recommendation/risk flowTeam Memberdavid@demo.teampilot.ioShows the "overloaded" side of the storyExecutive Managergrace@demo.teampilot.ioPortfolio viewAdministratorsamuel@demo.teampilot.ioTeam/skill management
Credentials are documented in the README (Chapter 20) with a clearly labeled "Demo Accounts" section — judges should never have to guess or ask.

7. Pre-Submission Verification Checklist
Run this checklist within 24 hours of the July 31 deadline, not the night before it's too late to fix anything:

 Live URL loads without errors on first visit (cold start).
 All 4 demo accounts (Section 6) log in successfully.
 Seed data is present and shows a realistic mix (some healthy projects, at least one Critical-risk project — per Chapter 9 §14).
 Recommendation Inbox shows at least one pending recommendation with a real (or fallback) justification.
 Chat panel returns a grounded answer to at least one test question.
 Simulated AI outage (Chapter 16 §6) correctly falls back without crashing.
 GitHub repo is public, README is complete (Chapter 20), and the live URL is linked at the top.
 .env / credentials are confirmed not committed anywhere in the repo history.


8. Known Limitations (Documented Transparently, Not Hidden)
Consistent with Chapter 7 §9 (explicitly deferred scope), the README and this document should state plainly:

Single-organization deployment only (no multi-tenant isolation).
Polling-based updates, not real-time WebSockets (Chapter 12 §6).
No automated cross-browser testing performed (Chapter 16 §7).

Stating limitations directly is intentional — judges evaluating "Implementation & Feasibility" tend to trust a team that clearly knows its own boundaries more than one that implies the prototype is production-ready when it isn't.