from django.db import models
import uuid


class Notification(models.Model):
    """
    User notifications with throttling.
    See docs/09_Database_Design.md §12.
    BR-6.1: Notification triggers.
    BR-6.2: Throttling — at most one notification of the same type for the same
            object within a 1-hour window.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TYPE_CHOICES = [
        ('overload_alert', 'Overload Alert'),
        ('risk_alert', 'Risk Alert'),
        ('recommendation', 'Recommendation'),
        ('task_blocked', 'Task Blocked'),
        ('task_reassigned', 'Task Reassigned'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Link to related entity (optional, used as part of the throttle dedup key)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            # Fast unread-count queries and throttle window checks
            models.Index(
                fields=['user', 'is_read', 'created_at'],
                name='notif_user_read_time_idx',
            ),
            # Throttle dedup key lookups
            models.Index(
                fields=['user', 'notification_type', 'project', 'task', 'created_at'],
                name='notif_throttle_key_idx',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} | {self.notification_type} | {'read' if self.is_read else 'unread'}"
