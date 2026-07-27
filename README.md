# IA TeamPilot

**AI-powered team coordination assistant** — built for the IBM AI Builders Challenge 2026, Wildcard track: *"Build Intelligent Systems for the Future of Work."*

> The AI proposes, the human decides. TeamPilot AI never applies a change automatically.

---

## 1. Overview

IA TeamPilot continuously analyzes a development team's workload and project data, detects overload and delay risks before they happen, and recommends concrete task redistributions — each one justified in plain language by IBM Granite and requiring explicit Project Manager approval before anything changes.

## 2. The Problem

Project managers usually discover overload, blockers, and delays *after the fact* — during a standup, or worse, at the deadline. Existing tools (Jira, Trello, Asana) store task data but don't interpret it: the manager has to mentally cross-reference deadlines, availability, skills, and workload to catch a problem early. That cognitive load grows with team size and number of concurrent projects.

Full analysis: [`docs/02_Problem_Analysis.md`](docs/02_Problem_Analysis.md)

## 3. Features

### Authentication & Access Control
- **JWT-based authentication** with secure token refresh
- **Role-based access control** (BR-7.1): Admin, Project Manager, Team Member, Executive Manager
- **Scope isolation**: users only see data relevant to their role (404 on scope violations, never 403)

### Team & Project Management
- **Team management**: create teams, assign members with roles (lead/member), manage skills
- **Project lifecycle**: create/update/delete projects with start/end dates, status tracking (planning/active/on_hold/completed)
- **Skills registry**: define organizational skills, assign to users with proficiency levels (1-5)

### Task Management
- **Task CRUD** with assignees, priorities (Critical/High/Medium/Low), effort estimates, deadlines
- **Task dependencies**: define prerequisite relationships with circular dependency prevention (BR-8.1)
- **Status tracking**: todo → in_progress → blocked → done, with full history
- **Blocked task rules** (BR-3.1): blocked status requires mandatory reason, auto-escalates to PM after 24h
- **Auto-priority escalation** (BR-2.2): tasks due within 48h escalate one priority level (unless already Critical)
- **Dependency blocking** (BR-3.3): tasks automatically flagged "waiting on dependency" when prerequisite not done

### Workload Analytics
- **Real-time workload calculation** (BR-1.2): `workload% = (sum of effort hours in sprint window) / (weekly capacity × sprint weeks) × 100`
- **Status bands** (BR-1.3):
  - 0–60%: Underloaded (blue)
  - 61–99%: Balanced (green)
  - 100–120%: Overloaded (orange)
  - >120%: Critically Overloaded (red)
- **Per-project and team-wide views** for Project Managers
- **Individual workload view** for Team Members (cannot see others' individual workloads)

### Risk Scoring
- **Weighted composite risk score** (BR-4.1): `risk = 0.35×overload + 0.30×blocked_tasks + 0.20×deadline_proximity + 0.15×velocity`
- **Risk level bands** (BR-4.2):
  - 0–29%: Low (green)
  - 30–59%: Moderate (yellow)
  - 60–79%: High (orange)
  - 80–100%: Critical (red)
- **Automatic recalculation** on task changes + scheduled every 6 hours
- **AI-generated explanations** of risk factors via IBM Granite (with deterministic fallback)

### AI-Powered Recommendations
- **Task reassignment suggestions** triggered when:
  - At least one team member is overloaded/critically overloaded (BR-5.1)
  - At least one teammate has capacity to spare
  - Candidate has matching skills for the task (BR-5.2)
- **Candidate ranking** (BR-5.3): highest skill match → lowest workload → fewest blocked tasks
- **Confidence levels** (BR-5.4): High/Medium/Low based on skill match quality and resulting workload
- **IBM Granite justifications**: natural-language explanation for each recommendation
- **Human-in-the-loop approval** (BR-5.5): recommendations NEVER applied automatically — explicit PM accept/reject required
- **Graceful degradation**: if Granite unavailable, uses deterministic template explanations

### Notifications
- **Event-driven notifications** (BR-6.1):
  - Task reassigned → Team Member (in-app + email)
  - New recommendation generated → Project Manager
  - Task blocked >24h → Project Manager
  - Project risk reaches Critical → PM + Executive Manager
- **Intelligent throttling** (BR-6.2): max 1 notification per (user, type, object) per 60 minutes
- **Mark read/unread** with read timestamps
- **Bulk mark all read** for inbox management

### AI Chat Assistant
- **IBM Granite-powered conversational interface** for Project Managers and Executives
- **Full business context**: queries grounded in user's scoped data (projects, teams, members, tasks, skills, workload, risk, recommendations)
- **Enriched data snapshot**:
  - Members with workload percentages, status, and skills
  - Categorized tasks: blocked (top 10), overdue (top 10), high-priority (top 10)
  - Per-status task counts (todo, in_progress, blocked, done, total_open)
  - Risk factor breakdown with pending recommendations
  - Organization summary for cross-project queries (admin/executive/PM)
- **Causal analysis**: answers "why" questions about risk, overload, and blockers
- **Conversation history**: persistent conversations with automatic truncation (last 10 turns)
- **Graceful fallback**: when AI unavailable, returns "Données insuffisantes" instead of crashing
- **BR-7.1 security scoping**: members cannot access chat (403), PM/admin/exec see only their authorized projects

### Role-Aware Dashboards
- **Project Manager Dashboard**:
  - Projects summary with risk scores (sorted by risk descending)
  - Personal workload card
  - Top AI recommendations inbox
  - Pending recommendations count
  - Unread notifications count
- **Team Member Dashboard**:
  - Personal workload with progress bar
  - My upcoming tasks (sorted by deadline)
  - Task breakdown by status (todo/in_progress/blocked/waiting)
  - Done tasks excluded from summary
- **Executive Dashboard**:
  - Portfolio view (all projects, cross-organizational)
  - Projects sorted by risk (highest first)
  - Read-only access to all organizational data
- **Admin Dashboard**:
  - Full organizational visibility
  - User/team/skill management access

## 4. AI Architecture

TeamPilot AI uses **IBM Granite** (via **watsonx.ai**) for exactly three purposes:

### The Three AI Chains

1. **Recommendation Justification Chain**
   - **Purpose**: Explains *why* a task reassignment is suggested
   - **Input**: Overloaded member, candidate, task, ranking reason
   - **Output**: 2-3 sentence natural-language justification
   - **Guardrail**: References only data from input; rejects hallucinations

2. **Risk Explanation Chain**
   - **Purpose**: Explains *why* a project's risk score is what it is
   - **Input**: Pre-computed risk score + factor breakdown
   - **Output**: Plain-language explanation of top risk contributors
   - **Guardrail**: Never recomputes score; only explains existing value

3. **Chat Assistant Chain**
   - **Purpose**: Answers scoped questions about user's own project data
   - **Input**: User question + server-assembled data snapshot (never raw DB)
   - **Output**: Grounded answer or explicit "data not available"
   - **Guardrail**: No cross-project leakage; refuses when data missing

### Core Design Principle

**"The AI proposes, the human decides."**

- **Numeric values** (workload %, risk score) are **always computed by Python business rules** (BR-1.2, BR-4.1) — never by the AI
- **Natural-language explanations** are generated by IBM Granite — with deterministic fallback templates when AI unavailable
- **Data modifications** require explicit human approval (BR-5.5) — AI never writes to database
- **Database isolation**: AI chains never query database directly; only receive explicitly-scoped data from service layer

This architecture ensures that AI failures degrade explanation quality, never correctness of underlying calculations.

Full detail: [`docs/13_AI_Architecture.md`](docs/13_AI_Architecture.md)

## 5. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 4.2+, Django REST Framework 3.14+ |
| Database | PostgreSQL 15+ |
| Authentication | djangorestframework-simplejwt (JWT with refresh tokens) |
| Frontend | React 18+ (Vite), Tailwind CSS 3+, React Router 6+, Axios |
| AI | LangChain 0.1+ (prompt orchestration), IBM watsonx Python SDK 1.0+ |
| AI Model | IBM Granite (granite-13b-chat-v2 or granite-4-h-small) via watsonx.ai |
| Testing | pytest 7+, Django TestCase, 220+ automated tests |
| Dev Tools | black, ruff, python-dotenv |

### Deliberately NOT Used (and why)

These exclusions are architectural decisions, not limitations:

- **Celery / Redis** — Not needed for MVP; periodic risk recalculation uses Django management command + cron instead (see `docs/11_Backend_Architecture.md` §5)
- **FAISS / SentenceTransformers / vector search** — No RAG or semantic search; all three AI chains operate on structured data explicitly passed to them, not retrieved via embeddings
- **WebSockets / Django Channels** — Polling (15-30s) sufficient for MVP demo; real-time not critical for this use case (see `docs/12_Frontend_Architecture.md` §6)
- **Redux / Zustand** — Server state refetched on navigation; no heavy client-side state caching needed
- **TypeScript** — Plain JavaScript chosen for faster prototyping; type safety enforced via comprehensive test suite instead

See [`.ai/tech-stack.md`](.ai/tech-stack.md) for full rationale.

## 6. Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- IBM watsonx.ai account with API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements/local.txt
pip install -r requirements/ai.txt
```

### Environment Configuration

Create `backend/.env` from template:

```bash
cp .env.example .env
```

**Required environment variables**:

```ini
# Django
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=teampilot_db
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

# IBM watsonx.ai (required for AI features)
WATSONX_API_KEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-4-h-small
```

> **Note**: AI features (recommendations, risk explanations, chat assistant) require valid IBM watsonx credentials. Without them, the system falls back to deterministic template explanations for recommendations and risk, and chat returns "Données insuffisantes".

### Database Initialization

```bash
python manage.py migrate
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```ini
VITE_API_BASE_URL=http://localhost:8000/api
```

```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 7. Demo / Try It Yourself

### Populate Demo Data

```bash
cd backend
python manage.py seed_demo
```

This creates a realistic demo organization with:
- 12 users across 3 teams
- 4 projects (1 at CRITICAL risk, 3 at LOW risk)
- Multiple tasks with dependencies, blocked status, and varying workloads
- Pre-computed workload snapshots and risk scores
- Sample recommendations

### Demo Accounts

| Role | Username | Password | What to Try |
|------|----------|----------|-------------|
| **Admin** | `demo_admin` | `Demo1234!` | Full organizational visibility; manage users, teams, skills |
| **Project Manager** | `demo_alice.pm` | `Demo1234!` | Review AI recommendations for "CRM Platform Rewrite" (CRITICAL risk 85.2%); accept/reject task reassignments; use chat assistant to query team status |
| **Team Member** | `demo_david.chen` | `Demo1234!` | View personal workload (critically overloaded at 127.5% on CRM); see assigned tasks; cannot access recommendations or chat |
| **Executive** | `demo_grace.exec` | `Demo1234!` | Portfolio dashboard with all 4 projects; cross-project risk visibility; read-only access; use chat for org-wide queries |

### Key Demo Scenarios

1. **Login as `demo_alice.pm`** (Project Manager)
   - Dashboard shows "CRM Platform Rewrite" at CRITICAL risk (85.2%)
   - Click "AI Recommendations" to see task reassignment suggestions
   - Read IBM Granite justifications for each recommendation
   - Accept a recommendation to see task reassignment in action
   - Use Chat Assistant: ask "Qui est surchargé dans mon équipe ?" to see that all 5 CRM team members are overloaded (127.5%, 110%, 110%, 100%, 100%)

2. **Login as `demo_david.chen`** (Team Member - Critically Overloaded)
   - Personal workload shows 127.5% (critically overloaded, red bar)
   - Task list shows multiple CRITICAL/HIGH priority items with tight/past deadlines
   - Status breakdown shows 4 blocked tasks contributing to project risk

3. **Login as `demo_grace.exec`** (Executive - Portfolio View)
   - Portfolio table shows all 4 projects sorted by risk
   - "CRM Platform Rewrite" (CRITICAL ~85%) at top with red badge
   - Use Chat: ask "Quels projets sont à risque ?" for cross-project risk analysis

4. **Reset Demo Data**
   ```bash
   python manage.py seed_demo --reset
   ```

## 8. Project Structure

```
IA-TeamPilot/
├── .ai/                        # Condensed context for AI assistants
│   ├── architecture.md         # System design quick reference
│   ├── business-rules.md       # Core formulas & thresholds
│   ├── coding-rules.md         # Coding standards
│   ├── glossary.md             # Domain terminology
│   ├── project.md              # Project overview
│   └── tech-stack.md           # Technology decisions
├── docs/                       # Full 18-chapter specification
│   ├── 01_projet_vision.md
│   ├── 02_problem_analysis.md
│   ├── 05_bussiness_rules.md  # Complete business rule formulas
│   ├── 13_AI_Architecture.md  # AI chain design & prompts
│   └── ...
├── backend/                    # Django + DRF + AI engine
│   ├── apps/                   # Django apps (accounts, teams, projects, tasks, analytics, recommendations, notifications, chat)
│   ├── ai_engine/              # LangChain + Granite integration
│   │   ├── langchain_client.py
│   │   ├── chains.py
│   │   ├── chat_service.py
│   │   └── prompts/            # Versioned prompt templates
│   ├── config/                 # Django settings
│   ├── requirements/           # Pip dependencies (base, local, production, ai)
│   └── manage.py
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── api/                # API client per resource
│   │   ├── auth/               # AuthContext, ProtectedRoute
│   │   ├── pages/              # Page components (dashboard, tasks, recommendations, chat, etc.)
│   │   ├── components/         # Reusable UI components
│   │   ├── hooks/              # Custom React hooks
│   │   └── utils/              # Helpers (errorMessage, etc.)
│   └── package.json
├── dev-notes/                  # Development reports (gitignored)
├── README.md
└── LICENSE
```

Detailed backend structure: [`docs/11_Backend_Architecture.md`](docs/11_Backend_Architecture.md)  
Detailed frontend structure: [`docs/12_Frontend_Architecture.md`](docs/12_Frontend_Architecture.md)

## 9. Useful Commands

### Backend

| Command | Description |
|---|---|
| `python manage.py runserver` | Start Django dev server (port 8000) |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create new migrations from model changes |
| `python manage.py test` | Run full test suite (220+ tests) |
| `python manage.py seed_demo` | Populate demo data |
| `python manage.py seed_demo --reset` | Wipe and reseed demo data |
| `python manage.py check` | Validate Django configuration |
| `black . && ruff check .` | Format & lint backend code |

### Frontend

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server (port 5173) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |

### Scheduled Tasks (Production)

```bash
# Recalculate risk scores for all projects (run every 6 hours via cron)
python manage.py recalculate_risk

# Check blocked tasks and notify PMs (run daily)
python manage.py check_blocked_tasks
```

## 10. Test Coverage

**220+ automated tests** covering:

- ✅ **Business rule validation** (BR-1.1 through BR-8.2)
- ✅ **Boundary value testing** for thresholds (workload bands, risk bands, priority escalation timing)
- ✅ **Permission & scope isolation** (BR-7.1) — every app with user-scoped data tested for 404 on violations
- ✅ **AI chain behavior** — both successful Granite responses and fallback templates
- ✅ **Notification throttling** (BR-6.2)
- ✅ **Circular dependency prevention** (BR-8.1)
- ✅ **Role-based dashboard payloads** (PM, Member, Executive, Admin)
- ✅ **Chat assistant scoping** — cross-project isolation, enriched snapshot validation

Run tests:
```bash
cd backend
python manage.py test
# or
pytest
```

Test strategy: [`docs/16_Testing.md`](docs/16_Testing.md)

## 11. Deployment

Deployment configuration and production checklist: [`docs/17_Deployment.md`](docs/17_Deployment.md)

**Production considerations**:
- Use `requirements/production.txt` (includes gunicorn, whitenoise)
- Set `DEBUG=False` in production `.env`
- Configure `ALLOWED_HOSTS` with your domain
- Use strong `SECRET_KEY` (never commit)
- Set up PostgreSQL with SSL
- Configure watsonx API rate limits for production usage
- Set up cron jobs for `recalculate_risk` and `check_blocked_tasks`
- Serve frontend static files via CDN or reverse proxy (nginx)

## 12. IBM watsonx Integration Details

### API Configuration

TeamPilot AI connects to IBM watsonx.ai using the **IBM watsonx Python SDK** via **LangChain**:

```python
from langchain_ibm import WatsonxLLM

llm = WatsonxLLM(
    model_id=os.getenv('GRANITE_MODEL_ID', 'ibm/granite-13b-chat-v2'),
    url=os.getenv('WATSONX_URL'),
    apikey=os.getenv('WATSONX_API_KEY'),
    project_id=os.getenv('WATSONX_PROJECT_ID'),
    params={
        "decoding_method": "sample",
        "max_new_tokens": 200,
        "temperature": 0.3,
    }
)
```

### Model Used

**`ibm/granite-4-h-small`** — Default model configured in production (see `backend/.env.example` and `backend/config/settings.py`)

> **Note**: The code defaults to `ibm/granite-13b-chat-v2` if `GRANITE_MODEL_ID` is not set, but the project's standard configuration uses `ibm/granite-4-h-small` which has been tested and confirmed working with HTTP 200 responses from watsonx.ai.

### Prompt Engineering

All prompts stored as versioned templates in `backend/ai_engine/prompts/`:
- `recommendation_prompt.txt` — Task reassignment justification
- `risk_explanation_prompt.txt` — Risk score explanation
- `chat_prompt.txt` — Conversational assistant with business data context

**Prompt structure**:
1. Clear role definition ("You are explaining...", "You do NOT decide...")
2. Structured input data (JSON-like format)
3. Explicit constraints ("Do not invent data...", "Reference only...")
4. Output format specification

### Graceful Degradation

When IBM watsonx is unavailable (network error, rate limit, invalid credentials):
- **Recommendations**: Use deterministic template: `"Reassign {task} from {overloaded_user} to {candidate} (skill match: {skills}, resulting workload: {pct}%)"`
- **Risk explanations**: Use factor breakdown template: `"Risk is {level} due to: {factor_list}"`
- **Chat assistant**: Return `"Données insuffisantes"` message

No crashes, no blocking of core CRUD operations.

Full AI architecture: [`docs/13_AI_Architecture.md`](docs/13_AI_Architecture.md)

## 13. Repository Organization

The **`docs/` folder** contains the complete 18-chapter specification, written before implementation began.

The **`.ai/` folder** is a condensed, always-relevant reference kept in sync with `docs/` — used by AI coding assistants (Claude, ChatGPT, IBM Bob) so they never invent architecture or business rules that aren't documented.

See [`docs/18_GitHub_Submission.md`](docs/18_GitHub_Submission.md) for commit conventions and repository structure rationale.

The **`dev-notes/` folder** (gitignored) contains sprint reports, bug fix summaries, and audit reports from the development process — not part of the submission repository.

## 14. Business Rules Reference

Key business rules (full spec in [`docs/05_bussiness_rules.md`](docs/05_bussiness_rules.md)):

- **BR-1.2**: Workload % formula
- **BR-1.3**: Workload status bands (0-60% underloaded, 61-99% balanced, 100-120% overloaded, >120% critically overloaded)
- **BR-2.2**: Priority auto-escalation (tasks due within 48h escalate one level)
- **BR-3.1**: Blocked tasks require mandatory reason field
- **BR-4.1**: Risk score weighted formula (35% overload, 30% blocked tasks, 20% deadline proximity, 15% velocity)
- **BR-4.2**: Risk level bands (0-29% low, 30-59% moderate, 60-79% high, 80-100% critical)
- **BR-5.5**: Human override rule — recommendations NEVER applied automatically
- **BR-6.2**: Notification throttling (max 1 per user/type/object per 60 minutes)
- **BR-7.1**: Data visibility scope by role (404 on violations, not 403)
- **BR-8.1**: Circular dependency prevention

## 15. Contributors

- **Tshibangu Dieudo** — Full-stack development, AI integration, system architecture

## 16. License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

**Built for the IBM AI Builders Challenge 2026** | Powered by IBM Granite via watsonx.ai
