"""
Tests for the dashboard summary endpoint (Sprint 9).
See docs/14_REST_API.md §11 and .ai/business-rules.md BR-7.1.
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.analytics.models import WorkloadSnapshot, RiskScore
from apps.recommendations.models import Recommendation
from apps.notifications.models import Notification


def make_user(username, role='pm'):
    return User.objects.create_user(
        username=username, email=f'{username}@dash.test',
        password='testpass', role=role,
    )


def make_project(owner, team=None, name='Test Project'):
    if team is None:
        team = Team.objects.create(name=f'Team {name}')
    today = timezone.now().date()
    return Project.objects.create(
        name=name, description='', start_date=today,
        end_date=today + timedelta(days=30),
        status='active', owner=owner, team=team,
    )


def make_task(project, assignee, status='todo'):
    return Task.objects.create(
        project=project, assignee=assignee, title='Task',
        description='', priority='medium', status=status,
        estimated_effort_hours=Decimal('8.00'),
        deadline=timezone.now().date() + timedelta(days=7),
    )


class DashboardSummaryPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_returns_200(self):
        user = make_user('auth_user')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/dashboard/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardPMPayloadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('dash_pm', role='pm')
        self.team = Team.objects.create(name='Dash Team')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team, 'PM Project')

    def _get(self):
        self.client.force_authenticate(user=self.pm)
        return self.client.get('/api/dashboard/summary/')

    def test_role_field_is_pm(self):
        response = self._get()
        self.assertEqual(response.data['role'], 'pm')

    def test_contains_required_fields(self):
        response = self._get()
        for field in ('projects_summary', 'my_workload', 'pending_recommendations_count',
                      'top_recommendations', 'unread_notifications_count', 'recent_notifications'):
            self.assertIn(field, response.data, f'Missing field: {field}')

    def test_projects_summary_contains_own_project(self):
        response = self._get()
        ids = [p['id'] for p in response.data['projects_summary']]
        self.assertIn(str(self.project.id), ids)

    def test_scope_isolation_pm_does_not_see_other_pm_project(self):
        other_pm = make_user('other_dash_pm', role='pm')
        other_team = Team.objects.create(name='Other Dash Team')
        other_project = make_project(other_pm, other_team, 'Other Project')
        response = self._get()
        ids = [p['id'] for p in response.data['projects_summary']]
        self.assertNotIn(str(other_project.id), ids)

    def test_pending_recs_count_reflects_reality(self):
        Recommendation.objects.create(
            project=self.project, task=None,
            current_assignee=None, suggested_assignee=self.pm,
            recommendation_type='overloaded_member',
            title='Test Reco', description='', explanation='',
            confidence_score=80, priority='medium', status='pending',
        )
        response = self._get()
        self.assertEqual(response.data['pending_recommendations_count'], 1)

    def test_unread_count_only_for_requesting_user(self):
        Notification.objects.create(
            user=self.pm, notification_type='risk_alert',
            title='Alert', message='Test', project=self.project,
        )
        other = make_user('notif_other_pm', role='pm')
        Notification.objects.create(
            user=other, notification_type='risk_alert',
            title='Other', message='Other',
        )
        response = self._get()
        self.assertEqual(response.data['unread_notifications_count'], 1)

    def test_projects_sorted_by_risk_descending(self):
        # Create a second project and give it a high risk score
        project2 = make_project(self.pm, self.team, 'High Risk Project')
        RiskScore.objects.create(
            project=project2, score=85, level='critical',
            overload_factor=50, blocked_task_factor=50,
            deadline_proximity_factor=50, historical_velocity_factor=1,
        )
        response = self._get()
        summaries = response.data['projects_summary']
        if len(summaries) >= 2:
            scores = [
                float(s['risk']['score']) if s['risk'] else 0
                for s in summaries
            ]
            self.assertEqual(scores, sorted(scores, reverse=True))


class DashboardMemberPayloadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.member = make_user('dash_member', role='member')
        self.pm = make_user('dash_mem_pm', role='pm')
        self.team = Team.objects.create(name='Member Team')
        TeamMembership.objects.create(team=self.team, user=self.member)
        self.project = make_project(self.pm, self.team)

    def _get(self):
        self.client.force_authenticate(user=self.member)
        return self.client.get('/api/dashboard/summary/')

    def test_role_field_is_member(self):
        response = self._get()
        self.assertEqual(response.data['role'], 'member')

    def test_contains_required_fields(self):
        response = self._get()
        for field in ('my_workload', 'my_tasks_by_status', 'my_upcoming_tasks',
                      'unread_notifications_count'):
            self.assertIn(field, response.data)

    def test_my_upcoming_tasks_only_for_member(self):
        make_task(self.project, self.member, status='in_progress')
        make_task(self.project, self.pm, status='todo')  # other user's task
        response = self._get()
        task_ids_projects = [t['project_name'] for t in response.data['my_upcoming_tasks']]
        # Should have 1 task (member's), not 2
        self.assertEqual(len(response.data['my_upcoming_tasks']), 1)

    def test_done_tasks_excluded_from_summary(self):
        make_task(self.project, self.member, status='done')
        make_task(self.project, self.member, status='todo')
        response = self._get()
        # Only the non-done task appears
        self.assertEqual(len(response.data['my_upcoming_tasks']), 1)
        self.assertEqual(response.data['my_tasks_by_status']['todo'], 1)


class DashboardExecutivePayloadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.exec_user = make_user('dash_exec', role='executive')
        self.pm = make_user('dash_exec_pm', role='pm')
        self.team = Team.objects.create(name='Exec Team')
        self.project = make_project(self.pm, self.team)

    def _get(self):
        self.client.force_authenticate(user=self.exec_user)
        return self.client.get('/api/dashboard/summary/')

    def test_role_field_is_executive(self):
        response = self._get()
        self.assertEqual(response.data['role'], 'executive')

    def test_contains_portfolio(self):
        response = self._get()
        self.assertIn('portfolio', response.data)

    def test_executive_sees_all_projects(self):
        """BR-7.1: executive has cross-project read-only access."""
        response = self._get()
        ids = [p['id'] for p in response.data['portfolio']]
        self.assertIn(str(self.project.id), ids)

    def test_portfolio_sorted_by_risk_descending(self):
        project2 = make_project(self.pm, self.team, 'Critical Project')
        RiskScore.objects.create(
            project=project2, score=90, level='critical',
            overload_factor=50, blocked_task_factor=50,
            deadline_proximity_factor=50, historical_velocity_factor=1,
        )
        response = self._get()
        portfolio = response.data['portfolio']
        if len(portfolio) >= 2:
            scores = [float(p['risk']['score']) if p['risk'] else 0 for p in portfolio]
            self.assertEqual(scores, sorted(scores, reverse=True))
