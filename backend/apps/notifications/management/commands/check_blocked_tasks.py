"""
Management command: check_blocked_tasks
See docs/05_Business_Rules.md BR-3.2 and FR-NOTIF-003.

Fires a 'task_blocked' notification to the Project Manager when a task has
remained in 'blocked' status for more than 24 hours.

Architecture note: Uses a management command + cron pattern (no Celery),
consistent with apps/analytics/management/commands/recalculate_risk.py.
Throttling is handled inside create_notification_service (BR-6.2), so
running this command every hour is safe — duplicates within 1h are suppressed.

Recommended cron schedule: once per hour.
    0 * * * * /path/to/venv/bin/python manage.py check_blocked_tasks

Usage:
    python manage.py check_blocked_tasks
    python manage.py check_blocked_tasks --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.tasks.models import Task
from apps.notifications.services import create_notification_service


class Command(BaseCommand):
    help = (
        "Notify Project Managers when a task has been Blocked for more than 24 hours. "
        "Safe to run repeatedly — BR-6.2 throttling prevents duplicate alerts within 1h."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print eligible tasks without creating notifications.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        threshold = timezone.now() - timedelta(hours=24)

        # Find tasks blocked for more than 24h
        # Task.blocked_at is set by update_task_status_service when status → 'blocked'
        blocked_tasks = Task.objects.filter(
            status='blocked',
            blocked_at__isnull=False,
            blocked_at__lte=threshold,
        ).select_related('project__owner', 'assignee')

        count = blocked_tasks.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No tasks blocked >24h found.'))
            return

        notified = 0
        suppressed = 0

        for task in blocked_tasks:
            pm = task.project.owner
            blocked_hours = int(
                (timezone.now() - task.blocked_at).total_seconds() / 3600
            )
            title = "Task Blocked >24h"
            message = (
                f"Task '{task.title}' in project '{task.project.name}' "
                f"has been blocked for approximately {blocked_hours} hour(s). "
                f"Assignee: {task.assignee.username if task.assignee else 'Unassigned'}."
            )

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would notify PM '{pm.username}' — {message}"
                )
                notified += 1
                continue

            result = create_notification_service(
                user=pm,
                notification_type='task_blocked',
                title=title,
                message=message,
                project=task.project,
                task=task,
            )

            if result is not None:
                notified += 1
            else:
                suppressed += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would notify {notified} task(s).')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'check_blocked_tasks complete: {notified} notification(s) sent, '
                    f'{suppressed} suppressed by throttle.'
                )
            )
