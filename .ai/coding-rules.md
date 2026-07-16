# Coding Rules: IA TeamPilot

Rules any AI assistant (or human) must follow when writing code for
this project. These are enforceable, not aspirational — code
reviews (human or Bob-assisted) check against this list.

## Backend (Django)
1. Business logic lives in `services.py` / `services/` — never in
   views. Views stay thin: validate request, call service, return
   response.
2. Every model uses a UUID primary key, not auto-increment integer.
3. Every model has `created_at` (and `updated_at` where the record
   is mutable).
4. No hard deletes on user-facing data — prefer status/archived
   flags where a use case requires it (see `docs/09_Database_Design.md`
   for which entities this applies to; not a blanket rule for every table).
5. Permission checks happen server-side, in DRF permission classes —
   never trust the frontend to enforce access control.
6. `ai_engine/` never imports Django models. It receives and returns
   plain Python dicts only.
7. Every business rule formula (Chapter 5) gets at least one unit
   test, including boundary values (e.g., exactly 100% workload).
8. Prompts for LangChain live in `ai_engine/prompts/*.txt` — never
   as inline Python strings.
9. Secrets and API keys are read from environment variables only —
   never hardcoded, never committed (`.env` is gitignored).

## Frontend (React)
1. TypeScript is not currently in scope — the project uses plain
   JS/JSX per `docs/12_Frontend_Architecture.md`. Do not introduce
   TypeScript without updating that chapter and `.ai/tech-stack.md` first.
2. Tailwind utility classes only — no custom CSS files beyond the
   Tailwind entrypoint.
3. Components that render AI output (recommendation justification,
   risk explanation) must always display the explanation text
   visibly — never hide it behind a tooltip or "details" toggle.
4. `ProtectedRoute` is a UX convenience, not a security boundary —
   never assume frontend route-guarding is sufficient on its own.

## General
1. No code is written before checking the relevant `/docs` chapter
   or `.ai/` file exists and has been read.
2. If a task requires a decision not covered in `/docs` or `.ai/`,
   stop and ask — do not invent architecture or business rules.
3. Follow SOLID principles where they add clarity; do not
   over-engineer abstractions for a system of this scope.
4. Every commit message should reference the doc chapter or feature
   it implements (see `docs/18_GitHub_Submission.md` §5 for examples).
5. Write tests for business rules and AI validators before writing
   tests for simple CRUD — prioritize per `docs/16_Testing.md` §8.