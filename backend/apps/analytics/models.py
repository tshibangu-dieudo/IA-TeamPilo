"""
Models for analytics app.
See .ai/coding-rules.md: Every model uses UUID primary key, has created_at/updated_at.
See docs/09_Database_Design.md §9-10 for full field specification.
"""
import uuid
from django.db import models


class WorkloadSnapshot(models.Model):
    """
    Snapshot of user workload at a point in time.
    See docs/09_Database_Design.md §9.
    BR-1.3: Workload status thresholds.
    """
    STATUS_CHOICES = [
        ('underloaded', 'Underloaded'),
        ('balanced', 'Balanced'),
        ('overloaded', 'Overloaded'),
        ('critically_overloaded', 'Critically Overloaded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='workload_snapshots',
    )
    workload_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workload_snapshots'
        ordering = ['-computed_at']
        indexes = [
            models.Index(fields=['user', 'computed_at'], name='workload_user_time_idx'),
        ]

    def __str__(self):
        return f"{self.user.full_name}: {self.workload_percentage}% ({self.status})"


class RiskScore(models.Model):
    """
    Project risk score calculation.
    See docs/09_Database_Design.md §10.
    BR-4.1: Risk score formula (weighted composite).
    BR-4.2: Risk level bands.
    """
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='risk_scores',
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    # Component scores (BR-4.1)
    overload_factor = models.DecimalField(max_digits=5, decimal_places=2)
    blocked_task_factor = models.DecimalField(max_digits=5, decimal_places=2)
    deadline_proximity_factor = models.DecimalField(max_digits=5, decimal_places=2)
    historical_velocity_factor = models.DecimalField(max_digits=5, decimal_places=2)

    explanation_text = models.TextField(blank=True)
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'risk_scores'
        ordering = ['-computed_at']
        indexes = [
            models.Index(fields=['project', 'computed_at'], name='risk_project_time_idx'),
        ]

    def __str__(self):
        return f"{self.project.name}: {self.score}% ({self.level})"
