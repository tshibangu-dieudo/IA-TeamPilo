"""
Tests for tasks app.
See .ai/coding-rules.md §7: every BR formula gets at least one unit test,
including boundary values.
See docs/16_Testing.md: unit tests for service functions first.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership
from apps.projects.models import Project
from .models import Task, TaskDependency, TaskStatusHistory
from .services import (
    create_task_service,
    update_task_status_service,
    add_task_dependency_service,
    remove_task_dependency_service,
    auto_escalate_priority_service,
    get_task_status_history_service,
    _has_circular_dependency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username, role='pm'):
    return User.objects.create_user(
        username=username,
        email=f'{username}@test.io',
        password='testpassword',
        role=role,
    )


def make_team(name='Test Team'):
    return Team.objects.create(name=name)


def make_project(owner, team, name='Test Project'):
    return Project.objects.create(
        name=name,
        description='',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status='active',
        owner=owner,
        team=team,
    )


def make_task(project, assignee=None, status='todo', priority='medium',
              deadline_offset_days=10):
    return Task.objects.create(
        project=project,
        assignee=assignee,
        title='Test Task',
        description='',
        priority=priority,
        status=status,
        estimated_effort_hours=Decimal('8.00'),
        deadline=date.today() + timedelta(days=deadline_offset_days),
    )


# ---------------------------------------------------------------------------
# Unit tests — services
# ---------------------------------------------------------------------------

class CreateTaskServiceTest(TestCase):
    def setUp(self):
        self.pm = make_user('pm_user')
        self.member = make_user('member_user', role='member')
        self.team = make_team()
        TeamMembership.objects.create(team=self.team, user=self.pm)
        TeamMembership.objects.create(team=self.team, user=self.member)
        self.project = make_project(self.pm, self.team)

    def test_creates_task_with_initial_history(self):
        task = create_task_service(
            project=self.project,
            title='New Task',
            description='desc',
            priority='high',
            estimated_effort_hours=Decimal('4.00'),
            deadline=date.today() + timedelta(days=5),
        )
        self.assertEqual(task.status, 'todo')
        history = TaskStatusHistory.objects.filter(task=task)
        self.assertEqual(history.count(), 1)
        self.assertIsNone(history.first().previous_status)
        self.assertEqual(history.first().new_status, 'todo')

    def test_unassigned_since_set_when_no_assignee(self):
        task = create_task_service(
            project=self.project,
            title='Unassigned',
            description='',
            priority='low',
            estimated_effort_hours=Decimal('2.00'),
            deadline=date.today() + timedelta(days=5),
        )
        self.assertIsNotNone(task.unassigned_since)

    def test_unassigned_since_none_when_assignee_given(self):
        task = create_task_service(
            project=self.project,
            title='Assigned',
            description='',
            priority='low',
            estimated_effort_hours=Decimal('2.00'),
            deadline=date.today() + timedelta(days=5),
            assignee=self.member,
        )
        self.assertIsNone(task.unassigned_since)


class UpdateTaskStatusServiceTest(TestCase):
    """
    Tests for status transitions, BR-3.1.
    """

    def setUp(self):
        self.pm = make_user('pm2')
        self.team = make_team('Team B')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)
        self.task = make_task(self.project, assignee=self.pm)

    def test_status_transition_recorded_in_history(self):
        update_task_status_service(self.task, 'in_progress', self.pm)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')
        history = TaskStatusHistory.objects.filter(task=self.task).order_by('-changed_at')
        latest = history.first()
        self.assertEqual(latest.previous_status, 'todo')
        self.assertEqual(latest.new_status, 'in_progress')

    def test_blocked_requires_reason_br3_1(self):
        """BR-3.1: blocked_reason is mandatory when transitioning to 'blocked'."""
        with self.assertRaises(ValueError):
            update_task_status_service(self.task, 'blocked', self.pm, blocked_reason='')

    def test_blocked_sets_blocked_at(self):
        update_task_status_service(self.task, 'blocked', self.pm, blocked_reason='Waiting for API key')
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.blocked_at)

    def test_unblocking_clears_blocked_at(self):
        update_task_status_service(self.task, 'blocked', self.pm, blocked_reason='reason')
        update_task_status_service(self.task, 'in_progress', self.pm)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.blocked_at)
        self.assertEqual(self.task.blocked_reason, '')


class TaskDependencyServiceTest(TestCase):
    """
    Tests for dependency management, BR-8.1.
    """

    def setUp(self):
        self.pm = make_user('pm3')
        self.team = make_team('Team C')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)
        self.task_a = make_task(self.project)
        self.task_b = make_task(self.project)
        self.task_c = make_task(self.project)

    def test_add_dependency(self):
        dep = add_task_dependency_service(self.task_b, self.task_a)
        self.assertEqual(dep.task, self.task_b)
        self.assertEqual(dep.depends_on_task, self.task_a)

    def test_self_dependency_rejected_br8_1(self):
        with self.assertRaises(ValueError):
            add_task_dependency_service(self.task_a, self.task_a)

    def test_circular_dependency_rejected_br8_1(self):
        """A → B, B → C, C → A should be rejected."""
        add_task_dependency_service(self.task_b, self.task_a)  # B depends on A
        add_task_dependency_service(self.task_c, self.task_b)  # C depends on B
        with self.assertRaises(ValueError):
            add_task_dependency_service(self.task_a, self.task_c)  # A depends on C → cycle

    def test_remove_dependency(self):
        add_task_dependency_service(self.task_b, self.task_a)
        remove_task_dependency_service(self.task_b, self.task_a)
        self.assertFalse(
            TaskDependency.objects.filter(task=self.task_b, depends_on_task=self.task_a).exists()
        )

    def test_waiting_on_dependency_status_set_br3_3(self):
        """BR-3.3: task is flagged 'waiting_on_dependency' when prerequisite is not Done."""
        add_task_dependency_service(self.task_b, self.task_a)
        self.task_b.refresh_from_db()
        self.assertEqual(self.task_b.status, 'waiting_on_dependency')

    def test_waiting_on_dependency_cleared_when_dep_done(self):
        add_task_dependency_service(self.task_b, self.task_a)
        # Mark prerequisite done
        self.task_a.status = 'done'
        self.task_a.save()
        # Remove and re-add to trigger refresh
        remove_task_dependency_service(self.task_b, self.task_a)
        add_task_dependency_service(self.task_b, self.task_a)
        self.task_b.refresh_from_db()
        # All deps are done, so status should revert
        self.assertEqual(self.task_b.status, 'todo')


class AutoEscalatePriorityServiceTest(TestCase):
    """
    Tests for priority auto-escalation, BR-2.2.
    """

    def setUp(self):
        self.pm = make_user('pm4')
        self.team = make_team('Team D')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)

    def test_escalates_when_within_48h(self):
        """BR-2.2: deadline within 48h → escalate by one level."""
        task = make_task(self.project, priority='medium', deadline_offset_days=1)
        task = auto_escalate_priority_service(task)
        self.assertEqual(task.priority, 'high')

    def test_does_not_escalate_beyond_critical(self):
        """BR-2.2: critical is the cap."""
        task = make_task(self.project, priority='critical', deadline_offset_days=1)
        task = auto_escalate_priority_service(task)
        self.assertEqual(task.priority, 'critical')

    def test_no_escalation_when_deadline_far(self):
        """No escalation when deadline is more than 48h away."""
        task = make_task(self.project, priority='low', deadline_offset_days=10)
        task = auto_escalate_priority_service(task)
        self.assertEqual(task.priority, 'low')

    def test_no_escalation_when_done_br2_2(self):
        """BR-2.2: done tasks are not escalated."""
        task = make_task(self.project, status='done', priority='medium', deadline_offset_days=1)
        task = auto_escalate_priority_service(task)
        self.assertEqual(task.priority, 'medium')

    def test_boundary_exactly_48h(self):
        """Boundary: exactly 48h (2 days) should trigger escalation."""
        task = make_task(self.project, priority='low', deadline_offset_days=2)
        task = auto_escalate_priority_service(task)
        self.assertEqual(task.priority, 'medium')


# ---------------------------------------------------------------------------
# Integration tests — API endpoints
# ---------------------------------------------------------------------------

class TaskAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('api_pm')
        self.member = make_user('api_member', role='member')
        self.other_pm = make_user('other_pm')
        self.team = make_team('API Team')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        TeamMembership.objects.create(team=self.team, user=self.member)
        self.project = make_project(self.pm, self.team)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_tasks_for_project(self):
        make_task(self.project)
        make_task(self.project)
        self._auth(self.pm)
        url = f'/api/projects/{self.project.id}/tasks/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_task_as_pm(self):
        self._auth(self.pm)
        url = f'/api/projects/{self.project.id}/tasks/'
        data = {
            'title': 'API Task',
            'description': 'Test',
            'priority': 'high',
            'estimated_effort_hours': '8.00',
            'deadline': str(date.today() + timedelta(days=10)),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Task')

    def test_create_task_as_member_forbidden(self):
        """Team members cannot create tasks — PM only."""
        self._auth(self.member)
        url = f'/api/projects/{self.project.id}/tasks/'
        data = {
            'title': 'Member Task',
            'priority': 'low',
            'estimated_effort_hours': '4.00',
            'deadline': str(date.today() + timedelta(days=10)),
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_detail_accessible_to_member(self):
        task = make_task(self.project, assignee=self.member)
        self._auth(self.member)
        response = self.client.get(f'/api/tasks/{task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_status_update_by_assignee(self):
        task = make_task(self.project, assignee=self.member)
        self._auth(self.member)
        response = self.client.patch(
            f'/api/tasks/{task.id}/status/',
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_blocked_status_requires_reason_api(self):
        task = make_task(self.project, assignee=self.member)
        self._auth(self.member)
        response = self.client.patch(
            f'/api/tasks/{task.id}/status/',
            {'status': 'blocked', 'blocked_reason': ''},
            format='json',
        )
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ])

    def test_status_update_by_non_assignee_forbidden(self):
        task = make_task(self.project, assignee=self.pm)
        self._auth(self.member)
        response = self.client.patch(
            f'/api/tasks/{task.id}/status/',
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_dependency_as_pm(self):
        task_a = make_task(self.project)
        task_b = make_task(self.project)
        self._auth(self.pm)
        response = self.client.post(
            f'/api/tasks/{task_b.id}/dependencies/',
            {'depends_on_task_id': str(task_a.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_circular_dependency_returns_422(self):
        task_a = make_task(self.project)
        task_b = make_task(self.project)
        add_task_dependency_service(task_b, task_a)
        self._auth(self.pm)
        response = self.client.post(
            f'/api/tasks/{task_a.id}/dependencies/',
            {'depends_on_task_id': str(task_b.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_task_history(self):
        task = make_task(self.project, assignee=self.pm)
        update_task_status_service(task, 'in_progress', self.pm)
        self._auth(self.pm)
        response = self.client.get(f'/api/tasks/{task.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The endpoint uses DRF pagination — unwrap 'results' if present
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_my_tasks(self):
        make_task(self.project, assignee=self.member)
        self._auth(self.member)
        response = self.client.get('/api/tasks/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The endpoint uses DRF pagination — unwrap 'results' if present
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_unauthenticated_request_rejected(self):
        response = self.client.get('/api/tasks/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_out_of_scope_project_returns_404(self):
        """BR-7.1: scope violations return 404, not 403."""
        outsider = make_user('outsider', role='pm')
        other_team = make_team('Other Team')
        other_project = make_project(outsider, other_team, name='Other Project')
        task = make_task(other_project)
        self._auth(self.pm)
        response = self.client.get(f'/api/projects/{other_project.id}/tasks/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
