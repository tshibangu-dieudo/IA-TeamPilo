from django.db import models
from django.utils import timezone
import uuid


class Recommendation(models.Model):
    """
    AI-generated recommendation for task redistribution, risk reduction, etc.
    """
    RECOMMENDATION_TYPE_CHOICES = [
        ('overloaded_member', 'Overloaded Member'),
        ('idle_member', 'Idle/Unassigned Member'),
        ('blocked_task', 'Blocked Task'),
        ('high_risk_project', 'High-Risk Project'),
        ('overdue_task', 'Overdue Task'),
        ('workload_imbalance', 'Workload Imbalance'),
        ('deadline_conflict', 'Deadline Conflict'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('dismissed', 'Dismissed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    GENERATED_BY_CHOICES = [
        ('granite', 'Granite AI'),
        ('fallback_template', 'Fallback Template'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(
        'projects.Project', 
        on_delete=models.CASCADE, 
        related_name='recommendations'
    )
    task = models.ForeignKey(
        'tasks.Task', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recommendations'
    )
    
    # Trackers for task reassignments
    current_assignee = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recommendations_current'
    )
    suggested_assignee = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recommendations_suggested'
    )

    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    explanation = models.TextField()  # Justification text

    confidence_score = models.IntegerField(default=50)  # 0 to 100
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generated_by = models.CharField(max_length=50, choices=GENERATED_BY_CHOICES, default='granite')

    accepted_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recommendations_accepted'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'recommendations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status'], name='reco_project_status_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"
