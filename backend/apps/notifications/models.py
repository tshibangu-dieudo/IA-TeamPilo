from django.db import models
import uuid


class Notification(models.Model):
    """
    User notifications with throttling.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    TYPE_CHOICES = [
        ('overload_alert', 'Overload Alert'),
        ('risk_alert', 'Risk Alert'),
        ('recommendation', 'Recommendation'),
        ('task_blocked', 'Task Blocked'),
    ]
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Link to related entity (optional)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    class Meta:
        db_table = 'notifications'
