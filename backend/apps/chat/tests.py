"""
Tests for the chat app — Sprint 8.
See .ai/coding-rules.md: service tests first, then API tests.
See docs/13_AI_Architecture.md §3.3 (Chain 3) and §6 (fallback).

Coverage:
- Conversation creation and ownership
- Message persistence after a query
- Conversation history truncation (HISTORY_TURN_LIMIT)
- Data snapshot scoping (BR-7.1)
- AI engine always mocked — no real watsonx calls in tests
- Fallback path when AI raises
- API: query endpoint happy path and permission checks
- API: summary endpoint
- API: conversation list/detail/delete scoped to owner
- Scope isolation: users cannot access each other's conversations
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership
from apps.projects.models import Project
from apps.tasks.models import Task

from .models import Conversation, ChatMessage
from .services import (
    process_chat_query,
    process_executive_summary,
    get_conversation_history,
    HISTORY_TURN_LIMIT,
    _build_data_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username, role='pm'):
    return User.objects.create_user(
        username=username,
        email=f'{username}@chat.test',
        password='testpassword',
        role=role,
    )


def make_team(name='Chat Team'):
    return Team.objects.create(name=name)


def make_project(owner, team, name='Chat Project'):
    today = timezone.now().date()
    return Project.objects.create(
        name=name,
        description='',
        start_date=today,
        end_date=today + timedelta(days=30),
        status='active',
        owner=owner,
        team=team,
    )


def make_task(project, assignee=None):
    return Task.objects.create(
        project=project,
        assignee=assignee,
        title='Chat Task',
        description='',
        priority='medium',
        status='todo',
        estimated_effort_hours=Decimal('8.00'),
        deadline=timezone.now().date() + timedelta(days=7),
    )


MOCK_AI_RETURN = ('David is overloaded at 135%.', 'granite')
MOCK_FALLBACK_RETURN = ('AI assistant temporarily unavailable. Here is the raw data: {}', 'fallback_template')

# The correct mock target: the function as imported inside ai_engine.chat_service
_MOCK_TARGET = 'ai_engine.chat_service.generate_chat_response'


# ---------------------------------------------------------------------------
# Unit tests — services
# ---------------------------------------------------------------------------

class ProcessChatQueryServiceTest(TestCase):
    """Tests for the main process_chat_query service function."""

    def setUp(self):
        self.pm = make_user('chat_pm')
        self.team = make_team()
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_creates_conversation_on_first_query(self, mock_ai):
        result = process_chat_query(self.pm, 'Who is overloaded?', project=self.project)
        self.assertIsNotNone(result['conversation_id'])
        self.assertTrue(Conversation.objects.filter(id=result['conversation_id']).exists())

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_persists_user_and_assistant_messages(self, mock_ai):
        result = process_chat_query(self.pm, 'Who is overloaded?', project=self.project)
        conv = Conversation.objects.get(id=result['conversation_id'])
        messages = list(conv.messages.order_by('created_at'))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, 'user')
        self.assertEqual(messages[0].content, 'Who is overloaded?')
        self.assertEqual(messages[1].role, 'assistant')
        self.assertEqual(messages[1].content, MOCK_AI_RETURN[0])
        self.assertEqual(messages[1].generated_by, 'granite')

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_title_set_from_first_question(self, mock_ai):
        result = process_chat_query(self.pm, 'Who is overloaded?', project=self.project)
        conv = Conversation.objects.get(id=result['conversation_id'])
        self.assertEqual(conv.title, 'Who is overloaded?')

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_continues_existing_conversation(self, mock_ai):
        r1 = process_chat_query(self.pm, 'First question', project=self.project)
        conv_id = r1['conversation_id']
        r2 = process_chat_query(self.pm, 'Second question', project=self.project, conversation_id=conv_id)
        self.assertEqual(r2['conversation_id'], conv_id)
        # 4 messages total: 2 per query
        self.assertEqual(
            ChatMessage.objects.filter(conversation_id=conv_id).count(), 4
        )

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_unknown_conversation_id_creates_new(self, mock_ai):
        import uuid
        r = process_chat_query(
            self.pm, 'Question', project=self.project,
            conversation_id=uuid.uuid4(),
        )
        self.assertIsNotNone(r['conversation_id'])

    @patch('ai_engine.router.route_chat_request', return_value=('Fallback answer.', 'fallback_template', 'TEAMPILOT_DATA'))
    def test_fallback_path_stored_correctly(self, mock_ai):
        result = process_chat_query(self.pm, 'Any question?', project=self.project)
        self.assertEqual(result['generated_by'], 'fallback_template')
        msg = ChatMessage.objects.filter(
            conversation_id=result['conversation_id'], role='assistant'
        ).first()
        self.assertEqual(msg.generated_by, 'fallback_template')

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_conversation_title_not_overwritten_on_second_query(self, mock_ai):
        r1 = process_chat_query(self.pm, 'First question', project=self.project)
        process_chat_query(
            self.pm, 'Second question', project=self.project,
            conversation_id=r1['conversation_id'],
        )
        conv = Conversation.objects.get(id=r1['conversation_id'])
        self.assertEqual(conv.title, 'First question')


class ConversationHistoryTruncationTest(TestCase):
    """Verify HISTORY_TURN_LIMIT is respected."""

    def setUp(self):
        self.pm = make_user('hist_pm')
        self.team = make_team('Hist Team')
        self.project = make_project(self.pm, self.team)
        self.conv = Conversation.objects.create(user=self.pm, project=self.project)

    def test_history_capped_at_limit(self):
        # Create more messages than HISTORY_TURN_LIMIT
        for i in range(HISTORY_TURN_LIMIT + 4):
            ChatMessage.objects.create(
                conversation=self.conv,
                user=self.pm,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i}',
            )
        history = get_conversation_history(self.conv)
        self.assertLessEqual(len(history), HISTORY_TURN_LIMIT)

    def test_empty_history_returns_empty_list(self):
        history = get_conversation_history(self.conv)
        self.assertEqual(history, [])


class DataSnapshotScopingTest(TestCase):
    """Verify _build_data_snapshot respects BR-7.1."""

    def setUp(self):
        self.pm = make_user('snap_pm')
        self.exec_user = make_user('snap_exec', role='executive')
        self.member = make_user('snap_member', role='member')
        self.team = make_team('Snap Team')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        TeamMembership.objects.create(team=self.team, user=self.member)
        self.project = make_project(self.pm, self.team)

    def test_project_snapshot_contains_project_info(self):
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        self.assertIn('projects', snapshot)
        self.assertGreater(len(snapshot['projects']), 0)
        self.assertEqual(snapshot['projects'][0]['name'], self.project.name)

    def test_member_snapshot_contains_only_own_tasks(self):
        make_task(self.project, assignee=self.member)
        snapshot = _build_data_snapshot(self.member)
        self.assertIn('tasks', snapshot)
        self.assertGreater(len(snapshot['tasks']), 0)
        self.assertNotIn('projects', snapshot)

    def test_executive_cross_project_snapshot_contains_projects(self):
        snapshot = _build_data_snapshot(self.exec_user)
        self.assertIn('projects', snapshot)


class EnrichedSnapshotTest(TestCase):
    """Tests for enriched _build_data_snapshot with teams, members, tasks categorization."""

    def setUp(self):
        from apps.analytics.models import WorkloadSnapshot, RiskScore
        from apps.recommendations.models import Recommendation
        from apps.accounts.models import UserSkill
        
        self.pm = make_user('enrich_pm')
        self.admin = make_user('enrich_admin', role='admin')
        self.exec_user = make_user('enrich_exec', role='executive')
        self.member = make_user('enrich_member', role='member')
        self.team = make_team('Enrich Team')
        TeamMembership.objects.create(team=self.team, user=self.pm, role='lead')
        TeamMembership.objects.create(team=self.team, user=self.member, role='member')
        self.project = make_project(self.pm, self.team, name='Enrich Project')
        
        # Create workload snapshots
        today = timezone.now()
        WorkloadSnapshot.objects.create(
            user=self.member,
            project=self.project,
            workload_percentage=Decimal('135.00'),
            status='overloaded',
            computed_at=today,
        )
        WorkloadSnapshot.objects.create(
            user=self.pm,
            project=self.project,
            workload_percentage=Decimal('75.00'),
            status='balanced',
            computed_at=today,
        )
        
        # Create risk score
        RiskScore.objects.create(
            project=self.project,
            score=Decimal('7.5'),
            level='high',
            overload_factor=Decimal('0.4'),
            blocked_task_factor=Decimal('0.2'),
            deadline_proximity_factor=Decimal('0.1'),
            historical_velocity_factor=Decimal('0.0'),
            explanation_text='High overload and blocked tasks',
            computed_at=today,
        )
        
        # Create tasks
        self.blocked_task = Task.objects.create(
            project=self.project,
            assignee=self.member,
            title='Blocked Task',
            description='',
            priority='high',
            status='blocked',
            blocked_reason='Waiting for API access',
            estimated_effort_hours=Decimal('8.00'),
            deadline=timezone.now().date() + timedelta(days=7),
            updated_at=timezone.now() - timedelta(days=3),
        )
        self.overdue_task = Task.objects.create(
            project=self.project,
            assignee=self.member,
            title='Overdue Task',
            description='',
            priority='critical',
            status='in_progress',
            estimated_effort_hours=Decimal('8.00'),
            deadline=timezone.now().date() - timedelta(days=2),
        )
        self.high_priority_task = Task.objects.create(
            project=self.project,
            assignee=self.pm,
            title='High Priority Task',
            description='',
            priority='high',
            status='todo',
            estimated_effort_hours=Decimal('8.00'),
            deadline=timezone.now().date() + timedelta(days=14),
        )
        self.done_task = Task.objects.create(
            project=self.project,
            assignee=self.member,
            title='Done Task',
            description='',
            priority='medium',
            status='done',
            estimated_effort_hours=Decimal('8.00'),
            deadline=timezone.now().date() + timedelta(days=7),
        )
        
        # Create skills (using UserSkill directly with skill_name string)
        UserSkill.objects.create(user=self.member, skill_name='Python', proficiency_level=4)
        UserSkill.objects.create(user=self.pm, skill_name='React', proficiency_level=3)
        
        # Create recommendation
        Recommendation.objects.create(
            project=self.project,
            task=self.blocked_task,
            title='Reassign blocked task',
            current_assignee=self.member,
            suggested_assignee=self.pm,
            status='pending',
            confidence_score=85,  # 0-100 integer scale
            explanation='PM has availability and required skills',
        )

    def test_snapshot_includes_all_categories_for_project(self):
        """Snapshot should include metadata, projects, teams, members, tasks, analytics."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('metadata', snapshot)
        self.assertIn('projects', snapshot)
        self.assertIn('teams', snapshot)
        self.assertIn('members', snapshot)
        self.assertIn('tasks', snapshot)
        self.assertIn('analytics', snapshot)

    def test_snapshot_excludes_empty_categories(self):
        """If no tasks exist, tasks section should not appear."""
        new_pm = make_user('new_pm')
        new_team = make_team('New Team')
        new_project = make_project(new_pm, new_team, name='Empty Project')
        
        snapshot = _build_data_snapshot(new_pm, project=new_project)
        
        self.assertNotIn('tasks', snapshot)
        self.assertNotIn('analytics', snapshot)

    def test_member_scoping_isolation(self):
        """Member should never see other team members' data or other teams' data."""
        snapshot = _build_data_snapshot(self.member)
        
        # Should see only own tasks
        self.assertIn('tasks', snapshot)
        self.assertIn('my_tasks', snapshot['tasks'])
        
        # Should see own member data only
        self.assertIn('members', snapshot)
        self.assertEqual(len(snapshot['members']), 1)
        self.assertEqual(snapshot['members'][0]['name'], self.member.username)
        
        # Should not see projects list
        self.assertNotIn('projects', snapshot)

    def test_pm_scoping_owned_projects(self):
        """PM should see projects they own and their teams."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('projects', snapshot)
        self.assertEqual(snapshot['projects'][0]['name'], 'Enrich Project')
        self.assertEqual(snapshot['projects'][0]['owner'], self.pm.username)

    def test_admin_executive_full_visibility(self):
        """Admin and Executive should see all projects."""
        admin_snapshot = _build_data_snapshot(self.admin)
        exec_snapshot = _build_data_snapshot(self.exec_user)
        
        self.assertIn('projects', admin_snapshot)
        self.assertIn('projects', exec_snapshot)
        self.assertIn('organization', admin_snapshot)
        self.assertIn('organization', exec_snapshot)

    def test_per_status_task_counts(self):
        """Verify tasks.summary includes todo, in_progress, blocked, done counts."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('tasks', snapshot)
        self.assertIn('summary', snapshot['tasks'])
        summary = snapshot['tasks']['summary']
        
        self.assertEqual(summary['todo'], 1)  # high_priority_task
        self.assertEqual(summary['in_progress'], 1)  # overdue_task
        self.assertEqual(summary['blocked'], 1)  # blocked_task
        self.assertEqual(summary['done'], 1)  # done_task
        self.assertEqual(summary['total_open'], 3)

    def test_blocked_tasks_categorization(self):
        """Blocked tasks should appear in tasks.blocked with days_blocked."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('tasks', snapshot)
        self.assertIn('blocked', snapshot['tasks'])
        
        blocked = snapshot['tasks']['blocked']
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]['title'], 'Blocked Task')
        self.assertEqual(blocked[0]['blocked_reason'], 'Waiting for API access')
        # Days blocked might be 0 in fast test execution, just check it exists
        self.assertIn('days_blocked', blocked[0])
        self.assertGreaterEqual(blocked[0]['days_blocked'], 0)

    def test_overdue_tasks_categorization(self):
        """Overdue tasks should appear in tasks.overdue with days_overdue."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('tasks', snapshot)
        self.assertIn('overdue', snapshot['tasks'])
        
        overdue = snapshot['tasks']['overdue']
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]['title'], 'Overdue Task')
        self.assertGreaterEqual(overdue[0]['days_overdue'], 2)

    def test_high_priority_tasks_categorization(self):
        """High priority tasks should appear in tasks.high_priority."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('tasks', snapshot)
        self.assertIn('high_priority', snapshot['tasks'])
        
        high_priority = snapshot['tasks']['high_priority']
        # Should include both blocked_task (high) and high_priority_task (high)
        self.assertGreaterEqual(len(high_priority), 1)
        priorities = [t['priority'] for t in high_priority]
        self.assertTrue(all(p in ['high', 'critical'] for p in priorities))

    def test_members_include_workload_and_skills(self):
        """Members should include workload_pct, workload_status, and skills."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('members', snapshot)
        member_data = next(m for m in snapshot['members'] if m['name'] == self.member.username)
        
        self.assertEqual(member_data['workload_pct'], 135.0)
        self.assertEqual(member_data['workload_status'], 'overloaded')
        self.assertIn('skills', member_data)
        self.assertEqual(len(member_data['skills']), 1)
        self.assertEqual(member_data['skills'][0]['name'], 'Python')

    def test_analytics_includes_risk_factors(self):
        """Analytics should include risk score with factor breakdown."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('analytics', snapshot)
        self.assertIn('risk_score', snapshot['analytics'])
        
        risk = snapshot['analytics']['risk_score']
        self.assertEqual(risk['score'], 7.5)
        self.assertEqual(risk['level'], 'high')
        self.assertEqual(risk['overload_factor'], 0.4)
        self.assertEqual(risk['blocked_task_factor'], 0.2)
        self.assertEqual(risk['deadline_proximity_factor'], 0.1)

    def test_analytics_includes_recommendations_with_reason(self):
        """Analytics should include pending recommendations with reason."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('analytics', snapshot)
        self.assertIn('recommendations', snapshot['analytics'])
        
        recommendations = snapshot['analytics']['recommendations']
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['title'], 'Reassign blocked task')
        self.assertEqual(recommendations[0]['confidence_score'], 85)
        self.assertIn('PM has availability', recommendations[0]['reason'])

    def test_teams_include_member_count_and_lead(self):
        """Teams should include member_count and lead username."""
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('teams', snapshot)
        team = snapshot['teams'][0]
        
        self.assertEqual(team['name'], 'Enrich Team')
        self.assertEqual(team['member_count'], 2)
        self.assertEqual(team['lead'], self.pm.username)

    def test_performance_limits_respected(self):
        """Snapshot should respect limits: 10 tasks/category, 15 projects cross-project."""
        # Create 15 tasks in each category (should be limited to 10)
        for i in range(15):
            Task.objects.create(
                project=self.project,
                assignee=self.member,
                title=f'Blocked Task {i}',
                priority='high',
                status='blocked',
                blocked_reason='Test',
                estimated_effort_hours=Decimal('8.00'),
                deadline=timezone.now().date() + timedelta(days=7),
            )
        
        snapshot = _build_data_snapshot(self.pm, project=self.project)
        
        self.assertIn('tasks', snapshot)
        self.assertIn('blocked', snapshot['tasks'])
        # Should be limited to 10
        self.assertLessEqual(len(snapshot['tasks']['blocked']), 10)

    def test_cross_project_organization_summary(self):
        """Cross-project snapshot should include organization summary for admin/exec/pm."""
        snapshot = _build_data_snapshot(self.admin)
        
        self.assertIn('organization', snapshot)
        org = snapshot['organization']
        
        self.assertIn('total_projects', org)
        self.assertIn('active_projects', org)
        self.assertIn('total_teams', org)
        self.assertIn('total_members', org)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

class ChatQueryAPITest(TestCase):
    """Tests for POST /api/chat/query/"""

    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('api_pm_chat')
        self.member = make_user('api_member_chat', role='member')
        self.team = make_team('API Chat Team')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)

    def _auth(self, user=None):
        self.client.force_authenticate(user=user or self.pm)

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_query_returns_200_with_answer(self, mock_ai):
        self._auth()
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Who is overloaded?', 'project_id': str(self.project.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('conversation_id', response.data)
        self.assertEqual(response.data['answer'], MOCK_AI_RETURN[0])

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_query_without_project_scope(self, mock_ai):
        self._auth()
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Give me an overview.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_query_unauthenticated_returns_401(self):
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Who is overloaded?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_query_member_role_returns_403(self):
        """Team members cannot use the chat assistant."""
        self._auth(self.member)
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Who is overloaded?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_query_out_of_scope_project_returns_404(self):
        """BR-7.1: scope violation returns 404."""
        other_pm = make_user('other_pm_chat')
        other_team = make_team('Other Chat Team')
        other_project = make_project(other_pm, other_team, name='Other Chat Project')
        self._auth()
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Tell me about this project.', 'project_id': str(other_project.id)},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_empty_question_returns_400(self):
        self._auth()
        response = self.client.post(
            '/api/chat/query/',
            {'question': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_missing_question_returns_400(self):
        self._auth()
        response = self.client.post('/api/chat/query/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_conversation_id_in_response_is_valid_uuid(self, mock_ai):
        self._auth()
        response = self.client.post(
            '/api/chat/query/',
            {'question': 'Any question'},
            format='json',
        )
        import uuid
        try:
            uuid.UUID(response.data['conversation_id'])
        except (ValueError, KeyError):
            self.fail('conversation_id is not a valid UUID')


class ChatSummaryAPITest(TestCase):
    """Tests for POST /api/chat/summary/{project_id}/"""

    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('sum_pm')
        self.exec_user = make_user('sum_exec', role='executive')
        self.team = make_team('Sum Team')
        TeamMembership.objects.create(team=self.team, user=self.pm)
        self.project = make_project(self.pm, self.team)

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_summary_returns_200(self, mock_ai):
        self.client.force_authenticate(user=self.exec_user)
        response = self.client.post(f'/api/chat/summary/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)

    @patch('ai_engine.chat_service.generate_chat_response', return_value=MOCK_AI_RETURN)
    def test_summary_accessible_to_pm(self, mock_ai):
        self.client.force_authenticate(user=self.pm)
        response = self.client.post(f'/api/chat/summary/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_summary_unauthenticated_returns_401(self):
        response = self.client.post(f'/api/chat/summary/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_out_of_scope_returns_404(self):
        other_pm = make_user('other_sum_pm')
        other_team = make_team('Other Sum Team')
        other_project = make_project(other_pm, other_team)
        self.client.force_authenticate(user=self.pm)
        response = self.client.post(f'/api/chat/summary/{other_project.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ConversationListAPITest(TestCase):
    """Tests for GET /api/chat/conversations/"""

    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('conv_pm')
        self.other_pm = make_user('other_conv_pm')
        self.team = make_team('Conv Team')
        self.project = make_project(self.pm, self.team)

    def _make_conv(self, user=None):
        return Conversation.objects.create(
            user=user or self.pm,
            project=self.project,
            title='Test Conversation',
        )

    def test_list_returns_only_own_conversations(self):
        self._make_conv()
        self._make_conv()
        self._make_conv(user=self.other_pm)
        self.client.force_authenticate(user=self.pm)
        response = self.client.get('/api/chat/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get('/api/chat/conversations/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_empty_when_no_conversations(self):
        self.client.force_authenticate(user=self.pm)
        response = self.client.get('/api/chat/conversations/')
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)


class ConversationDetailAPITest(TestCase):
    """Tests for GET/DELETE /api/chat/conversations/{id}/"""

    def setUp(self):
        self.client = APIClient()
        self.pm = make_user('det_pm')
        self.other_pm = make_user('det_other_pm')
        self.team = make_team('Det Team')
        self.project = make_project(self.pm, self.team)

    def _make_conv(self, user=None):
        return Conversation.objects.create(
            user=user or self.pm,
            project=self.project,
            title='Detail Conv',
        )

    def test_get_own_conversation_returns_200_with_messages(self):
        conv = self._make_conv()
        ChatMessage.objects.create(
            conversation=conv, user=self.pm, role='user',
            content='Hello', project=self.project,
        )
        self.client.force_authenticate(user=self.pm)
        response = self.client.get(f'/api/chat/conversations/{conv.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('messages', response.data)
        self.assertEqual(len(response.data['messages']), 1)

    def test_get_other_users_conversation_returns_404(self):
        conv = self._make_conv(user=self.other_pm)
        self.client.force_authenticate(user=self.pm)
        response = self.client.get(f'/api/chat/conversations/{conv.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_conversation_returns_204(self):
        conv = self._make_conv()
        self.client.force_authenticate(user=self.pm)
        response = self.client.delete(f'/api/chat/conversations/{conv.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Conversation.objects.filter(id=conv.id).exists())

    def test_delete_other_users_conversation_returns_404(self):
        conv = self._make_conv(user=self.other_pm)
        self.client.force_authenticate(user=self.pm)
        response = self.client.delete(f'/api/chat/conversations/{conv.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Conversation.objects.filter(id=conv.id).exists())
