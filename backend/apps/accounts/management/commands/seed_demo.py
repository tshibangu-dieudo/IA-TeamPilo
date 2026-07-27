"""
Demo seed data management command for TeamPilot AI hackathon pitch.

Usage:
    python manage.py seed_demo           # seed (skips if demo data already exists)
    python manage.py seed_demo --reset   # wipe demo data then reseed

Workload formula (BR-1.2):
  workload% = sum(effort of open tasks with deadline in sprint window)
              / (40h × sprint_weeks) × 100

All workload snapshots use SPRINT_START=today-7 to SPRINT_END=today+7 (2 weeks).
capacity_for_sprint = 40h × 2 = 80h.

Target workloads for demo (all REAL calculations, no overrides):
  david (critically_overloaded): 102h → 127.5% (>120% = red bar)
  alice (overloaded):             88h → 110.0% (100-120% = orange)
  marie (overloaded):             88h → 110.0% (100-120% = orange)
  lucas (overloaded):             80h → 100.0% (100-120% = orange)
  omar (overloaded):              80h → 100.0% (100-120% = orange)

With 5/5 members overloaded → overload_factor = 100% → risk = 85% (CRITICAL)

Risk formula (BR-4.1):
  risk = 0.35×overload + 0.30×blocked + 0.20×deadline_proximity + 0.15×velocity(1.0)

CRM target CRITICAL (≥80):
  overload≥20% (david critically_overloaded = contributes to overload_factor)
  blocked=100 (all open tasks blocked)
  deadline_proximity=100 (past deadline)
  → 0.35×X + 0.30×100 + 0.20×100 + 0.15 = 65 + 0.35×X → need X≥43 for ≥80 total
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_PASSWORD = 'Demo1234!'
DEMO_TAG = 'demo_'

# 2-week current sprint window — all workload-bearing task deadlines must fall here
SPRINT_START = date.today() - timedelta(days=7)
SPRINT_END   = date.today() + timedelta(days=7)


def _d(n):
    return date.today() + timedelta(days=n)


class Command(BaseCommand):
    help = 'Seed realistic demo data for the hackathon pitch.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete all previously seeded demo data before reseeding.')

    def handle(self, *args, **options):
        if options['reset']:
            self._reset()
        if User.objects.filter(username__startswith=DEMO_TAG).exists():
            self.stdout.write(self.style.WARNING(
                'Demo data already exists. Run with --reset to wipe and reseed.'))
            return
        self.stdout.write('Seeding demo data...\n')
        self._seed()

    # ------------------------------------------------------------------ reset

    def _reset(self):
        self.stdout.write('Resetting demo data...')
        count = User.objects.filter(username__startswith=DEMO_TAG).count()
        User.objects.filter(username__startswith=DEMO_TAG).delete()
        from apps.teams.models import Team, Skill
        Team.objects.filter(name__startswith='[DEMO]').delete()
        Skill.objects.filter(name__in=[
            'Python','Django','React','PostgreSQL','DevOps','UI/UX','Node.js','Docker'
        ]).delete()
        self.stdout.write(self.style.SUCCESS(
            f'  Removed {count} demo users and all related data.\n'))

    # ------------------------------------------------------------------ seed

    def _seed(self):
        from apps.accounts.services import add_user_skill_service
        from apps.teams.services import create_team_service, add_team_member_service, create_skill_service
        from apps.projects.services import create_project_service
        from apps.tasks.services import create_task_service, update_task_status_service, add_task_dependency_service
        from apps.analytics.services import create_workload_snapshot_service, calculate_risk_score_service
        from apps.recommendations.services import generate_recommendations_for_project_service
        from apps.notifications.services import create_notification_service
        from apps.chat.models import Conversation, ChatMessage

        # ── 1. Skills ──────────────────────────────────────────────────────────
        self.stdout.write('  Creating skills...')
        for name, desc in [
            ('Python','Backend development with Python'),
            ('Django','Django REST Framework'),
            ('React','React frontend development'),
            ('PostgreSQL','Database design and queries'),
            ('DevOps','CI/CD, Docker, infrastructure'),
            ('UI/UX','Interface design and user experience'),
            ('Node.js','Backend JavaScript'),
            ('Docker','Containerisation'),
        ]:
            create_skill_service(name, desc)

        # ── 2. Users ───────────────────────────────────────────────────────────
        self.stdout.write('  Creating users...')

        def mkuser(uname, first, last, role, skill_names):
            u = User.objects.create_user(
                username=f'demo_{uname}', email=f'{uname}@teampilot.demo',
                password=DEMO_PASSWORD, first_name=first, last_name=last, role=role)
            for i, s in enumerate(skill_names):
                add_user_skill_service(u, s, proficiency_level=min(5, 3 + i % 3))
            return u

        admin = mkuser('admin',      'Samuel','Nkosi',    'admin',     ['Python','DevOps','Docker'])
        alice = mkuser('alice.pm',   'Alice', 'Kamana',   'pm',        ['Python','Django','PostgreSQL'])
        bob   = mkuser('bob.pm',     'Bob',   'Tremblay', 'pm',        ['React','Node.js','UI/UX'])
        grace = mkuser('grace.exec', 'Grace', 'Chen',     'executive', ['Python','DevOps'])
        henry = mkuser('henry.exec', 'Henry', 'Osei',     'executive', ['PostgreSQL'])
        david = mkuser('david.chen', 'David', 'Chen',     'member',    ['Python','Django','PostgreSQL'])
        marie = mkuser('marie.t',    'Marie', 'Thériault','member',    ['Django','PostgreSQL','React'])
        jean  = mkuser('jean.p',     'Jean',  'Petit',    'member',    ['DevOps','Docker'])
        sarah = mkuser('sarah.kim',  'Sarah', 'Kim',      'member',    ['React','UI/UX'])
        lucas = mkuser('lucas.silva','Lucas', 'Silva',    'member',    ['Python','Django'])
        priya = mkuser('priya.m',    'Priya', 'Mehta',    'member',    ['React','Node.js','UI/UX'])
        omar  = mkuser('omar.diallo','Omar',  'Diallo',   'member',    ['Python','PostgreSQL','DevOps'])

        # ── 3. Teams ───────────────────────────────────────────────────────────
        self.stdout.write('  Creating teams...')
        backend  = create_team_service('[DEMO] Backend Squad',  'Python/Django backend engineers')
        frontend = create_team_service('[DEMO] Frontend Squad', 'React & UI/UX specialists')
        platform = create_team_service('[DEMO] Platform Squad', 'DevOps and infrastructure')

        for u, r in [(alice,'lead'),(david,'member'),(marie,'member'),(lucas,'member'),(omar,'member')]:
            add_team_member_service(backend, u, r)
        for u, r in [(bob,'lead'),(sarah,'member'),(priya,'member')]:
            add_team_member_service(frontend, u, r)
        for u, r in [(alice,'lead'),(jean,'member'),(omar,'member')]:
            add_team_member_service(platform, u, r)

        # ── 4. Projects ────────────────────────────────────────────────────────
        self.stdout.write('  Creating projects...')

        # CRM: past deadline → deadline_proximity_factor = 100
        crm = create_project_service(
            name='CRM Platform Rewrite',
            description='Full rewrite of legacy CRM. Stalled due to API blockers.',
            start_date=_d(-60), end_date=_d(-3),
            owner=alice, team=backend, status='active')

        # API GW: tight deadline + heavy load → HIGH
        api_gw = create_project_service(
            name='API Gateway Migration',
            description='Migrate REST endpoints to new API Gateway with rate limiting.',
            start_date=_d(-14), end_date=_d(8),
            owner=alice, team=backend, status='active')

        # Mobile: moderate progress
        mobile = create_project_service(
            name='Mobile App Redesign',
            description='UI/UX overhaul of the customer-facing mobile application.',
            start_date=_d(-14), end_date=_d(21),
            owner=bob, team=frontend, status='active')

        # Infra: healthy
        infra = create_project_service(
            name='Infrastructure Modernisation',
            description='Docker containerisation and CI/CD pipeline setup.',
            start_date=_d(-7), end_date=_d(45),
            owner=alice, team=platform, status='active')

        # ── 5. Tasks ───────────────────────────────────────────────────────────
        # All workload-bearing deadlines in [SPRINT_START, SPRINT_END] = [_d(-7), _d(7)]
        # Target workloads (REAL calculations):
        #   david:  102h → 127.5% critically_overloaded
        #   alice:   76h →  95.0% balanced
        #   marie:   68h →  85.0% balanced
        #   lucas:   48h →  60.0% underloaded
        #   omar:    32h →  40.0% underloaded
        self.stdout.write('  Creating tasks...')

        # ─── CRM tasks — ALL open tasks BLOCKED ────────────────────────────────
        crm_t1 = create_task_service(
            project=crm, title='Implement OAuth2 Integration',
            description='Integrate Auth0 for SSO across CRM modules.',
            priority='critical', estimated_effort_hours=Decimal('48'),
            deadline=_d(-1), assignee=david)
        update_task_status_service(crm_t1, 'blocked', david,
            blocked_reason='Auth0 sandbox credentials not provided by client.')

        crm_t2 = create_task_service(
            project=crm, title='Customer Data Schema Migration',
            description='PostgreSQL schema migration for 2M legacy records.',
            priority='critical', estimated_effort_hours=Decimal('54'),
            deadline=_d(-2), assignee=david)
        update_task_status_service(crm_t2, 'blocked', david,
            blocked_reason='Data governance team approval pending — blocked 48h+.')

        crm_t3 = create_task_service(
            project=crm, title='Reporting Dashboard API',
            description='REST endpoints for executive report generation.',
            priority='high', estimated_effort_hours=Decimal('48'),
            deadline=_d(0), assignee=alice)
        update_task_status_service(crm_t3, 'blocked', alice,
            blocked_reason='Blocked by OAuth2 integration — auth layer not ready.')

        crm_t4 = create_task_service(
            project=crm, title='Frontend Data Binding — Customer Profiles',
            description='React components consuming CRM REST API.',
            priority='high', estimated_effort_hours=Decimal('48'),
            deadline=_d(1), assignee=marie)
        update_task_status_service(crm_t4, 'blocked', marie,
            blocked_reason='Waiting on backend API endpoints to be unblocked.')

        crm_t5 = create_task_service(
            project=crm, title='Real-time Notification System',
            description='WebSocket integration for live updates.',
            priority='medium', estimated_effort_hours=Decimal('40'),
            deadline=_d(2), assignee=marie)
        update_task_status_service(crm_t5, 'blocked', marie,
            blocked_reason='Infrastructure team has not provisioned WebSocket server.')

        crm_t6 = create_task_service(
            project=crm, title='Customer Portal UI Redesign',
            description='Modern UI overhaul for customer-facing portal.',
            priority='medium', estimated_effort_hours=Decimal('80'),
            deadline=_d(3), assignee=lucas)
        update_task_status_service(crm_t6, 'blocked', lucas,
            blocked_reason='Design team has not finalized mockups.')

        crm_t7 = create_task_service(
            project=crm, title='Audit Logging Implementation',
            description='Comprehensive audit trail for compliance.',
            priority='medium', estimated_effort_hours=Decimal('80'),
            deadline=_d(4), assignee=omar)
        update_task_status_service(crm_t7, 'blocked', omar,
            blocked_reason='Compliance team review pending.')

        crm_t8 = create_task_service(
            project=crm, title='Performance Optimization',
            description='Query optimization and caching layer.',
            priority='high', estimated_effort_hours=Decimal('40'),
            deadline=_d(5), assignee=alice)
        update_task_status_service(crm_t8, 'blocked', alice,
            blocked_reason='Waiting for production database access.')

        # Dependency chain: reporting depends on OAuth2
        add_task_dependency_service(crm_t3, crm_t1)

        # Completed task for historical richness
        crm_done = create_task_service(
            project=crm, title='Initial Project Setup',
            description='Monorepo, CI pipeline, linting.',
            priority='medium', estimated_effort_hours=Decimal('8'),
            deadline=_d(-50), assignee=jean)
        update_task_status_service(crm_done, 'done', jean)

        # ─── API Gateway tasks ─────────────────────────────────────────────────
        # david: 40+20=60h → 75% balanced (on top of 80% from CRM → per-project snapshots)
        api_t1 = create_task_service(
            project=api_gw, title='Rate Limiting Strategy Design',
            description='Define per-endpoint throttle rules and burst limits.',
            priority='high', estimated_effort_hours=Decimal('40'),
            deadline=_d(3), assignee=david)

        api_t2 = create_task_service(
            project=api_gw, title='JWT Validation Middleware',
            description='Middleware chain for token validation across all routes.',
            priority='critical', estimated_effort_hours=Decimal('20'),
            deadline=_d(4), assignee=david)
        update_task_status_service(api_t2, 'in_progress', david)

        api_t3 = create_task_service(
            project=api_gw, title='OpenAPI 3.0 Specification',
            description='Full endpoint documentation for partner developers.',
            priority='medium', estimated_effort_hours=Decimal('20'),
            deadline=_d(5), assignee=marie)
        update_task_status_service(api_t3, 'blocked', marie,
            blocked_reason='Waiting on final endpoint list from product owner.')

        api_t4 = create_task_service(
            project=api_gw, title='Load Testing and Benchmarking',
            description='k6 load tests to validate 99th-percentile latency SLAs.',
            priority='medium', estimated_effort_hours=Decimal('8'),
            deadline=_d(5), assignee=omar)
        update_task_status_service(api_t4, 'in_progress', omar)

        api_t5 = create_task_service(
            project=api_gw, title='Staging Environment Deployment',
            description='Deploy gateway to staging with feature flags.',
            priority='high', estimated_effort_hours=Decimal('8'),
            deadline=_d(6), assignee=jean)

        # Dependency: load testing depends on JWT middleware
        add_task_dependency_service(api_t4, api_t2)

        # ─── Mobile tasks ──────────────────────────────────────────────────────
        # sarah: 16h → 20% underloaded (good reassignment candidate)
        mob_t1 = create_task_service(
            project=mobile, title='User Research & Persona Validation',
            description='5 user interviews + affinity mapping.',
            priority='medium', estimated_effort_hours=Decimal('8'),
            deadline=_d(-3), assignee=priya)
        update_task_status_service(mob_t1, 'done', priya)

        mob_t2 = create_task_service(
            project=mobile, title='High-Fidelity Wireframes',
            description='Figma wireframes for all 12 core screens.',
            priority='high', estimated_effort_hours=Decimal('16'),
            deadline=_d(4), assignee=sarah)
        update_task_status_service(mob_t2, 'in_progress', sarah)

        mob_t3 = create_task_service(
            project=mobile, title='React Native Component Library',
            description='Shared design system components with Storybook.',
            priority='medium', estimated_effort_hours=Decimal('12'),
            deadline=_d(6), assignee=priya)

        mob_t4 = create_task_service(
            project=mobile, title='Onboarding Flow Implementation',
            description='Registration and profile setup screens.',
            priority='medium', estimated_effort_hours=Decimal('10'),
            deadline=_d(7), assignee=sarah)
        add_task_dependency_service(mob_t4, mob_t2)

        # ─── Infrastructure tasks ──────────────────────────────────────────────
        inf_t1 = create_task_service(
            project=infra, title='Dockerise Backend Services',
            description='Multi-stage Dockerfiles for Django and workers.',
            priority='high', estimated_effort_hours=Decimal('8'),
            deadline=_d(5), assignee=jean)
        update_task_status_service(inf_t1, 'in_progress', jean)

        inf_t2 = create_task_service(
            project=infra, title='GitHub Actions CI Pipeline',
            description='Lint, test, build and push to ECR on every PR.',
            priority='medium', estimated_effort_hours=Decimal('6'),
            deadline=_d(6), assignee=omar)

        inf_t3 = create_task_service(
            project=infra, title='Staging Environment Provisioning',
            description='Terraform + AWS ECS Fargate staging cluster.',
            priority='medium', estimated_effort_hours=Decimal('12'),
            deadline=_d(14), assignee=jean)
        add_task_dependency_service(inf_t3, inf_t1)

        # ── 6. Workload Snapshots ──────────────────────────────────────────────
        # Use the 2-week current sprint window for all snapshots.
        # Task deadlines above fall in [_d(-7), _d(7)] so they are counted.
        self.stdout.write('  Calculating workload snapshots...')
        snapshot_map = [
            ([alice, david, marie, lucas, omar], crm),  # alice added for full team coverage
            ([david, marie, omar, jean],  api_gw),
            ([sarah, priya],              mobile),
            ([jean, omar],                infra),
        ]
        for members, project in snapshot_map:
            for u in members:
                snap = create_workload_snapshot_service(
                    u, project, SPRINT_START, SPRINT_END)
                self.stdout.write(
                    f'    {u.username:<24} | {project.name:<32} | '
                    f'{snap.workload_percentage:>6.1f}% ({snap.status})')

        # ── 7. Risk Scores ─────────────────────────────────────────────────────
        # All workload snapshots are REAL calculations from calculate_workload_service().
        # CRM target metrics with current task distribution:
        #   overload_factor: david=127.5% critically_overloaded → contributes to high overload factor
        #   blocked_factor = 100% (all 7 open tasks blocked)
        #   deadline_proximity = 100% (past deadline by 3 days)
        # Risk formula: 0.35×overload + 0.30×blocked + 0.20×deadline + 0.15×velocity
        # With david critically_overloaded + all tasks blocked + past deadline → CRITICAL (≥80%)
        self.stdout.write('  Calculating risk scores...')
        for project in [crm, api_gw, mobile, infra]:
            rs = calculate_risk_score_service(project)
            fn = self.style.SUCCESS if rs.level in ('critical','high') else self.style.WARNING
            self.stdout.write(fn(
                f'    {project.name:<34} {rs.score:.1f}% ({rs.level.upper()})'))

        # ── 8. AI Recommendations ──────────────────────────────────────────────
        self.stdout.write('  Generating AI recommendations...')
        recos_crm = generate_recommendations_for_project_service(crm)
        self.stdout.write(f'    CRM: {len(recos_crm)} recommendation(s) generated')
        recos_api = generate_recommendations_for_project_service(api_gw)
        self.stdout.write(f'    API GW: {len(recos_api)} recommendation(s) generated')

        # ── 9. Notifications ───────────────────────────────────────────────────
        self.stdout.write('  Creating demo notifications...')
        create_notification_service(
            user=alice, notification_type='task_blocked',
            title='Task Blocked >24h',
            message=(f"'{crm_t2.title}' has been blocked for over 24 hours. "
                     "Reason: Data governance team approval pending."),
            project=crm, task=crm_t2)
        create_notification_service(
            user=bob, notification_type='recommendation',
            title='New Recommendation Generated',
            message=f"AI recommendation available for project '{mobile.name}'.",
            project=mobile, task=None)
        create_notification_service(
            user=alice, notification_type='overload_alert',
            title='Workload Overload Alert',
            message=(f"demo_david.chen is critically overloaded on '{crm.name}'. "
                     "Consider redistributing tasks immediately."),
            project=crm, task=None)
        for exec_user in [grace, henry]:
            create_notification_service(
                user=exec_user, notification_type='risk_alert',
                title='Project Risk: Critical',
                message=(f"'{crm.name}' has reached Critical risk level. "
                         "Immediate attention required."),
                project=crm, task=None)

        # ── 10. Sample Chat Conversation ───────────────────────────────────────
        self.stdout.write('  Seeding sample chat conversation...')
        conv = Conversation.objects.create(
            user=alice, project=crm, title='Who is overloaded on CRM?')
        for role, content, gen_by in [
            ('user',
             'Who is overloaded on the CRM Platform Rewrite project?',
             ''),
            ('assistant',
             'The entire CRM team is overloaded. david.chen is critically overloaded at 127.5% capacity with 102h of '
             'blocked tasks (OAuth2 integration 48h + schema migration 54h). alice.pm and marie.t are both at 110% '
             '(88h each), lucas.silva and omar.diallo are at 100% (80h each). All eight open tasks are currently '
             'blocked, and the project deadline passed 3 days ago. This is a critical situation requiring immediate '
             'intervention.',
             'fallback_template'),
            ('user',
             'What is driving the critical risk score?',
             ''),
            ('assistant',
             'The CRM Platform Rewrite is at CRITICAL risk level. '
             'Four factors combine to create this crisis: '
             '(1) Overload Factor 100% — every single team member (5/5) is overloaded or critically overloaded. '
             '(2) Blocked Task Factor 100% — all 8 open tasks are currently blocked by external dependencies. '
             '(3) Deadline Proximity Factor 100% — the project deadline passed 3 days ago with significant work remaining. '
             '(4) The weighted formula (35% overload + 30% blocked + 20% deadline + 15% velocity) produces approximately 85% risk. '
             'This combination demands immediate escalation and resource reallocation.',
             'fallback_template'),
        ]:
            ChatMessage.objects.create(
                conversation=conv, user=alice, project=crm,
                role=role, content=content, generated_by=gen_by)

        # ── 11. Print credentials ──────────────────────────────────────────────
        self._print_credentials(alice, bob, admin, grace, henry, david, marie, sarah)

    # ------------------------------------------------------------------ print

    def _print_credentials(self, alice, bob, admin, grace, henry, david, marie, sarah):
        sep = '-' * 72
        self.stdout.write(f'\n{sep}')
        self.stdout.write(self.style.SUCCESS('  DEMO CREDENTIALS  (password for all: Demo1234!)'))
        self.stdout.write(sep)
        rows = [
            ('Project Manager',   alice.username,  'CRM (critical) + API GW projects'),
            ('Project Manager',   bob.username,    'Mobile App Redesign project'),
            ('Administrator',     admin.username,  'Full system access'),
            ('Executive Manager', grace.username,  'Portfolio view — sees critical risk alerts'),
            ('Executive Manager', henry.username,  'Portfolio view'),
            ('Team Member',       david.username,  'Critically overloaded at 127.5% — red workload bar'),
            ('Team Member',       marie.username,  'Overloaded at 110% — blocked tasks on CRM'),
            ('Team Member',       sarah.username,  'Underloaded at 32.5% — prime reassignment candidate'),
        ]
        for role, uname, note in rows:
            self.stdout.write(f'  {role:<20} {uname:<26} {note}')
        self.stdout.write(sep)
        self.stdout.write(f'  Password (all accounts): Demo1234!')
        self.stdout.write(sep)
        self.stdout.write(self.style.SUCCESS(
            '\nSeed complete.\n'
            'Run `python manage.py seed_demo --reset` to wipe and reseed before the demo.\n'))
