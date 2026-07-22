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

from apps.projects.models import Project
from apps.analytics.models import WorkloadSnapshot, RiskScore
from apps.tasks.models import Task
from apps.recommendations.models import Recommendation
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
    Assemble a structured dict of live project/team data scoped to the user.
    This is the only data the AI chain will see (FR-CHAT-002).

    Scope rules (BR-7.1):
    - PM: sees only projects they own.
    - Executive: sees all projects (read-only).
    - Member: sees only their own tasks.
    - Admin: sees all.
    """
    snapshot = {}

    if project:
        # Single-project snapshot
        snapshot['project'] = {
            'id': str(project.id),
            'name': project.name,
            'status': project.status,
            'end_date': str(project.end_date),
        }

        # Latest risk score
        latest_risk = (
            RiskScore.objects.filter(project=project)
            .order_by('-computed_at')
            .first()
        )
        if latest_risk:
            snapshot['risk_score'] = {
                'score': float(latest_risk.score),
                'level': latest_risk.level,
                'explanation': latest_risk.explanation_text[:300] if latest_risk.explanation_text else '',
                'computed_at': str(latest_risk.computed_at),
            }

        # Team workloads
        team_workloads = []
        for membership in project.team.memberships.select_related('user').all():
            ws = (
                WorkloadSnapshot.objects.filter(user=membership.user, project=project)
                .order_by('-computed_at')
                .first()
            )
            if ws:
                team_workloads.append({
                    'name': membership.user.username,
                    'workload_pct': float(ws.workload_percentage),
                    'status': ws.status,
                })
        snapshot['team_workloads'] = team_workloads

        # Open tasks summary
        open_tasks = Task.objects.filter(
            project=project,
            status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency'],
        ).select_related('assignee')

        snapshot['open_tasks'] = [
            {
                'title': t.title,
                'status': t.status,
                'priority': t.priority,
                'assignee': t.assignee.username if t.assignee else None,
                'deadline': str(t.deadline),
            }
            for t in open_tasks[:20]  # cap at 20 to keep snapshot size sane
        ]

        # Pending recommendations
        pending_recos = Recommendation.objects.filter(
            project=project,
            status='pending',
        ).select_related('task', 'current_assignee', 'suggested_assignee')

        snapshot['pending_recommendations'] = [
            {
                'title': r.title,
                'task': r.task.title if r.task else None,
                'current_assignee': r.current_assignee.username if r.current_assignee else None,
                'suggested_assignee': r.suggested_assignee.username if r.suggested_assignee else None,
                'confidence_score': r.confidence_score,
            }
            for r in pending_recos[:10]
        ]

    else:
        # Cross-project snapshot (executive view or no project specified)
        if user.role == 'executive':
            projects_qs = Project.objects.all()
        elif user.role in ('pm', 'admin'):
            from django.db.models import Q
            from apps.teams.models import TeamMembership
            team_ids = TeamMembership.objects.filter(user=user).values_list('team_id', flat=True)
            projects_qs = Project.objects.filter(
                Q(owner=user) | Q(team_id__in=team_ids)
            ).distinct()
        else:
            # Member: only see their own tasks
            projects_qs = Project.objects.none()
            snapshot['my_tasks'] = [
                {
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'project': t.project.name,
                    'deadline': str(t.deadline),
                }
                for t in Task.objects.filter(
                    assignee=user,
                    status__in=['todo', 'in_progress', 'blocked'],
                ).select_related('project')[:20]
            ]
            return snapshot

        at_risk_projects = []
        for p in projects_qs.select_related('team')[:15]:
            latest_risk = (
                RiskScore.objects.filter(project=p)
                .order_by('-computed_at')
                .first()
            )
            at_risk_projects.append({
                'name': p.name,
                'status': p.status,
                'risk_level': latest_risk.level if latest_risk else 'unknown',
                'risk_score': float(latest_risk.score) if latest_risk else None,
            })
        snapshot['projects'] = at_risk_projects

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
    2. Assemble scoped data snapshot.
    3. Build conversation history for context.
    4. Call ai_engine.chat_service.generate_chat_response.
    5. Persist user + assistant messages.
    6. Return response dict.

    Returns:
        {
            "answer": str,
            "generated_by": str,
            "conversation_id": str,
            "conversation_title": str,
        }
    """
    from ai_engine.chat_service import generate_chat_response

    # 1. Resolve conversation
    conversation = get_or_create_conversation(user, project=project, conversation_id=conversation_id)

    # 2. Assemble data snapshot (scoped per BR-7.1)
    data_snapshot = _build_data_snapshot(user, project=project)

    # 3. Build history
    history = get_conversation_history(conversation)

    # 4. Call AI engine
    scope = f"project_id={project.id}" if project else f"user_id={user.id} (cross-project)"
    answer, generated_by = generate_chat_response(
        question=question,
        data_snapshot=data_snapshot,
        scope=scope,
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
