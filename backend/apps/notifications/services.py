"""
Business logic for notifications app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
BR-6.1: Notification triggers (task_reassigned, recommendation, task_blocked,
         risk_alert, overload_alert).
BR-6.2: Throttling — at most one notification of the same type for the same
         (user, notification_type, project_id, task_id) composite key within a
         rolling 60-minute window. Returns None on suppression.
"""
from django.utils import timezone
from datetime import timedelta

from .models import Notification


# ---------------------------------------------------------------------------
# Core factory — the ONLY code path that creates Notification records.
# All callers (recommendations, analytics, tasks) MUST use this function.
# ---------------------------------------------------------------------------

def create_notification_service(
    user,
    notification_type,
    title,
    message,
    project=None,
    task=None,
):
    """
    Create a throttle-aware notification.

    Throttle rule (BR-6.2):
    - Dedup key: (user_id, notification_type, project_id, task_id).
    - If project and task are both None, dedup key is (user_id, notification_type).
    - If a matching Notification was created within the last 60 minutes, return None
      without creating a new record.

    Args:
        user: User instance — the recipient.
        notification_type: str — must be one of Notification.TYPE_CHOICES values.
        title: str
        message: str
        project: Project instance or None
        task: Task instance or None

    Returns:
        Notification instance if created, None if throttled.
    """
    one_hour_ago = timezone.now() - timedelta(hours=1)

    # Build the throttle filter — always include user + type
    throttle_filter = dict(
        user=user,
        notification_type=notification_type,
        created_at__gte=one_hour_ago,
    )
    # Extend with optional FK keys so different objects don't suppress each other
    if project is not None or task is not None:
        throttle_filter['project'] = project
        throttle_filter['task'] = task

    if Notification.objects.filter(**throttle_filter).exists():
        return None  # Throttled — suppress duplicate

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        project=project,
        task=task,
    )


# ---------------------------------------------------------------------------
# Read-state mutations — called by views, not by trigger services.
# ---------------------------------------------------------------------------

def mark_notification_read_service(notification):
    """
    Mark a single notification as read.
    Idempotent: if already read, returns the unchanged instance.

    Returns the notification instance.
    """
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at', 'updated_at'])
    return notification


def mark_all_read_service(user):
    """
    Mark all unread notifications for the given user as read in a single query.

    Returns the count of records updated.
    """
    now = timezone.now()
    count = Notification.objects.filter(
        user=user,
        is_read=False,
    ).update(is_read=True, read_at=now)
    return count
