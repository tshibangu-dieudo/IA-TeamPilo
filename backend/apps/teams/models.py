"""
Models for teams app.
See .ai/coding-rules.md: Every model uses UUID primary key, has created_at/updated_at.
See .ai/architecture.md: teams/ - Team, TeamMembership, Skill.
"""
from django.db import models
import uuid


class Team(models.Model):
    """
    Team entity.
    """
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member', 'Team Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Skill(models.Model):
    """
    Skill definitions available in the system.
    """
    PROFICIENCY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Expert'),
        (5, 'Master'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'skills'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    """
    Membership of a user in a team.
    """
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('member', 'Team Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        db_table = 'team_memberships'
        unique_together = ['team', 'user']
        ordering = ['team', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"
