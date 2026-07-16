from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """
    Custom User model with UUID primary key.
    See .ai/coding-rules.md: Every model uses UUID primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Role-based access control
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('pm', 'Project Manager'),
        ('member', 'Team Member'),
        ('executive', 'Executive Manager'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        db_table = 'users'


class UserSkill(models.Model):
    """
    Skills associated with a user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.IntegerField()  # 1-5 scale
    
    class Meta:
        db_table = 'user_skills'
        unique_together = ['user', 'skill_name']
