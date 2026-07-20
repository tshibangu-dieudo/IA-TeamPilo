"""
Unit tests for teams app.
See .ai/coding-rules.md: Write tests for business rules before simple CRUD.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Team, Skill, TeamMembership
from .services import (
    create_team_service, add_team_member_service, remove_team_member_service,
    update_team_member_role_service, create_skill_service, get_user_teams_service
)

User = get_user_model()


class TeamModelTest(TestCase):
    """Test Team model functionality."""
    
    def test_create_team(self):
        """Test creating a team."""
        team = Team.objects.create(name='Engineering Team', description='Backend development team')
        self.assertEqual(team.name, 'Engineering Team')
        self.assertEqual(team.description, 'Backend development team')
        self.assertIsNotNone(team.id)
    
    def test_team_uuid_primary_key(self):
        """Test that Team uses UUID primary key."""
        team = Team.objects.create(name='Test Team')
        self.assertIsNotNone(team.id)
        self.assertNotEqual(str(team.id), str(int(team.id)))
    
    def test_team_str_representation(self):
        """Test Team string representation."""
        team = Team.objects.create(name='Test Team')
        self.assertEqual(str(team), 'Test Team')


class SkillModelTest(TestCase):
    """Test Skill model functionality."""
    
    def test_create_skill(self):
        """Test creating a skill."""
        skill = Skill.objects.create(name='Python', description='Programming language')
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(skill.description, 'Programming language')
    
    def test_skill_unique_name(self):
        """Test that skill names are unique."""
        Skill.objects.create(name='Python')
        with self.assertRaises(Exception):
            Skill.objects.create(name='Python')


class TeamMembershipModelTest(TestCase):
    """Test TeamMembership model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
    
    def test_create_membership(self):
        """Test creating a team membership."""
        membership = TeamMembership.objects.create(team=self.team, user=self.user, role='member')
        self.assertEqual(membership.team, self.team)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, 'member')
    
    def test_unique_team_user(self):
        """Test that a user can only have one membership per team."""
        TeamMembership.objects.create(team=self.team, user=self.user, role='member')
        with self.assertRaises(Exception):
            TeamMembership.objects.create(team=self.team, user=self.user, role='lead')
    
    def test_membership_str_representation(self):
        """Test TeamMembership string representation."""
        membership = TeamMembership.objects.create(team=self.team, user=self.user, role='member')
        expected = f"{self.user.username} - {self.team.name} (member)"
        self.assertEqual(str(membership), expected)


class TeamsServiceTest(TestCase):
    """Test teams business logic services."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
    
    def test_create_team_service(self):
        """Test team creation service."""
        team = create_team_service('New Team', 'Description')
        self.assertEqual(team.name, 'New Team')
        self.assertEqual(team.description, 'Description')
    
    def test_add_team_member_service(self):
        """Test adding a team member."""
        membership = add_team_member_service(self.team, self.user, 'member')
        self.assertEqual(membership.team, self.team)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, 'member')
    
    def test_update_existing_membership_service(self):
        """Test updating an existing membership."""
        add_team_member_service(self.team, self.user, 'member')
        membership = add_team_member_service(self.team, self.user, 'lead')
        self.assertEqual(membership.role, 'lead')
    
    def test_remove_team_member_service(self):
        """Test removing a team member."""
        add_team_member_service(self.team, self.user, 'member')
        result = remove_team_member_service(self.team, self.user)
        self.assertTrue(result)
        self.assertFalse(TeamMembership.objects.filter(team=self.team, user=self.user).exists())
    
    def test_remove_nonexistent_member_service(self):
        """Test removing a non-existent member."""
        result = remove_team_member_service(self.team, self.user)
        self.assertFalse(result)
    
    def test_update_team_member_role_service(self):
        """Test updating team member role."""
        add_team_member_service(self.team, self.user, 'member')
        membership = update_team_member_role_service(self.team, self.user, 'lead')
        self.assertEqual(membership.role, 'lead')
    
    def test_update_nonexistent_member_role_service(self):
        """Test updating role for non-existent member."""
        membership = update_team_member_role_service(self.team, self.user, 'lead')
        self.assertIsNone(membership)
    
    def test_create_skill_service(self):
        """Test skill creation service."""
        skill = create_skill_service('JavaScript', 'Web development')
        self.assertEqual(skill.name, 'JavaScript')
        self.assertEqual(skill.description, 'Web development')
    
    def test_get_user_teams_service(self):
        """Test getting user's teams."""
        add_team_member_service(self.team, self.user, 'member')
        teams = get_user_teams_service(self.user)
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0], self.team)


class TeamsAPITest(TestCase):
    """Test teams API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
        add_team_member_service(self.team, self.user, 'lead')
    
    def test_create_team_endpoint(self):
        """Test team creation endpoint."""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'New Team', 'description': 'New description'}
        response = self.client.post('/api/teams/teams/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Team.objects.filter(name='New Team').exists())
    
    def test_list_teams_endpoint(self):
        """Test listing teams endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/teams/teams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The endpoint uses DRF pagination — unwrap 'results' if present
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
    
    def test_retrieve_team_endpoint(self):
        """Test retrieving a team endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/teams/teams/{self.team.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Team')
    
    def test_unauthenticated_cannot_access_teams(self):
        """Test that unauthenticated users cannot access teams."""
        response = self.client.get('/api/teams/teams/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_skill_endpoint(self):
        """Test skill creation endpoint."""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'React', 'description': 'Frontend framework'}
        response = self.client.post('/api/teams/skills/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_add_team_member_endpoint(self):
        """Test adding team member endpoint."""
        new_user = User.objects.create_user(username='newuser', email='new@example.com', password='newpass123')
        self.client.force_authenticate(user=self.user)
        data = {'team': str(self.team.id), 'user': str(new_user.id), 'role': 'member'}
        response = self.client.post('/api/teams/memberships/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_my_teams_endpoint(self):
        """Test my teams endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/teams/my-teams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The endpoint uses DRF pagination — unwrap 'results' if present
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
