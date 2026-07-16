# Tech Stack: IA TeamPilot

Do not introduce a library or service not listed here without
updating this file and confirming it against `docs/10_System_Architecture.md`.

## Backend
- Python 3.11+
- Django + Django REST Framework
- PostgreSQL
- djangorestframework-simplejwt (JWT auth)
- python-dotenv (env vars, never committed)
- gunicorn + whitenoise (production only)

## Frontend
- React (Vite, not Create React App)
- Tailwind CSS (utility classes only — no Bootstrap, no MUI)
- Axios or fetch wrapper (`src/api/client.js`)
- No Redux, no Zustand — see `.ai/architecture.md` for state strategy

## AI
- LangChain (prompt templating and chain orchestration only —
  not multi-agent orchestration; three chains, single purpose each)
- IBM Granite via watsonx.ai (the only model provider used)

## Explicitly NOT Used (and why)
- **Celery / Redis** — not needed for MVP; periodic recalculation
  uses a management command + cron instead (`docs/11_Backend_Architecture.md` §5).
- **FAISS / SentenceTransformers / vector search** — no RAG or
  semantic search anywhere in this system; all three AI chains
  operate on structured data explicitly passed to them, not
  retrieved via embeddings.
- **WebSockets / Django Channels** — polling is sufficient for the
  MVP demo (`docs/12_Frontend_Architecture.md` §6).
- **Redux / any heavy client-state library** — server state is
  refetched, not cached client-side at scale.

## Dev Tools
- pytest / Django TestCase
- black, ruff (formatting/linting)
- IBM Bob — used for scaffolding, code review, test generation
  during development (see `.ai/prompts/bob.md`)

## Requirements Files
```
backend/requirements/
├── base.txt         # Django, DRF, psycopg, JWT, dotenv
├── local.txt         # base + dev tools
├── production.txt     # base + gunicorn, whitenoise
└── ai.txt              # LangChain, IBM watsonx SDK

frontend/package.json   # React ecosystem — never mixed into
                          # backend requirements/ files
```