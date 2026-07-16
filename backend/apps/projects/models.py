from django.db import models
import uuid


class Project(models.Model):
    """
    Project entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='owned_projects')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='projects')
    
    class Meta:
        db_table = 'projects'
