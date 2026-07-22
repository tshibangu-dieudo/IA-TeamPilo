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

    @patch('ai_engine.chat_service.generate_chat_response', return_value=('Fallback answer.', 'fallback_template'))
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
        self.assertIn('project', snapshot)
        self.assertEqual(snapshot['project']['name'], self.project.name)

    def test_member_snapshot_contains_only_own_tasks(self):
        make_task(self.project, assignee=self.member)
        snapshot = _build_data_snapshot(self.member)
        self.assertIn('my_tasks', snapshot)
        self.assertNotIn('projects', snapshot)

    def test_executive_cross_project_snapshot_contains_projects(self):
        snapshot = _build_data_snapshot(self.exec_user)
        self.assertIn('projects', snapshot)


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
