"""
Business logic for the chat app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
See docs/13_AI_Architecture.md §3.3: Chain 3 — Chat Assistant.

Responsibilities:
1. Assemble a role-scoped data snapshot from existing services (BR-7.1).
2. Retrieve conversation history for context.
3. Call ai_engine/chat_service.py with the assembled context.
4. Persist user message + assistant response in the Conversation model.
5. Never query the DB directly inside ai_engine — only this service does that.
"""
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from apps.projects.models import Project
from apps.projects.services import get_user_projects_service
from apps.analytics.models import WorkloadSnapshot, RiskScore
from apps.tasks.models import Task
from apps.recommendations.models import Recommendation
from apps.teams.models import Team, TeamMembership
from apps.accounts.models import UserSkill
from .models import Conversation, ChatMessage


# ---------------------------------------------------------------------------
# History limit — keep the last N turns to avoid blowing the LLM context
# ---------------------------------------------------------------------------
HISTORY_TURN_LIMIT = 10  # last 10 messages (5 user + 5 assistant)


# ---------------------------------------------------------------------------
# Data snapshot assembly (BR-7.1 — scoped to what the user can see)
# ---------------------------------------------------------------------------

def _build_data_snapshot(user, project=None) -> dict:
    """
    Assemble a structured dict of live project/team/member/task data scoped to the user.
    This is the only data the AI chain will see (FR-CHAT-002).

    Scope rules (BR-7.1) - reuses get_user_projects_service():
    - Admin/Executive: sees all projects/teams/members.
    - PM: sees only projects they own and their teams.
    - Member: sees only their own tasks and team context.
    
    Snapshot structure (only includes sections with data):
    {
        "metadata": {...},          # Always present
        "organization": {...},      # Only in cross-project mode
        "projects": [...],          # Only if projects visible
        "teams": [...],             # Only if teams visible
        "members": [...],           # Only if team members visible
        "tasks": {...},             # Only if tasks visible (with summary + categorized lists)
        "analytics": {...},         # Only if risk/recommendations available
    }
    
    Limiting strategy to prevent prompt bloat:
    - Projects: 15 max (cross-project), all (single-project)
    - Members: All team members in scope (naturally limited by team size)
    - Tasks: 10 per category (blocked, overdue, high-priority)
    - Recommendations: 10 max
    """
    now = timezone.now()
    snapshot = {
        'metadata': {
            'scope': f"user_id={user.id}",
            'role': user.role,
            'generated_at': now.isoformat(),
        }
    }

    if project:
        # ========== SINGLE-PROJECT MODE ==========
        snapshot['metadata']['scope'] = f"project_id={project.id}"
        
        # Projects
        snapshot['projects'] = [{
            'id': str(project.id),
            'name': project.name,
            'status': project.status,
            'end_date': str(project.end_date),
            'owner': project.owner.username,
            'team_name': project.team.name if project.team else None,
        }]

        # Add risk score if available
        latest_risk = (
            RiskScore.objects.filter(project=project)
            .order_by('-computed_at')
            .first()
        )
        if latest_risk:
            snapshot['projects'][0]['risk_score'] = float(latest_risk.score)
            snapshot['projects'][0]['risk_level'] = latest_risk.level

        # Teams
        if project.team:
            team = project.team
            lead_membership = team.memberships.filter(role='lead').first()
            snapshot['teams'] = [{
                'id': str(team.id),
                'name': team.name,
                'description': team.description[:200] if team.description else '',
                'member_count': team.memberships.count(),
                'lead': lead_membership.user.username if lead_membership else None,
            }]

            # Members with workload and skills
            members_data = []
            for membership in team.memberships.select_related('user').all():
                member_user = membership.user
                ws = (
                    WorkloadSnapshot.objects.filter(user=member_user, project=project)
                    .order_by('-computed_at')
                    .first()
                )
                member_data = {
                    'name': member_user.username,
                    'role': membership.role,
                }
                if ws:
                    member_data.update({
                        'workload_pct': float(ws.workload_percentage),
                        'workload_status': ws.status,
                    })
                
                # Add skills
                member_skills = UserSkill.objects.filter(user=member_user)[:10]
                if member_skills.exists():
                    member_data['skills'] = [
                        {
                            'name': us.skill_name,
                            'proficiency': us.proficiency_level,
                        }
                        for us in member_skills
                    ]
                
                members_data.append(member_data)
            
            if members_data:
                snapshot['members'] = members_data

        # Tasks (categorized and limited)
        all_open_tasks = Task.objects.filter(
            project=project,
            status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency'],
        ).select_related('assignee')

        # Task counts by status (for progress analysis) - ADDED PER APPROVAL
        all_tasks = Task.objects.filter(project=project)
        task_counts = {
            'todo': all_tasks.filter(status='todo').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'blocked': all_tasks.filter(status='blocked').count(),
            'done': all_tasks.filter(status='done').count(),
            'total_open': all_open_tasks.count(),
        }

        # Blocked tasks (top 10)
        blocked_tasks = all_open_tasks.filter(status='blocked')[:10]
        blocked_data = []
        for t in blocked_tasks:
            days_blocked = (now.date() - t.updated_at.date()).days if t.updated_at else 0
            blocked_data.append({
                'title': t.title,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'blocked_reason': t.blocked_reason or 'No reason specified',
                'days_blocked': days_blocked,
                'project': project.name,
            })

        # Overdue tasks (top 10)
        overdue_tasks = all_open_tasks.filter(deadline__lt=now.date())[:10]
        overdue_data = []
        for t in overdue_tasks:
            days_overdue = (now.date() - t.deadline).days
            overdue_data.append({
                'title': t.title,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'deadline': str(t.deadline),
                'days_overdue': days_overdue,
                'project': project.name,
            })

        # High priority tasks (top 10)
        high_priority_tasks = all_open_tasks.filter(priority__in=['critical', 'high'])[:10]
        high_priority_data = []
        for t in high_priority_tasks:
            high_priority_data.append({
                'title': t.title,
                'priority': t.priority,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'status': t.status,
                'project': project.name,
            })

        # Only include tasks section if there's actual data
        if task_counts['total_open'] > 0 or task_counts['done'] > 0:
            tasks_section = {'summary': task_counts}
            if blocked_data:
                tasks_section['blocked'] = blocked_data
            if overdue_data:
                tasks_section['overdue'] = overdue_data
            if high_priority_data:
                tasks_section['high_priority'] = high_priority_data
            snapshot['tasks'] = tasks_section

        # Analytics: pending recommendations
        pending_recos = Recommendation.objects.filter(
            project=project,
            status='pending',
        ).select_related('task', 'current_assignee', 'suggested_assignee')[:10]

        if pending_recos.exists():
            recommendations_data = []
            for r in pending_recos:
                recommendations_data.append({
                    'title': r.title,
                    'task': r.task.title if r.task else None,
                    'current_assignee': r.current_assignee.username if r.current_assignee else None,
                    'suggested_assignee': r.suggested_assignee.username if r.suggested_assignee else None,
                    'confidence_score': r.confidence_score,
                    'reason': r.explanation[:200] if r.explanation else '',
                })
            
            snapshot['analytics'] = {'recommendations': recommendations_data}
            
            # Add risk score to analytics if available
            if latest_risk:
                if 'analytics' not in snapshot:
                    snapshot['analytics'] = {}
                snapshot['analytics']['risk_score'] = {
                    'score': float(latest_risk.score),
                    'level': latest_risk.level,
                    'explanation': latest_risk.explanation_text[:300] if latest_risk.explanation_text else '',
                    'overload_factor': float(latest_risk.overload_factor),
                    'blocked_task_factor': float(latest_risk.blocked_task_factor),
                    'deadline_proximity_factor': float(latest_risk.deadline_proximity_factor),
                }

    else:
        # ========== CROSS-PROJECT MODE ==========
        snapshot['metadata']['scope'] = f"user_id={user.id} (cross-project)"
        
        # Use proven scoping logic from projects.services
        projects_qs = get_user_projects_service(user)

        # Organization summary (only for admin/executive/PM in cross-project mode)
        if user.role in ['admin', 'executive', 'pm']:
            total_projects = projects_qs.count()
            active_projects = projects_qs.filter(status='active').count()
            
            # Get teams visible to this user
            if user.role in ['admin', 'executive']:
                visible_teams = Team.objects.all()
                # Count unique users across all team memberships
                visible_members = TeamMembership.objects.values('user').distinct().count()
            else:
                team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
                visible_teams = Team.objects.filter(id__in=team_ids)
                visible_members = TeamMembership.objects.filter(team_id__in=team_ids).values('user').distinct().count()
            
            snapshot['organization'] = {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'total_teams': visible_teams.count(),
                'total_members': visible_members,
            }

        # Member-specific snapshot (only their tasks)
        if user.role == 'member':
            my_tasks = Task.objects.filter(
                assignee=user,
                status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency'],
            ).select_related('project')[:20]
            
            if my_tasks.exists():
                tasks_data = {
                    'my_tasks': []
                }
                for t in my_tasks:
                    tasks_data['my_tasks'].append({
                        'title': t.title,
                        'status': t.status,
                        'priority': t.priority,
                        'project': t.project.name,
                        'deadline': str(t.deadline),
                    })
                snapshot['tasks'] = tasks_data
            
            # Add member's own info with workload
            ws = WorkloadSnapshot.objects.filter(user=user).order_by('-computed_at').first()
            member_data = {
                'name': user.username,
                'role': user.role,
            }
            if ws:
                member_data.update({
                    'workload_pct': float(ws.workload_percentage),
                    'workload_status': ws.status,
                })
            
            # Add user's skills
            user_skills = UserSkill.objects.filter(user=user)[:10]
            if user_skills.exists():
                member_data['skills'] = [
                    {
                        'name': us.skill_name,
                        'proficiency': us.proficiency_level,
                    }
                    for us in user_skills
                ]
            
            snapshot['members'] = [member_data]
            return snapshot

        # Projects with risk (limited to 15 for cross-project)
        projects_data = []
        for p in projects_qs.select_related('team', 'owner')[:15]:
            latest_risk = (
                RiskScore.objects.filter(project=p)
                .order_by('-computed_at')
                .first()
            )
            project_data = {
                'id': str(p.id),
                'name': p.name,
                'status': p.status,
                'owner': p.owner.username,
                'team_name': p.team.name if p.team else None,
            }
            if latest_risk:
                project_data.update({
                    'risk_level': latest_risk.level,
                    'risk_score': float(latest_risk.score),
                })
            projects_data.append(project_data)
        
        if projects_data:
            snapshot['projects'] = projects_data

        # Teams summary (for PM/admin/executive)
        if user.role in ['admin', 'executive']:
            teams_qs = Team.objects.all()
        else:
            team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
            teams_qs = Team.objects.filter(id__in=team_ids)
        
        teams_data = []
        for team in teams_qs[:10]:  # Limit to 10 teams
            lead_membership = team.memberships.filter(role='lead').first()
            teams_data.append({
                'id': str(team.id),
                'name': team.name,
                'member_count': team.memberships.count(),
                'lead': lead_membership.user.username if lead_membership else None,
            })
        
        if teams_data:
            snapshot['teams'] = teams_data

        # Members with workload (for PM/admin/executive cross-project)
        # Get all team members visible to this user with their workload
        if user.role in ['admin', 'executive']:
            team_memberships = TeamMembership.objects.select_related('user', 'team').all()[:50]  # Limit to 50 members
        else:
            # PM: only members of teams they're part of
            team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
            team_memberships = TeamMembership.objects.filter(team_id__in=team_ids).select_related('user', 'team')[:50]
        
        members_data = []
        for membership in team_memberships:
            member_user = membership.user
            # Get latest workload across all projects
            ws = WorkloadSnapshot.objects.filter(user=member_user).order_by('-computed_at').first()
            member_data = {
                'name': member_user.username,
                'role': membership.role,
                'team': membership.team.name,
            }
            if ws:
                member_data.update({
                    'workload_pct': float(ws.workload_percentage),
                    'workload_status': ws.status,
                })
            
            # Add skills
            member_skills = UserSkill.objects.filter(user=member_user)[:5]  # Limit to 5 skills per member
            if member_skills.exists():
                member_data['skills'] = [
                    {
                        'name': us.skill_name,
                        'proficiency': us.proficiency_level,
                    }
                    for us in member_skills
                ]
            
            members_data.append(member_data)
        
        if members_data:
            snapshot['members'] = members_data

        # Tasks (categorized, cross-project)
        # Get all open tasks visible to this user
        all_open_tasks = Task.objects.filter(
            project__in=projects_qs,
            status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency'],
        ).select_related('assignee', 'project')

        # Task counts by status
        all_tasks = Task.objects.filter(project__in=projects_qs)
        task_counts = {
            'todo': all_tasks.filter(status='todo').count(),
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'blocked': all_tasks.filter(status='blocked').count(),
            'done': all_tasks.filter(status='done').count(),
            'total_open': all_open_tasks.count(),
        }

        # Blocked tasks (top 10 across all projects)
        blocked_tasks = all_open_tasks.filter(status='blocked')[:10]
        blocked_data = []
        for t in blocked_tasks:
            days_blocked = (now.date() - t.updated_at.date()).days if t.updated_at else 0
            blocked_data.append({
                'title': t.title,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'blocked_reason': t.blocked_reason or 'No reason specified',
                'days_blocked': days_blocked,
                'project': t.project.name,
            })

        # Overdue tasks (top 10 across all projects)
        overdue_tasks = all_open_tasks.filter(deadline__lt=now.date())[:10]
        overdue_data = []
        for t in overdue_tasks:
            days_overdue = (now.date() - t.deadline).days
            overdue_data.append({
                'title': t.title,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'deadline': str(t.deadline),
                'days_overdue': days_overdue,
                'project': t.project.name,
            })

        # High priority tasks (top 10 across all projects)
        high_priority_tasks = all_open_tasks.filter(priority__in=['critical', 'high'])[:10]
        high_priority_data = []
        for t in high_priority_tasks:
            high_priority_data.append({
                'title': t.title,
                'priority': t.priority,
                'assignee': t.assignee.username if t.assignee else 'Unassigned',
                'status': t.status,
                'project': t.project.name,
            })

        # Only include tasks section if there's actual data
        if task_counts['total_open'] > 0 or task_counts['done'] > 0:
            tasks_section = {'summary': task_counts}
            if blocked_data:
                tasks_section['blocked'] = blocked_data
            if overdue_data:
                tasks_section['overdue'] = overdue_data
            if high_priority_data:
                tasks_section['high_priority'] = high_priority_data
            snapshot['tasks'] = tasks_section

    return snapshot


# ---------------------------------------------------------------------------
# Conversation management
# ---------------------------------------------------------------------------

def get_or_create_conversation(user, project=None, conversation_id=None) -> Conversation:
    """
    Return an existing conversation (owned by user) or create a new one.
    Scope violation on conversation_id → returns a new conversation (404
    semantics are enforced at the view layer).
    """
    if conversation_id:
        try:
            return Conversation.objects.get(id=conversation_id, user=user)
        except Conversation.DoesNotExist:
            pass  # fall through to create new

    return Conversation.objects.create(
        user=user,
        project=project,
        title='',  # filled on first message
    )


def get_conversation_history(conversation: Conversation) -> list:
    """Return the last HISTORY_TURN_LIMIT messages as dicts for the LLM context."""
    # Evaluate to a plain list first — Django querysets don't support negative slicing
    all_messages = list(
        conversation.messages
        .order_by('created_at')
        .values('role', 'content')
    )
    return all_messages[-HISTORY_TURN_LIMIT:]


def _derive_title(question: str) -> str:
    """Derive a short conversation title from the first user message."""
    title = question.strip()
    if len(title) > 80:
        title = title[:77] + '…'
    return title


# ---------------------------------------------------------------------------
# Main service — called by views
# ---------------------------------------------------------------------------

def process_chat_query(user, question: str, project=None, conversation_id=None) -> dict:
    """
    Full chat query pipeline:
    1. Resolve/create conversation.
    2. Classify intent to determine routing.
    3. Assemble scoped data snapshot (only for TEAMPILOT_DATA mode).
    4. Build conversation history for context.
    5. Call ai_engine.router.route_chat_request with pre-classified intent.
    6. Persist user + assistant messages.
    7. Return response dict.

    Returns:
        {
            "answer": str,
            "generated_by": str,
            "conversation_id": str,
            "conversation_title": str,
        }
    """
    from ai_engine.intent_classifier import classify_intent
    from ai_engine.router import route_chat_request

    # 1. Resolve conversation
    conversation = get_or_create_conversation(user, project=project, conversation_id=conversation_id)

    # 2. Classify intent (approach a: classify once in services.py)
    intent, confidence = classify_intent(question)

    # 3. Build history
    history = get_conversation_history(conversation)

    # 4. Route based on intent
    if intent == "TEAMPILOT_DATA":
        # Build data snapshot for TeamPilot data mode
        data_snapshot = _build_data_snapshot(user, project=project)
        scope = f"project_id={project.id}" if project else f"user_id={user.id} (cross-project)"
        
        answer, generated_by, final_intent = route_chat_request(
            question=question,
            intent=intent,
            data_snapshot=data_snapshot,
            scope=scope,
            conversation_history=history,
        )
    else:
        # General knowledge mode - no snapshot needed
        answer, generated_by, final_intent = route_chat_request(
            question=question,
            intent=intent,
            conversation_history=history,
        )

    # 5. Persist messages
    ChatMessage.objects.create(
        conversation=conversation,
        user=user,
        project=project,
        role='user',
        content=question,
    )
    ChatMessage.objects.create(
        conversation=conversation,
        user=user,
        project=project,
        role='assistant',
        content=answer,
        generated_by=generated_by,
    )

    # Set conversation title from first user message
    if not conversation.title:
        conversation.title = _derive_title(question)
        conversation.save(update_fields=['title', 'updated_at'])
    else:
        # Touch updated_at so the conversation floats to the top of the list
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

    return {
        'answer': answer,
        'generated_by': generated_by,
        'conversation_id': str(conversation.id),
        'conversation_title': conversation.title,
    }


def process_executive_summary(user, project) -> dict:
    """
    Generate an executive summary for a project (FR-CHAT-003).
    Uses the same Chain 3 but with a summary-specific question.

    Returns:
        {
            "answer": str,
            "generated_by": str,
            "conversation_id": str,
        }
    """
    question = (
        f"Provide a concise executive summary of the project '{project.name}': "
        f"current risk level, team workload status, any blocked tasks, "
        f"and top pending recommendations."
    )
    return process_chat_query(user, question, project=project)
