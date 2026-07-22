"""
Business logic for analytics app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
See docs/05_Business_Rules.md for all referenced BR-* rules.
"""
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import WorkloadSnapshot, RiskScore


# ---------------------------------------------------------------------------
# Workload Calculation — BR-1.2, BR-1.3
# ---------------------------------------------------------------------------

def calculate_workload_service(user, project, sprint_start_date, sprint_end_date):
    """
    Calculate workload % for a user within a sprint window.
    BR-1.2: Workload % = (Sum of estimated effort hours of all open tasks assigned to the user
              that fall within the current sprint window) / (User's weekly capacity × sprint length in weeks) × 100
    BR-1.3: Workload status thresholds.
    
    Args:
        user: User instance
        project: Project instance (to scope tasks)
        sprint_start_date: Date object or string (YYYY-MM-DD)
        sprint_end_date: Date object or string (YYYY-MM-DD)
    
    Returns:
        tuple: (workload_percentage, status)
    """
    from apps.tasks.models import Task
    
    # Parse dates if strings
    if isinstance(sprint_start_date, str):
        sprint_start_date = parse_date(sprint_start_date)
    if isinstance(sprint_end_date, str):
        sprint_end_date = parse_date(sprint_end_date)
    
    # Get user's weekly capacity (default 40 if not set)
    weekly_capacity = getattr(user, 'weekly_capacity_hours', 40) or 40
    
    # Calculate sprint length in weeks
    sprint_length_days = (sprint_end_date - sprint_start_date).days
    sprint_length_weeks = max(sprint_length_days / 7, 1)  # Avoid division by zero
    
    # Get all open tasks assigned to the user within the sprint window
    # Open tasks: status not 'done'
    open_tasks = Task.objects.filter(
        assignee=user,
        project=project,
        deadline__gte=sprint_start_date,
        deadline__lte=sprint_end_date,
        status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency']
    )
    
    # Sum estimated effort hours
    total_estimated_hours = sum(
        task.estimated_effort_hours for task in open_tasks
    )
    
    # Calculate workload percentage — round to 2 dp for consistent comparisons
    # (avoids float imprecision, e.g. 92/80*100 = 115.00000000000001)
    capacity_for_sprint = weekly_capacity * sprint_length_weeks
    if capacity_for_sprint == 0:
        workload_percentage = 0
    else:
        workload_percentage = round(
            (float(total_estimated_hours) / float(capacity_for_sprint)) * 100, 2
        )
    # Determine status based on BR-1.3 thresholds
    if workload_percentage <= 60:
        status = 'underloaded'
    elif workload_percentage <= 99:
        status = 'balanced'
    elif workload_percentage <= 120:
        status = 'overloaded'
    else:
        status = 'critically_overloaded'
    
    return workload_percentage, status


def create_workload_snapshot_service(user, project, sprint_start_date, sprint_end_date):
    """
    Create a workload snapshot for a user.
    Stores the calculated workload % and status.
    After saving the snapshot, checks if an overload alert should fire (BR-1.4)
    and dispatches the notification through create_notification_service (FR-NOTIF-003 type:
    overload_alert) if the check_overload_alert_service gate passes.
    """
    workload_percentage, status = calculate_workload_service(
        user, project, sprint_start_date, sprint_end_date
    )

    snapshot = WorkloadSnapshot.objects.create(
        user=user,
        project=project,
        workload_percentage=workload_percentage,
        status=status,
    )

    # Fire overload alert notification if the BR-1.4 gate passes.
    # check_overload_alert_service reads the snapshot we just saved, so we call it after
    # the snapshot is committed.
    if status in ('overloaded', 'critically_overloaded'):
        should_alert = check_overload_alert_service(
            user, project, sprint_start_date, sprint_end_date
        )
        if should_alert:
            from apps.notifications.services import create_notification_service
            create_notification_service(
                user=user,
                notification_type='overload_alert',
                title='Workload Overload Alert',
                message=(
                    f"{user.username} is currently at {workload_percentage:.0f}% workload "
                    f"({status.replace('_', ' ').title()}) on project '{project.name}'."
                ),
                project=project,
                task=None,
            )

    return snapshot


def check_overload_alert_service(user, project, sprint_start_date, sprint_end_date):
    """
    Check if an overload alert should be triggered for a user.
    BR-1.4: Alert triggered when status changes to Overloaded or Critically Overloaded,
            not re-triggered within 24h unless workload increases by 15pp.
    
    Returns:
        bool: True if alert should be triggered
    """
    current_workload, current_status = calculate_workload_service(
        user, project, sprint_start_date, sprint_end_date
    )
    
    # Only check if currently overloaded or critically overloaded
    if current_status not in ['overloaded', 'critically_overloaded']:
        return False
    
    # Get most recent snapshot within last 24 hours
    from datetime import timedelta
    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    
    recent_snapshot = WorkloadSnapshot.objects.filter(
        user=user,
        project=project,
        computed_at__gte=twenty_four_hours_ago
    ).order_by('-computed_at').first()
    
    # No recent snapshot - trigger alert
    if not recent_snapshot:
        return True
    
    # Check if workload increased by 15 percentage points
    workload_increase = current_workload - float(recent_snapshot.workload_percentage)
    if workload_increase >= 15:
        return True
    
    # Check if status changed from non-overloaded to overloaded
    if recent_snapshot.status not in ['overloaded', 'critically_overloaded']:
        return True
    
    return False


# ---------------------------------------------------------------------------
# Risk Score Calculation — BR-4.1, BR-4.2
# ---------------------------------------------------------------------------

def calculate_risk_score_service(project):
    """
    Calculate project risk score as weighted composite.
    BR-4.1: Risk Score = (W1 × Overload Factor) + (W2 × Blocked Task Factor)
                        + (W3 × Deadline Proximity Factor) + (W4 × Historical Velocity Factor)
    BR-4.2: Risk level bands.
    
    NOTE: Exact sub-formulas for factors are defined in docs/13_AI_Architecture.md
    since they depend on the specific Granite prompt/analysis design.
    For Sprint 5 (deterministic calculations only), we implement simplified versions:
    
    - Overload Factor: % of team members currently Overloaded or Critically Overloaded
    - Blocked Task Factor: % of open tasks currently Blocked, weighted by duration
    - Deadline Proximity Factor: Ratio of remaining work to remaining time
    - Historical Velocity Factor: 1.0 (placeholder for Sprint 6 AI integration)
    
    Args:
        project: Project instance
    
    Returns:
        RiskScore instance
    """
    from apps.tasks.models import Task
    from apps.accounts.models import User
    from django.utils import timezone
    from datetime import timedelta
    
    # Get project team members
    team_members = project.team.memberships.all()
    total_members = team_members.count()
    
    if total_members == 0:
        overload_factor = 0
    else:
        # Count overloaded members
        overloaded_count = 0
        for membership in team_members:
            user = membership.user
            # Get most recent workload snapshot for this user
            recent_snapshot = WorkloadSnapshot.objects.filter(
                user=user,
                project=project
            ).order_by('-computed_at').first()
            
            if recent_snapshot and recent_snapshot.status in ['overloaded', 'critically_overloaded']:
                overloaded_count += 1
        
        overload_factor = (overloaded_count / total_members) * 100 if total_members > 0 else 0
    
    # Blocked Task Factor: % of open tasks blocked, weighted by duration
    open_tasks = Task.objects.filter(
        project=project,
        status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency']
    )
    
    total_open_tasks = open_tasks.count()
    if total_open_tasks == 0:
        blocked_task_factor = 0
    else:
        blocked_tasks = open_tasks.filter(status='blocked')
        blocked_count = blocked_tasks.count()
        
        # Weight by duration blocked (simple version: count as percentage)
        blocked_task_factor = (blocked_count / total_open_tasks) * 100
    
    # Deadline Proximity Factor: ratio of remaining work to remaining time
    now = timezone.now().date()
    if project.end_date and project.end_date > now:
        remaining_days = (project.end_date - now).days
        if remaining_days > 0:
            # Remaining work: sum of estimated effort for open tasks
            remaining_work = sum(float(task.estimated_effort_hours) for task in open_tasks)

            # Simple ratio: remaining work / remaining days (normalized to 0-100)
            # This is a simplified version - full formula in AI Architecture
            deadline_proximity_factor = min((remaining_work / remaining_days) * 2, 100)
        else:
            deadline_proximity_factor = 100  # Past deadline
    else:
        deadline_proximity_factor = 100  # No deadline or past deadline
    
    # Historical Velocity Factor: placeholder for Sprint 6 AI integration
    # For now, use 1.0 (neutral)
    historical_velocity_factor = 1.0
    
    # Calculate weighted composite (BR-4.1)
    # W1 = 35%, W2 = 30%, W3 = 20%, W4 = 15%
    risk_score = (
        (0.35 * overload_factor) +
        (0.30 * blocked_task_factor) +
        (0.20 * deadline_proximity_factor) +
        (0.15 * historical_velocity_factor)
    )
    
    # Clamp to 0-100
    risk_score = max(0, min(100, risk_score))
    
    # Determine level based on BR-4.2 bands
    if risk_score <= 29:
        level = 'low'
    elif risk_score <= 59:
        level = 'moderate'
    elif risk_score <= 79:
        level = 'high'
    else:
        level = 'critical'
    
    # Generate explanation text (placeholder - full AI explanation in Sprint 6)
    explanation_text = (
        f"Risk level {level.upper()} ({risk_score:.1f}%), "
        f"driven primarily by: "
        f"Overload Factor: {overload_factor:.1f}%, "
        f"Blocked Task Factor: {blocked_task_factor:.1f}%, "
        f"Deadline Proximity Factor: {deadline_proximity_factor:.1f}%, "
        f"Historical Velocity Factor: {historical_velocity_factor:.1f}%."
    )
    
    # Create RiskScore record
    risk_score_obj = RiskScore.objects.create(
        project=project,
        score=risk_score,
        level=level,
        overload_factor=overload_factor,
        blocked_task_factor=blocked_task_factor,
        deadline_proximity_factor=deadline_proximity_factor,
        historical_velocity_factor=historical_velocity_factor,
        explanation_text=explanation_text,
    )

    # Notify PM and Executive Managers when risk reaches Critical (FR-NOTIF-004, BR-6.1)
    if level == 'critical':
        from apps.notifications.services import create_notification_service
        risk_title = "Project Risk: Critical"
        risk_message = (
            f"Project '{project.name}' has reached a Critical risk level "
            f"({risk_score:.1f}%). Immediate attention required."
        )
        # Notify PM (project owner)
        create_notification_service(
            user=project.owner,
            notification_type='risk_alert',
            title=risk_title,
            message=risk_message,
            project=project,
            task=None,
        )
        # Notify all Executive Managers (role='executive')
        executives = User.objects.filter(role='executive')
        for executive in executives:
            create_notification_service(
                user=executive,
                notification_type='risk_alert',
                title=risk_title,
                message=risk_message,
                project=project,
                task=None,
            )

    return risk_score_obj


def get_workload_history_service(user, project=None):
    """
    Get workload history for a user.
    If project specified, filter by project.
    """
    queryset = WorkloadSnapshot.objects.filter(user=user)
    if project:
        queryset = queryset.filter(project=project)
    return queryset.order_by('-computed_at')


def get_risk_history_service(project):
    """
    Get risk score history for a project.
    """
    return RiskScore.objects.filter(project=project).order_by('-computed_at')
