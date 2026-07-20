"""
Models for tasks app.
See .ai/coding-rules.md: Every model uses UUID primary key, has created_at/updated_at.
See .ai/architecture.md: tasks/ - Task, TaskDependency, TaskStatusHistory.
See docs/09_Database_Design.md §8 for full field specification.
"""
import uuid
from django.db import models
from django.utils import timezone


class Task(models.Model):
    """
    Task entity.
    See docs/09_Database_Design.md §8.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('waiting_on_dependency', 'Waiting on Dependency'),
        ('done', 'Done'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    assignee = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='todo')
    estimated_effort_hours = models.DecimalField(max_digits=6, decimal_places=2)
    deadline = models.DateField()

    # Blocked fields — BR-3.1
    blocked_reason = models.TextField(blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)

    # Unassigned tracking — FR-TASK-009, BR-8.2
    unassigned_since = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status'], name='task_project_status_idx'),
            models.Index(fields=['assignee', 'status'], name='task_assignee_status_idx'),
        ]

    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    """
    Prerequisite relationship between tasks (self-referencing).
    See docs/09_Database_Design.md §8.2.
    BR-8.1: circular dependency rejected at application level.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependencies',
    )
    depends_on_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependents',
    )

    class Meta:
        db_table = 'task_dependencies'
        unique_together = ['task', 'depends_on_task']

    def __str__(self):
        return f"{self.task.title} depends on {self.depends_on_task.title}"


class TaskStatusHistory(models.Model):
    """
    History of task status changes.
    See docs/09_Database_Design.md §8.3.
    Feeds the Historical Velocity Factor (BR-4.1 W4).
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('waiting_on_dependency', 'Waiting on Dependency'),
        ('done', 'Done'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    changed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_status_changes',
    )
    previous_status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
    )
    new_status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_status_history'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.task.title}: {self.previous_status} → {self.new_status}"


class TaskSkill(models.Model):
    """
    Required skills for a task.
    See docs/09_Database_Design.md §8.1.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='required_skills')
    skill = models.ForeignKey('teams.Skill', on_delete=models.CASCADE, related_name='tasks_required')

    class Meta:
        db_table = 'task_skills'
        unique_together = ['task', 'skill']

    def __str__(self):
        return f"{self.task.title} requires {self.skill.name}"

