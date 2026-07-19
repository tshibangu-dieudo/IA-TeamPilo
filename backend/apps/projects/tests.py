"""
Unit tests for projects app.
See .ai/coding-rules.md: Write tests for business rules before simple CRUD.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Project
from .services import (
    create_project_service, update_project_service, delete_project_service,
    get_user_projects_service, get_team_projects_service, get_project_by_id_service
)
from teams.models import Team, TeamMembership

User = get_user_model()


class ProjectModelTest(TestCase):
    """Test Project model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
    
    def test_create_project(self):
        """Test creating a project."""
        project = Project.objects.create(
            name='Test Project',
            description='Test description',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.status, 'planning')
        self.assertIsNotNone(project.id)
    
    def test_project_uuid_primary_key(self):
        """Test that Project uses UUID primary key."""
        project = Project.objects.create(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        self.assertIsNotNone(project.id)
        self.assertNotEqual(str(project.id), str(int(project.id)))
    
    def test_project_str_representation(self):
        """Test Project string representation."""
        project = Project.objects.create(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        self.assertEqual(str(project), 'Test Project')
    
    def test_project_date_validation(self):
        """Test that end_date must be after start_date."""
        project = Project(
            name='Test Project',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today(),
            owner=self.user,
            team=self.team
        )
        with self.assertRaises(Exception):
            project.full_clean()


class ProjectsServiceTest(TestCase):
    """Test projects business logic services."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
    
    def test_create_project_service(self):
        """Test project creation service."""
        project = create_project_service(
            name='New Project',
            description='New description',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team,
            status='planning'
        )
        self.assertEqual(project.name, 'New Project')
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.team, self.team)
    
    def test_update_project_service(self):
        """Test project update service."""
        project = create_project_service(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        updated = update_project_service(project, name='Updated Project', status='active')
        self.assertEqual(updated.name, 'Updated Project')
        self.assertEqual(updated.status, 'active')
    
    def test_delete_project_service(self):
        """Test project deletion service."""
        project = create_project_service(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        delete_project_service(project)
        self.assertFalse(Project.objects.filter(id=project.id).exists())
    
    def test_get_user_projects_service(self):
        """Test getting user's projects."""
        TeamMembership.objects.create(team=self.team, user=self.user, role='member')
        
        project1 = create_project_service(
            name='Owned Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        other_user = User.objects.create_user(username='other', email='other@example.com', password='otherpass123')
        project2 = create_project_service(
            name='Team Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=other_user,
            team=self.team
        )
        
        projects = get_user_projects_service(self.user)
        self.assertEqual(len(projects), 2)
    
    def test_get_team_projects_service(self):
        """Test getting team's projects."""
        create_project_service(
            name='Team Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        projects = get_team_projects_service(self.team)
        self.assertEqual(len(projects), 1)
    
    def test_get_project_by_id_service(self):
        """Test getting project by ID."""
        project = create_project_service(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        found = get_project_by_id_service(project.id)
        self.assertEqual(found, project)
        
        not_found = get_project_by_id_service('00000000-0000-0000-0000-000000000000')
        self.assertIsNone(not_found)


class ProjectsAPITest(TestCase):
    """Test projects API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.team = Team.objects.create(name='Test Team')
        TeamMembership.objects.create(team=self.team, user=self.user, role='lead')
    
    def test_create_project_endpoint(self):
        """Test project creation endpoint."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Project',
            'description': 'New description',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'team': str(self.team.id)
        }
        response = self.client.post('/api/projects/projects/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(name='New Project').exists())
    
    def test_create_project_invalid_dates(self):
        """Test project creation with invalid dates."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Invalid Project',
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today(),
            'team': str(self.team.id)
        }
        response = self.client.post('/api/projects/projects/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_projects_endpoint(self):
        """Test listing projects endpoint."""
        create_project_service(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/projects/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_retrieve_project_endpoint(self):
        """Test retrieving a project endpoint."""
        project = create_project_service(
            name='Test Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/projects/projects/{project.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')
    
    def test_unauthenticated_cannot_access_projects(self):
        """Test that unauthenticated users cannot access projects."""
        response = self.client.get('/api/projects/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_my_projects_endpoint(self):
        """Test my projects endpoint."""
        create_project_service(
            name='My Project',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            owner=self.user,
            team=self.team
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/projects/my-projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
