"""
Unit tests for accounts app.
See .ai/coding-rules.md: Write tests for business rules before simple CRUD.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserSkill
from .services import create_user_service, add_user_skill_service, remove_user_skill_service

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model functionality."""
    
    def test_create_user(self):
        """Test creating a standard user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, 'member')  # Default role
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
    
    def test_user_uuid_primary_key(self):
        """Test that User uses UUID primary key."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user.id)
        # Check that id is a UUID string, not an integer
        self.assertNotEqual(str(user.id), str(int(user.id)))


class UserSkillModelTest(TestCase):
    """Test UserSkill model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_user_skill(self):
        """Test creating a user skill."""
        skill = UserSkill.objects.create(
            user=self.user,
            skill_name='Python',
            proficiency_level=4
        )
        self.assertEqual(skill.skill_name, 'Python')
        self.assertEqual(skill.proficiency_level, 4)
    
    def test_unique_skill_per_user(self):
        """Test that a user cannot have duplicate skills."""
        UserSkill.objects.create(
            user=self.user,
            skill_name='Python',
            proficiency_level=4
        )
        # Attempting to create duplicate should fail
        with self.assertRaises(Exception):
            UserSkill.objects.create(
                user=self.user,
                skill_name='Python',
                proficiency_level=5
            )


class AccountsServiceTest(TestCase):
    """Test accounts business logic services."""
    
    def test_create_user_service(self):
        """Test user creation service."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        user = create_user_service(data)
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, 'member')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_add_user_skill_service(self):
        """Test adding a skill to a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        skill = add_user_skill_service(user, 'JavaScript', 3)
        self.assertEqual(skill.skill_name, 'JavaScript')
        self.assertEqual(skill.proficiency_level, 3)
    
    def test_update_existing_skill_service(self):
        """Test updating an existing skill."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        add_user_skill_service(user, 'Python', 3)
        skill = add_user_skill_service(user, 'Python', 5)
        self.assertEqual(skill.proficiency_level, 5)
    
    def test_remove_user_skill_service(self):
        """Test removing a skill from a user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        add_user_skill_service(user, 'Python', 3)
        result = remove_user_skill_service(user, 'Python')
        self.assertTrue(result)
        self.assertFalse(UserSkill.objects.filter(user=user, skill_name='Python').exists())
    
    def test_remove_nonexistent_skill_service(self):
        """Test removing a skill that doesn't exist."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        result = remove_user_skill_service(user, 'Nonexistent')
        self.assertFalse(result)


class AuthenticationAPITest(TestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_register_endpoint(self):
        """Test user registration endpoint."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Verify tokens are returned
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch."""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_endpoint(self):
        """Test login endpoint."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_current_user_endpoint(self):
        """Test getting current user profile."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_current_user_unauthenticated(self):
        """Test accessing current user without authentication."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionClassTest(TestCase):
    """Test permission classes."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.pm_user = User.objects.create_user(
            username='pm',
            email='pm@example.com',
            password='pmpass123',
            role='pm'
        )
        self.member_user = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='memberpass123',
            role='member'
        )
        self.executive_user = User.objects.create_user(
            username='executive',
            email='executive@example.com',
            password='executivepass123',
            role='executive'
        )
    
    def test_is_admin_permission(self):
        """Test IsAdmin permission class."""
        from .permissions import IsAdmin
        
        # Admin user should have permission
        self.client.force_authenticate(user=self.admin_user)
        request = self.client.get('/api/auth/users/').request
        permission = IsAdmin()
        self.assertTrue(permission.has_permission(request, None))
        
        # Non-admin user should not have permission
        self.client.force_authenticate(user=self.member_user)
        request = self.client.get('/api/auth/users/').request
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_admin_or_project_manager_permission(self):
        """Test IsAdminOrProjectManager permission class."""
        from .permissions import IsAdminOrProjectManager
        
        # Admin should have permission
        self.client.force_authenticate(user=self.admin_user)
        request = self.client.get('/api/auth/users/').request
        permission = IsAdminOrProjectManager()
        self.assertTrue(permission.has_permission(request, None))
        
        # PM should have permission
        self.client.force_authenticate(user=self.pm_user)
        request = self.client.get('/api/auth/users/').request
        self.assertTrue(permission.has_permission(request, None))
        
        # Member should not have permission
        self.client.force_authenticate(user=self.member_user)
        request = self.client.get('/api/auth/users/').request
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_admin_or_owner_object_permission(self):
        """Test IsAdminOrOwner object-level permission."""
        from .permissions import IsAdminOrOwner
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        
        # Admin should have permission on any object
        request = factory.get('/api/auth/skills/123/')
        request.user = self.admin_user
        permission = IsAdminOrOwner()
        self.assertTrue(permission.has_object_permission(request, None, self.member_user))
        
        # Owner should have permission on their own object
        request = factory.get('/api/auth/skills/123/')
        request.user = self.member_user
        self.assertTrue(permission.has_object_permission(request, None, self.member_user))
        
        # Non-owner should not have permission
        request = factory.get('/api/auth/skills/123/')
        request.user = self.pm_user
        self.assertFalse(permission.has_object_permission(request, None, self.member_user))
        
        # Unauthenticated user should not have permission
        request = factory.get('/api/auth/skills/123/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        self.assertFalse(permission.has_object_permission(request, None, self.member_user))


class RoleBasedAccessControlTest(TestCase):
    """Test role-based access control enforcement."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.member_user = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='memberpass123',
            role='member'
        )
    
    def test_admin_can_access_user_list(self):
        """Test that admin can access user list endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_admin_cannot_access_user_list(self):
        """Test that non-admin cannot access user list endpoint."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_scope_violation_returns_404(self):
        """Test that scope violations return 404, not 403 (business-rules.md:51)."""
        # Create a skill for admin user
        from .models import UserSkill
        skill = UserSkill.objects.create(
            user=self.admin_user,
            skill_name='Python',
            proficiency_level=5
        )
        
        # Try to access admin's skill as regular member
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(f'/api/auth/skills/{skill.id}/')
        
        # Should return 404 (not found) rather than 403 (forbidden)
        # This avoids leaking existence of data the user shouldn't know about
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
