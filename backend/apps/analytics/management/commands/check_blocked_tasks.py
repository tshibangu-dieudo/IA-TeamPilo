"""
Management command: check for tasks that have been Blocked for more than 24 hours
and notify the Project Manager (FR-NOTIF-003, BR-3.2).

Architecture note: Uses management command + cron, consistent with recalculate_risk.py.
No Celery/Redis — see .ai/tech-stack.md.

Cron example (run every 30 minutes):
    */30 * * * * /path/to/venv/bin/python manage.py check_blocked_tasks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.tasks.models import Task
from apps.notifications.services import create_notification_service


class Command(BaseCommand):
    help = 'Notify PMs of tasks blocked for more than 24 hours (FR-NOTIF-003, BR-3.2)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print which notifications would fire without creating them.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        threshold = timezone.now() - timedelta(hours=24)

        # Find all tasks currently blocked for more than 24h
        blocked_tasks = (
            Task.objects
            .filter(status='blocked', blocked_at__lte=threshold)
            .select_related('project__owner', 'project')
        )

        count_found = blocked_tasks.count()
        count_notified = 0

        if count_found == 0:
            self.stdout.write('No tasks have been blocked for more than 24h.')
            return

        self.stdout.write(
            f'Found {count_found} task(s) blocked for more than 24h. '
            f'{"(dry run)" if dry_run else "Creating notifications..."}'
        )

        for task in blocked_tasks:
            hours_blocked = int(
                (timezone.now() - task.blocked_at).total_seconds() / 3600
            )
            pm = task.project.owner
            message = (
                f"Task '{task.title}' in project '{task.project.name}' "
                f"has been Blocked for approximately {hours_blocked} hour(s). "
                f"Reason: {task.blocked_reason or 'No reason provided.'}"
            )

            if dry_run:
                self.stdout.write(
                    f'  [DRY RUN] Would notify {pm.username} about task '
                    f'"{task.title}" (blocked ~{hours_blocked}h)'
                )
                count_notified += 1
                continue

            notification = create_notification_service(
                user=pm,
                notification_type='task_blocked',
                title='Task Blocked >24h',
                message=message,
                project=task.project,
                task=task,
            )

            if notification:
                count_notified += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Notified {pm.username}: task "{task.title}" '
                        f'(blocked ~{hours_blocked}h)'
                    )
                )
            else:
                self.stdout.write(
                    f'  Throttled (already notified recently): '
                    f'task "{task.title}" for {pm.username}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {count_notified}/{count_found} notification(s) '
                f'{"would be " if dry_run else ""}created.'
            )
        )
