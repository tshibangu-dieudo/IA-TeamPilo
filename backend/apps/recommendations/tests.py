from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, UserSkill
from apps.teams.models import Team, TeamMembership, Skill
from apps.projects.models import Project
from apps.tasks.models import Task, TaskSkill, TaskDependency, TaskStatusHistory
from apps.analytics.models import RiskScore
from apps.notifications.models import Notification

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services import (
    generate_recommendations_for_project_service,
    accept_recommendation_service,
    dismiss_recommendation_service,
)
from ai_engine.langchain_client import AIConnectionError


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def create_user(username, role='member'):
    return User.objects.create_user(
        username=username,
        email=f"{username}@teampilot.test",
        password="testpassword",
        role=role
    )


def create_team(name="Test Team"):
    return Team.objects.create(name=name)


def create_project(owner, team, name="Test Project"):
    return Project.objects.create(
        name=name,
        description="A project for testing.",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=14), # 2-week sprint window
        status='active',
        owner=owner,
        team=team
    )


def create_task(project, assignee=None, status='todo', effort=8.0, deadline_offset=5):
    return Task.objects.create(
        project=project,
        assignee=assignee,
        title="Test Task",
        description="Task desc",
        priority='medium',
        status=status,
        estimated_effort_hours=Decimal(str(effort)),
        deadline=date.today() + timedelta(days=deadline_offset)
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class RecommendationModelTest(TestCase):
    def setUp(self):
        self.pm = create_user("reco_pm", role="pm")
        self.member = create_user("reco_mem", role="member")
        self.team = create_team()
        self.project = create_project(self.pm, self.team)
        self.task = create_task(self.project, assignee=self.member)

    def test_recommendation_creation(self):
        reco = Recommendation.objects.create(
            project=self.project,
            task=self.task,
            current_assignee=self.member,
            suggested_assignee=self.pm,
            recommendation_type='overloaded_member',
            title="Offload Task",
            description="Reassign task.",
            explanation="Explanation",
            confidence_score=90,
            priority='medium',
            status='pending',
            generated_by='granite'
        )
        self.assertEqual(reco.status, 'pending')
        self.assertEqual(reco.confidence_score, 90)
        self.assertEqual(reco.generated_by, 'granite')
        self.assertEqual(str(reco), "Offload Task (pending)")


class RecommendationSerializerTest(TestCase):
    def setUp(self):
        self.pm = create_user("ser_pm", role="pm")
        self.member = create_user("ser_mem", role="member")
        self.team = create_team()
        self.project = create_project(self.pm, self.team)
        self.task = create_task(self.project, assignee=self.member)
        self.reco = Recommendation.objects.create(
            project=self.project,
            task=self.task,
            current_assignee=self.member,
            suggested_assignee=self.pm,
            recommendation_type='overloaded_member',
            title="Offload Task",
            description="Reassign task.",
            explanation="This is the Granite justification text.",
            confidence_score=85,
            priority='medium',
            status='pending'
        )

    def test_serializer_outputs(self):
        serializer = RecommendationSerializer(self.reco)
        data = serializer.data
        
        # Test custom fields and formatting mapping
        self.assertEqual(data['justification'], "This is the Granite justification text.")
        self.assertEqual(data['confidence_level'], 'HIGH')
        
        # Test nested format mappings
        self.assertEqual(data['task']['title'], self.task.title)
        self.assertEqual(data['current_assignee']['username'], self.member.username)
        self.assertEqual(data['suggested_assignee']['username'], self.pm.username)


class RecommendationServicesTest(TestCase):
    def setUp(self):
        self.pm = create_user("srv_pm", role="pm")
        self.overloaded_dev = create_user("overloaded_dev", role="member")
        self.idle_dev = create_user("idle_dev", role="member")
        
        self.team = create_team()
        TeamMembership.objects.create(team=self.team, user=self.pm, role='lead')
        TeamMembership.objects.create(team=self.team, user=self.overloaded_dev, role='member')
        TeamMembership.objects.create(team=self.team, user=self.idle_dev, role='member')
        
        self.project = create_project(self.pm, self.team)
        
        # Define skills
        self.python_skill = Skill.objects.create(name="Python")
        
        # Associate user skills
        UserSkill.objects.create(user=self.idle_dev, skill_name="Python", proficiency_level=4)
        UserSkill.objects.create(user=self.overloaded_dev, skill_name="Python", proficiency_level=3)
        
        # Create tasks to overload overloaded_dev (capacity = 40h, sprint duration = 2 weeks)
        # Total capacity = 80h. Let's create tasks totaling 90h
        self.task1 = create_task(self.project, assignee=self.overloaded_dev, effort=50)
        self.task2 = create_task(self.project, assignee=self.overloaded_dev, effort=40)
        
        # Link skills to task2
        TaskSkill.objects.create(task=self.task2, skill=self.python_skill)

    def test_overloaded_member_trigger_and_ranking(self):
        # Generate recommendations
        recos = generate_recommendations_for_project_service(self.project)
        
        # Must find at least one recommendation for overloaded_dev
        self.assertGreaterEqual(len(recos), 1)
        
        # Find the overloaded_member recommendation specifically
        overload_recos = [r for r in recos if r.recommendation_type == 'overloaded_member']
        self.assertGreaterEqual(len(overload_recos), 1)
        reco = overload_recos[0]
        
        # BR-5.1: The recommendation must be about the overloaded user
        self.assertEqual(reco.current_assignee.id, self.overloaded_dev.id)
        
        # BR-5.2: The suggested assignee must NOT be the overloaded user themselves
        self.assertNotEqual(reco.suggested_assignee.id, self.overloaded_dev.id)
        
        # BR-5.3: The suggested assignee must be a valid team member
        valid_candidates = {self.idle_dev.id, self.pm.id}
        self.assertIn(reco.suggested_assignee.id, valid_candidates)
        
        # The task picked must be one assigned to the overloaded user
        self.assertEqual(reco.task.assignee.id, self.overloaded_dev.id)
        
        # Verify fallback path was used (WATSONX credentials absent in test environment)
        self.assertEqual(reco.generated_by, 'fallback_template')
        self.assertIn(self.overloaded_dev.username, reco.explanation)

    def test_accept_recommendation_workflow(self):
        # Create recommendation
        reco = Recommendation.objects.create(
            project=self.project,
            task=self.task2,
            current_assignee=self.overloaded_dev,
            suggested_assignee=self.idle_dev,
            recommendation_type='overloaded_member',
            title="Offload Python Task",
            description="Reassign task.",
            explanation="Reassign task.",
            confidence_score=90,
            priority='medium',
            status='pending'
        )
        
        # Accept recommendation
        accept_recommendation_service(reco, self.pm)
        
        # Re-fetch objects and verify changes applied
        reco.refresh_from_db()
        self.task2.refresh_from_db()
        
        self.assertEqual(reco.status, 'accepted')
        self.assertEqual(reco.accepted_by, self.pm)
        self.assertEqual(self.task2.assignee, self.idle_dev) # Assignee successfully updated!
        
        # Verify status history logged
        history = TaskStatusHistory.objects.filter(task=self.task2)
        self.assertTrue(history.exists())
        
        # Verify notification created for the new assignee
        notification = Notification.objects.filter(user=self.idle_dev, notification_type='task_reassigned').first()
        self.assertIsNotNone(notification)

    def test_dismiss_recommendation(self):
        reco = Recommendation.objects.create(
            project=self.project,
            task=self.task2,
            current_assignee=self.overloaded_dev,
            suggested_assignee=self.idle_dev,
            recommendation_type='overloaded_member',
            title="Offload Task",
            description="Reassign task.",
            explanation="Reassign task.",
            confidence_score=90,
            priority='medium',
            status='pending'
        )
        
        dismiss_recommendation_service(reco, self.pm)
        reco.refresh_from_db()
        self.assertEqual(reco.status, 'dismissed')
        self.assertIsNotNone(reco.dismissed_at)


class RecommendationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pm = create_user("api_pm", role="pm")
        self.member = create_user("api_member", role="member")
        self.team = create_team()
        TeamMembership.objects.create(team=self.team, user=self.pm, role='lead')
        TeamMembership.objects.create(team=self.team, user=self.member, role='member')
        self.project = create_project(self.pm, self.team)
        self.task = create_task(self.project, assignee=self.member)
        
        self.reco = Recommendation.objects.create(
            project=self.project,
            task=self.task,
            current_assignee=self.member,
            suggested_assignee=self.pm,
            recommendation_type='overloaded_member',
            title="Reassign Task",
            description="Details",
            explanation="Justification",
            confidence_score=90,
            priority='medium',
            status='pending'
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_recommendations_authenticated(self):
        self._auth(self.pm)
        response = self.client.get('/api/recommendations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The view uses pagination: response is {'count': N, 'results': [...]}
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)

    def test_project_recommendations_scope(self):
        self._auth(self.pm)
        response = self.client.get(f'/api/recommendations/project/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_recommendations_scope_leakage_404(self):
        # Other PM should not see recommendation for PM's project and get 404
        other_pm = create_user("other_pm", role="pm")
        self._auth(other_pm)
        response = self.client.get(f'/api/recommendations/project/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_recommendation_api(self):
        self._auth(self.pm)
        response = self.client.patch(f'/api/recommendations/{self.reco.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')

    def test_dismiss_recommendation_api(self):
        self._auth(self.pm)
        response = self.client.patch(f'/api/recommendations/{self.reco.id}/dismiss/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'dismissed')


class AIEngineMockTest(TestCase):
    @patch('apps.recommendations.services.generate_recommendation_justification')
    def test_watsonx_mocked_success(self, mock_ai_service):
        mock_ai_service.return_value = ("Marie has Django skills and low workload.", "granite")
        
        # Test service layer generates and stores recommendation using the mocked value
        from apps.recommendations.services import create_recommendation_and_notify
        pm = create_user("test_ai_pm", role="pm")
        team = create_team()
        project = create_project(pm, team)
        task = create_task(project)
        
        reco = create_recommendation_and_notify(
            project=project,
            task=task,
            current_assignee=None,
            suggested_assignee=pm,
            recommendation_type='overloaded_member',
            title="AI Reassignment",
            description="reassign",
            confidence_score=95,
            priority='medium',
            overloaded_user_name="Overloaded",
            overloaded_workload=120,
            candidate_name=pm.username,
            candidate_workload=40,
            candidate_skills=['Django'],
            task_title=task.title,
            task_hours=10,
            task_deadline=task.deadline,
            candidate_rank_reason="best match"
        )
        
        self.assertIsNotNone(reco)
        self.assertEqual(reco.explanation, "Marie has Django skills and low workload.")
        self.assertEqual(reco.generated_by, "granite")

