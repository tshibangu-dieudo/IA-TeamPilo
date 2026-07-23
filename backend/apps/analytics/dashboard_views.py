"""
Dashboard aggregation views.
See docs/14_REST_API.md §11: GET /api/dashboard/summary/
See .ai/coding-rules.md: Views stay thin — call services, return response.

A single endpoint that returns all data needed for the dashboard in one
call, role-scoped per BR-7.1. This avoids 4–5 waterfalled requests on
page load and helps meet the 2-second budget (FR-DASH-002).

No new models — this is pure read aggregation from existing services.
"""
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.analytics.models import WorkloadSnapshot, RiskScore
from apps.recommendations.models import Recommendation
from apps.notifications.models import Notification
from apps.teams.models import TeamMembership


def _get_scoped_projects(user):
    """Return projects visible to this user per BR-7.1."""
    if user.role in ('executive', 'admin'):
        return Project.objects.all().select_related('owner', 'team')
    team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
    return Project.objects.filter(
        Q(owner=user) | Q(team_id__in=team_ids)
    ).distinct().select_related('owner', 'team')


def _risk_for_project(project):
    rs = (
        RiskScore.objects
        .filter(project=project)
        .order_by('-computed_at')
        .first()
    )
    if not rs:
        return None
    return {
        'score': float(rs.score),
        'level': rs.level,
        'explanation_text': rs.explanation_text[:200] if rs.explanation_text else '',
        'computed_at': rs.computed_at.isoformat(),
    }


def _workload_for_user(user, project=None):
    qs = WorkloadSnapshot.objects.filter(user=user)
    if project:
        qs = qs.filter(project=project)
    ws = qs.order_by('-computed_at').first()
    if not ws:
        return None
    return {
        'workload_percentage': float(ws.workload_percentage),
        'status': ws.status,
        'computed_at': ws.computed_at.isoformat(),
    }


class DashboardSummaryView(APIView):
    """
    GET /api/dashboard/summary/
    Role-aware aggregated dashboard payload.

    Response shape varies by role:
    - pm / admin: projects_summary, my_workload, pending_recs_count,
                  unread_notifications_count, recent_notifications
    - member:     my_tasks_summary, my_workload, unread_notifications_count
    - executive:  portfolio_risk (all projects ranked), unread_notifications_count
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = getattr(user, 'role', 'member')

        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        recent_notifications = list(
            Notification.objects
            .filter(user=user)
            .order_by('-created_at')
            .values('id', 'notification_type', 'title', 'is_read', 'created_at')
            [:5]
        )
        # Serialise UUIDs and datetimes
        for n in recent_notifications:
            n['id'] = str(n['id'])
            n['created_at'] = n['created_at'].isoformat()

        if role in ('pm', 'admin'):
            return self._pm_payload(user, unread_count, recent_notifications)
        elif role == 'executive':
            return self._executive_payload(user, unread_count, recent_notifications)
        else:
            return self._member_payload(user, unread_count, recent_notifications)

    # ---------------------------------------------------------------- PM / Admin

    def _pm_payload(self, user, unread_count, recent_notifications):
        projects = _get_scoped_projects(user)

        projects_summary = []
        for p in projects[:10]:  # cap at 10 for page-load performance
            risk = _risk_for_project(p)
            pending_recs = Recommendation.objects.filter(
                project=p, status='pending'
            ).count()
            projects_summary.append({
                'id': str(p.id),
                'name': p.name,
                'status': p.status,
                'end_date': p.end_date.isoformat(),
                'risk': risk,
                'pending_recommendations_count': pending_recs,
            })

        # Sort by risk score descending (highest risk first — doc 15 §3)
        projects_summary.sort(
            key=lambda x: float(x['risk']['score']) if x['risk'] else 0,
            reverse=True,
        )

        my_workload = _workload_for_user(user)

        # Top 3 pending recommendations across all scoped projects
        project_ids = [p.id for p in projects]
        top_recommendations = list(
            Recommendation.objects
            .filter(project_id__in=project_ids, status='pending')
            .select_related('task', 'current_assignee', 'suggested_assignee')
            .order_by('-created_at')
            [:3]
        )
        recs_data = []
        for r in top_recommendations:
            recs_data.append({
                'id': str(r.id),
                'title': r.title,
                'confidence_level': r.confidence_level if hasattr(r, 'confidence_level') else None,
                'confidence_score': r.confidence_score,
                'task_title': r.task.title if r.task else None,
                'current_assignee': r.current_assignee.username if r.current_assignee else None,
                'suggested_assignee': r.suggested_assignee.username if r.suggested_assignee else None,
                'created_at': r.created_at.isoformat(),
            })

        pending_recs_count = Recommendation.objects.filter(
            project_id__in=project_ids, status='pending'
        ).count()

        return Response({
            'role': 'pm',
            'projects_summary': projects_summary,
            'my_workload': my_workload,
            'pending_recommendations_count': pending_recs_count,
            'top_recommendations': recs_data,
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        })

    # ---------------------------------------------------------------- Executive

    def _executive_payload(self, user, unread_count, recent_notifications):
        all_projects = Project.objects.all().select_related('team')

        portfolio = []
        for p in all_projects[:20]:
            risk = _risk_for_project(p)
            portfolio.append({
                'id': str(p.id),
                'name': p.name,
                'team_name': p.team.name if p.team else None,
                'status': p.status,
                'end_date': p.end_date.isoformat(),
                'risk': risk,
            })

        # Sort by risk descending
        portfolio.sort(
            key=lambda x: float(x['risk']['score']) if x['risk'] else 0,
            reverse=True,
        )

        return Response({
            'role': 'executive',
            'portfolio': portfolio,
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        })

    # ---------------------------------------------------------------- Member

    def _member_payload(self, user, unread_count, recent_notifications):
        my_workload = _workload_for_user(user)

        my_tasks = (
            Task.objects
            .filter(assignee=user)
            .exclude(status='done')
            .select_related('project')
            .order_by('deadline')
            [:10]
        )

        by_status = {'todo': 0, 'in_progress': 0, 'blocked': 0, 'waiting_on_dependency': 0}
        tasks_data = []
        for t in my_tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            tasks_data.append({
                'id': str(t.id),
                'title': t.title,
                'status': t.status,
                'priority': t.priority,
                'deadline': t.deadline.isoformat(),
                'project_name': t.project.name,
            })

        return Response({
            'role': 'member',
            'my_workload': my_workload,
            'my_tasks_by_status': by_status,
            'my_upcoming_tasks': tasks_data,
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        })
