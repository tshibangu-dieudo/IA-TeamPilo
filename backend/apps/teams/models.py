from django.db import models
import uuid


class Team(models.Model):
    """
    Team entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'teams'


class Skill(models.Model):
    """
    Skill definitions available in the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'skills'


class TeamMembership(models.Model):
    """
    Membership of a user in a team.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=50)  # e.g., 'Lead', 'Member'
    
    class Meta:
        db_table = 'team_memberships'
        unique_together = ['team', 'user']
