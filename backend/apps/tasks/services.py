"""
Business logic for tasks app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
See docs/05_Business_Rules.md for all referenced BR-* rules.
"""
from django.utils import timezone
from django.db import transaction

from .models import Task, TaskDependency, TaskStatusHistory


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

def create_task_service(project, title, description, priority, estimated_effort_hours,
                        deadline, assignee=None):
    """
    Create a new task and record the initial status history entry.
    BR-8.2: task cannot exist without a project.
    """
    with transaction.atomic():
        task = Task.objects.create(
            project=project,
            title=title,
            description=description,
            priority=priority,
            estimated_effort_hours=estimated_effort_hours,
            deadline=deadline,
            assignee=assignee,
            status='todo',
            unassigned_since=timezone.now() if assignee is None else None,
        )
        # Record initial status history (previous_status is None for creation)
        TaskStatusHistory.objects.create(
            task=task,
            changed_by=assignee,
            previous_status=None,
            new_status='todo',
        )
    return task


def update_task_service(task, changed_by, **kwargs):
    """
    Update mutable task fields.
    Delegates status transitions to update_task_status_service.
    """
    new_status = kwargs.pop('status', None)
    for key, value in kwargs.items():
        setattr(task, key, value)
    task.save()
    if new_status and new_status != task.status:
        task = update_task_status_service(task, new_status, changed_by,
                                          blocked_reason=kwargs.get('blocked_reason', ''))
    return task


def get_tasks_for_project_service(project):
    """
    Return all tasks for a project, with related fields pre-fetched.
    """
    return (
        Task.objects.filter(project=project)
        .select_related('assignee', 'project')
        .prefetch_related('dependencies', 'dependents')
    )


def get_task_by_id_service(task_id):
    """
    Fetch a single task by PK. Returns None if not found.
    """
    try:
        return Task.objects.select_related('assignee', 'project').get(id=task_id)
    except Task.DoesNotExist:
        return None


def get_tasks_for_user_service(user):
    """
    Return all tasks assigned to the given user.
    Used for GET /users/me/tasks (US-3.3).
    """
    return (
        Task.objects.filter(assignee=user)
        .select_related('project', 'assignee')
        .order_by('-created_at')
    )


# ---------------------------------------------------------------------------
# Status transition — BR-3.1, BR-3.3
# ---------------------------------------------------------------------------

def update_task_status_service(task, new_status, changed_by, blocked_reason=''):
    """
    Transition a task to a new status.
    - BR-3.1: blocked_reason required when status == 'blocked'.
    - Records a TaskStatusHistory row on every transition.
    """
    if new_status == 'blocked' and not blocked_reason:
        raise ValueError("blocked_reason is required when status is 'blocked'.")

    old_status = task.status

    with transaction.atomic():
        task.status = new_status

        if new_status == 'blocked':
            task.blocked_reason = blocked_reason
            task.blocked_at = timezone.now()
        else:
            task.blocked_at = None
            task.blocked_reason = ''

        task.save(update_fields=['status', 'blocked_reason', 'blocked_at', 'updated_at'])

        TaskStatusHistory.objects.create(
            task=task,
            changed_by=changed_by,
            previous_status=old_status,
            new_status=new_status,
        )

    return task


# ---------------------------------------------------------------------------
# Dependency management — BR-8.1
# ---------------------------------------------------------------------------

def _has_circular_dependency(task_id, depends_on_id, visited=None):
    """
    DFS check: would adding depends_on_id as a prerequisite of task_id
    create a cycle?
    BR-8.1: reject any configuration that creates a circular reference.

    Both task_id and depends_on_id must be str(uuid) throughout — the
    .values_list() call returns UUID objects from the DB, so we normalise
    every value to str() before comparing or recursing to avoid a silent
    type mismatch that would cause cycles to go undetected.
    """
    if visited is None:
        visited = set()
    # Normalise to str so UUID objects and str keys compare correctly
    task_id = str(task_id)
    depends_on_id = str(depends_on_id)
    if depends_on_id == task_id:
        return True
    if depends_on_id in visited:
        return False
    visited.add(depends_on_id)
    for dep in TaskDependency.objects.filter(task_id=depends_on_id).values_list(
        'depends_on_task_id', flat=True
    ):
        if _has_circular_dependency(task_id, str(dep), visited):
            return True
    return False


def add_task_dependency_service(task, depends_on_task):
    """
    Add a prerequisite dependency.
    Raises ValueError on self-reference or circular dependency (BR-8.1).
    Returns the created TaskDependency.
    """
    if task.pk == depends_on_task.pk:
        raise ValueError("A task cannot depend on itself.")

    if _has_circular_dependency(str(task.pk), str(depends_on_task.pk)):
        raise ValueError(
            f"Adding this dependency would create a circular reference "
            f"between '{task.title}' and '{depends_on_task.title}'."
        )

    dependency, _ = TaskDependency.objects.get_or_create(
        task=task,
        depends_on_task=depends_on_task,
    )

    # Update dependent task status if prerequisite is not done — BR-3.3
    _refresh_waiting_on_dependency(task)

    return dependency


def remove_task_dependency_service(task, depends_on_task):
    """
    Remove a dependency. Re-evaluates 'waiting_on_dependency' status.
    """
    TaskDependency.objects.filter(task=task, depends_on_task=depends_on_task).delete()
    _refresh_waiting_on_dependency(task)


def _refresh_waiting_on_dependency(task):
    """
    BR-3.3: if any prerequisite is not Done, mark task as 'waiting_on_dependency'.
    If all prerequisites are Done (or there are none), revert to 'todo' unless
    the task is already in a more advanced status.
    Only changes status when it is currently 'waiting_on_dependency' or 'todo'.
    """
    if task.status in ('blocked', 'in_progress', 'done'):
        return

    unfinished_deps = TaskDependency.objects.filter(task=task).exclude(
        depends_on_task__status='done'
    ).exists()

    if unfinished_deps and task.status != 'waiting_on_dependency':
        task.status = 'waiting_on_dependency'
        task.save(update_fields=['status', 'updated_at'])
    elif not unfinished_deps and task.status == 'waiting_on_dependency':
        task.status = 'todo'
        task.save(update_fields=['status', 'updated_at'])


# ---------------------------------------------------------------------------
# Priority auto-escalation — BR-2.2
# ---------------------------------------------------------------------------

PRIORITY_ORDER = ['low', 'medium', 'high', 'critical']


def auto_escalate_priority_service(task):
    """
    BR-2.2: if task deadline is within 48 hours and status is not 'done',
    escalate priority by one level (cap at 'critical').
    Returns the (possibly updated) task.
    """
    if task.status == 'done':
        return task

    now = timezone.now().date()
    hours_until_deadline = (task.deadline - now).total_seconds() / 3600

    if hours_until_deadline <= 48:
        current_index = PRIORITY_ORDER.index(task.priority)
        if current_index < len(PRIORITY_ORDER) - 1:
            task.priority = PRIORITY_ORDER[current_index + 1]
            task.save(update_fields=['priority', 'updated_at'])

    return task


# ---------------------------------------------------------------------------
# Status history query
# ---------------------------------------------------------------------------

def get_task_status_history_service(task):
    """
    Return all status history entries for a task, most recent first.
    """
    return TaskStatusHistory.objects.filter(task=task).select_related('changed_by')
