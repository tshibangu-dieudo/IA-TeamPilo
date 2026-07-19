"""
Models for projects app.
See .ai/coding-rules.md: Every model uses UUID primary key, has created_at/updated_at.
See .ai/architecture.md: projects/ - Project.
"""
from django.db import models
import uuid
from django.core.exceptions import ValidationError


class Project(models.Model):
    """
    Project entity.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='owned_projects')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='projects')
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at', 'name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate that end_date is after start_date."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})
