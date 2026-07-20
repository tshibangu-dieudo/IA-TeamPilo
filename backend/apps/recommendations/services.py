"""
Business logic for recommendations app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
Recommendation trigger and ranking logic will be implemented here.
"""
from datetime import date
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import User, UserSkill
from apps.projects.models import Project
from apps.tasks.models import Task, TaskStatusHistory, TaskSkill
from apps.analytics.services import calculate_workload_service
from apps.notifications.models import Notification
from ai_engine.recommendation_service import generate_recommendation_justification
from .models import Recommendation


def calculate_sprint_weeks(project):
    """Calculate project duration in weeks (as sprint length)."""
    sprint_length_days = (project.end_date - project.start_date).days
    return max(sprint_length_days / 7, 1)


def get_candidate_matching_skills(task, candidate_user):
    """
    Get matching skills between a task and a candidate user.
    Returns (matching_skills_list, required_skills_list)
    """
    required_skills = [ts.skill.name for ts in task.required_skills.select_related('skill')]
    candidate_skills = [us.skill_name for us in candidate_user.skills.all()]
    
    required_skills_lower = [s.lower() for s in required_skills]
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    matching_skills = [
        req for req in required_skills
        if req.lower() in candidate_skills_lower
    ]
    return matching_skills, required_skills


def rank_reassignment_candidates(task, team_members, project, sprint_start, sprint_end):
    """
    Rank candidates for task reassignment per BR-5.3:
    1. Highest skill match score.
    2. Lowest current workload %.
    3. Fewest currently blocked tasks.
    
    Returns a list of candidate dicts:
        { 'user': User, 'matching_skills': [...], 'workload_pct': float, 'blocked_tasks_count': int }
    """
    candidates = []
    
    for membership in team_members:
        candidate_user = membership.user
        
        # Candidate cannot be the current task assignee
        if task.assignee and candidate_user.id == task.assignee.id:
            continue
            
        # Candidate must not be overloaded or critically overloaded (workload < 100%)
        workload_pct, status = calculate_workload_service(
            candidate_user, project, sprint_start, sprint_end
        )
        if workload_pct >= 100:
            continue
            
        # Check skill match (BR-5.2/BR-5.1)
        matching_skills, required_skills = get_candidate_matching_skills(task, candidate_user)
        
        # If task requires skills, candidate must have at least one match
        if required_skills and not matching_skills:
            continue
            
        # Count blocked tasks for the candidate
        blocked_tasks_count = Task.objects.filter(
            assignee=candidate_user,
            project=project,
            status='blocked'
        ).count()
        
        candidates.append({
            'user': candidate_user,
            'matching_skills': matching_skills,
            'required_skills_count': len(required_skills),
            'workload_pct': workload_pct,
            'blocked_tasks_count': blocked_tasks_count
        })
        
    # Sort candidates: highest skill matches first, lowest workload second, fewest blocked third
    candidates.sort(key=lambda c: (
        -len(c['matching_skills']),
        c['workload_pct'],
        c['blocked_tasks_count']
    ))
    
    return candidates


def determine_confidence_level(matching_skills_count, required_skills_count, post_workload_pct):
    """
    Determine confidence scoring per BR-5.4:
    - High: exact skill match, workload < 80% after reassignment.
    - Medium: partial match, workload < 100% after reassignment.
    - Low: otherwise.
    
    Returns (score, priority)
    """
    is_exact = required_skills_count > 0 and matching_skills_count == required_skills_count
    is_partial = matching_skills_count > 0
    
    if (required_skills_count == 0 or is_exact) and post_workload_pct < 80:
        return 90, 'low'  # HIGH confidence, priority Low (stable reassignment)
    elif is_partial and post_workload_pct < 100:
        return 70, 'medium'  # MEDIUM confidence, priority Medium
    else:
        return 40, 'high'  # LOW confidence, priority High (caveat/alert needed)


def create_recommendation_and_notify(project, task, current_assignee, suggested_assignee, 
                                     recommendation_type, title, description, confidence_score, priority,
                                     overloaded_user_name, overloaded_workload, candidate_name, candidate_workload,
                                     candidate_skills, task_title, task_hours, task_deadline, candidate_rank_reason):
    """Helper to call AI engine, save recommendation, and send PM notification."""
    # Check if a pending or active recommendation already exists to avoid duplicates
    duplicate_exists = Recommendation.objects.filter(
        project=project,
        task=task,
        suggested_assignee=suggested_assignee,
        status__in=['pending', 'accepted']
    ).exists()
    
    if duplicate_exists:
        return None

    # Construct input context for AI Engine Justification
    input_context = {
        "overloaded_user": {
            "name": overloaded_user_name,
            "workload_pct": int(overloaded_workload),
            "role": getattr(current_assignee, 'role', 'Developer') if current_assignee else 'Developer'
        },
        "candidate": {
            "name": candidate_name,
            "workload_pct": int(candidate_workload),
            "matching_skills": candidate_skills
        },
        "task": {
            "title": task_title,
            "estimated_hours": float(task_hours),
            "deadline": str(task_deadline)
        },
        "rule_context": {
            "candidate_rank_reason": candidate_rank_reason,
            "confidence_tier": "HIGH" if confidence_score >= 80 else ("MEDIUM" if confidence_score >= 60 else "LOW")
        }
    }
    
    explanation, generated_by = generate_recommendation_justification(input_context)
    
    # Save the recommendation
    recommendation = Recommendation.objects.create(
        project=project,
        task=task,
        current_assignee=current_assignee,
        suggested_assignee=suggested_assignee,
        recommendation_type=recommendation_type,
        title=title,
        description=description,
        explanation=explanation,
        confidence_score=confidence_score,
        priority=priority,
        generated_by=generated_by,
        status='pending'
    )
    
    # Notify PM in-app (FR-NOTIF-002)
    Notification.objects.create(
        user=project.owner,
        notification_type='recommendation',
        title='New Recommendation Generated',
        message=f"New recommendation generated for project '{project.name}': {title}",
        project=project,
        task=task
    )
    
    return recommendation


def generate_recommendations_for_project_service(project):
    """
    Generate recommendations for a project based on workload, blocks, overdue dates, etc.
    """
    recommendations_generated = []
    
    sprint_start = project.start_date
    sprint_end = project.end_date
    sprint_weeks = calculate_sprint_weeks(project)
    
    team_members = project.team.memberships.all()
    open_tasks = Task.objects.filter(
        project=project,
        status__in=['todo', 'in_progress', 'blocked', 'waiting_on_dependency']
    )
    
    # Cache user workloads to prevent multiple calculations
    user_workloads = {}
    for member in team_members:
        u = member.user
        wl_pct, status = calculate_workload_service(u, project, sprint_start, sprint_end)
        user_workloads[u.id] = {
            'user': u,
            'workload_pct': wl_pct,
            'status': status
        }
        
    # Trigger 1 & 6: Overloaded members / Workload Imbalance
    for u_id, wl_data in user_workloads.items():
        if wl_data['status'] in ['overloaded', 'critically_overloaded']:
            overloaded_user = wl_data['user']
            overloaded_tasks = open_tasks.filter(assignee=overloaded_user)
            
            for task in overloaded_tasks:
                candidates = rank_reassignment_candidates(
                    task, team_members, project, sprint_start, sprint_end
                )
                
                if not candidates:
                    # BR-5.2: Skill gap alert when no candidate can take the task
                    Notification.objects.create(
                        user=project.owner,
                        notification_type='overload_alert',
                        title='Skill Gap Alert',
                        message=f"No matching skill candidate is available to offload task '{task.title}' from overloaded user {overloaded_user.username}.",
                        project=project,
                        task=task
                    )
                    continue
                    
                # Take top candidate
                best_cand = candidates[0]
                best_user = best_cand['user']
                
                # Calculate post workload
                capacity = getattr(best_user, 'weekly_capacity_hours', 40) or 40
                increment = (float(task.estimated_effort_hours) / float(capacity * sprint_weeks)) * 100
                post_wl = best_cand['workload_pct'] + increment
                
                score, priority = determine_confidence_level(
                    len(best_cand['matching_skills']),
                    best_cand['required_skills_count'],
                    post_wl
                )
                
                reco = create_recommendation_and_notify(
                    project=project,
                    task=task,
                    current_assignee=overloaded_user,
                    suggested_assignee=best_user,
                    recommendation_type='overloaded_member',
                    title=f"Offload Task to Resolve Overload ({overloaded_user.username})",
                    description=f"Reassign task '{task.title}' to {best_user.username} to reduce {overloaded_user.username}'s overload.",
                    confidence_score=score,
                    priority=priority,
                    overloaded_user_name=overloaded_user.username,
                    overloaded_workload=wl_data['workload_pct'],
                    candidate_name=best_user.username,
                    candidate_workload=best_cand['workload_pct'],
                    candidate_skills=best_cand['matching_skills'],
                    task_title=task.title,
                    task_hours=task.estimated_effort_hours,
                    task_deadline=task.deadline,
                    candidate_rank_reason=f"lowest workload ({best_cand['workload_pct']:.0f}%) and skill match"
                )
                if reco:
                    recommendations_generated.append(reco)

    # Trigger 2: Idle / Unassigned members
    # Find unassigned tasks
    unassigned_tasks = open_tasks.filter(assignee__isnull=True)
    for task in unassigned_tasks:
        candidates = rank_reassignment_candidates(
            task, team_members, project, sprint_start, sprint_end
        )
        if candidates:
            best_cand = candidates[0]
            best_user = best_cand['user']
            
            capacity = getattr(best_user, 'weekly_capacity_hours', 40) or 40
            increment = (float(task.estimated_effort_hours) / float(capacity * sprint_weeks)) * 100
            post_wl = best_cand['workload_pct'] + increment
            
            score, priority = determine_confidence_level(
                len(best_cand['matching_skills']),
                best_cand['required_skills_count'],
                post_wl
            )
            
            reco = create_recommendation_and_notify(
                project=project,
                task=task,
                current_assignee=None,
                suggested_assignee=best_user,
                recommendation_type='idle_member',
                title=f"Assign Unassigned Task ({task.title})",
                description=f"Assign unassigned task '{task.title}' to {best_user.username} who has available capacity.",
                confidence_score=score,
                priority=priority,
                overloaded_user_name="None (Unassigned)",
                overloaded_workload=0,
                candidate_name=best_user.username,
                candidate_workload=best_cand['workload_pct'],
                candidate_skills=best_cand['matching_skills'],
                task_title=task.title,
                task_hours=task.estimated_effort_hours,
                task_deadline=task.deadline,
                candidate_rank_reason="available workload capacity and skill alignment"
            )
            if reco:
                recommendations_generated.append(reco)

    # Trigger 3: Blocked Tasks
    blocked_tasks = open_tasks.filter(status='blocked')
    for task in blocked_tasks:
        # Suggest reassignment if it has assignee
        if task.assignee:
            candidates = rank_reassignment_candidates(
                task, team_members, project, sprint_start, sprint_end
            )
            if candidates:
                best_cand = candidates[0]
                best_user = best_cand['user']
                
                capacity = getattr(best_user, 'weekly_capacity_hours', 40) or 40
                increment = (float(task.estimated_effort_hours) / float(capacity * sprint_weeks)) * 100
                post_wl = best_cand['workload_pct'] + increment
                
                score, priority = determine_confidence_level(
                    len(best_cand['matching_skills']),
                    best_cand['required_skills_count'],
                    post_wl
                )
                
                reco = create_recommendation_and_notify(
                    project=project,
                    task=task,
                    current_assignee=task.assignee,
                    suggested_assignee=best_user,
                    recommendation_type='blocked_task',
                    title=f"Reassign Blocked Task to Unblock Work ({task.title})",
                    description=f"Reassign blocked task '{task.title}' from {task.assignee.username} to {best_user.username} to bypass blockers.",
                    confidence_score=score,
                    priority=priority,
                    overloaded_user_name=task.assignee.username,
                    overloaded_workload=user_workloads.get(task.assignee.id, {}).get('workload_pct', 0),
                    candidate_name=best_user.username,
                    candidate_workload=best_cand['workload_pct'],
                    candidate_skills=best_cand['matching_skills'],
                    task_title=task.title,
                    task_hours=task.estimated_effort_hours,
                    task_deadline=task.deadline,
                    candidate_rank_reason="capacity to support blocked task and skill match"
                )
                if reco:
                    recommendations_generated.append(reco)

    # Trigger 5: Overdue Tasks
    overdue_tasks = open_tasks.filter(deadline__lt=date.today())
    for task in overdue_tasks:
        candidates = rank_reassignment_candidates(
            task, team_members, project, sprint_start, sprint_end
        )
        if candidates:
            best_cand = candidates[0]
            best_user = best_cand['user']
            
            capacity = getattr(best_user, 'weekly_capacity_hours', 40) or 40
            increment = (float(task.estimated_effort_hours) / float(capacity * sprint_weeks)) * 100
            post_wl = best_cand['workload_pct'] + increment
            
            score, priority = determine_confidence_level(
                len(best_cand['matching_skills']),
                best_cand['required_skills_count'],
                post_wl
            )
            
            reco = create_recommendation_and_notify(
                project=project,
                task=task,
                current_assignee=task.assignee,
                suggested_assignee=best_user,
                recommendation_type='overdue_task',
                title=f"Reassign Overdue Task ({task.title})",
                description=f"Reassign overdue task '{task.title}' to {best_user.username} to speed up delivery.",
                confidence_score=score,
                priority=priority,
                overloaded_user_name=task.assignee.username if task.assignee else "None (Unassigned)",
                overloaded_workload=user_workloads.get(task.assignee.id, {}).get('workload_pct', 0) if task.assignee else 0,
                candidate_name=best_user.username,
                candidate_workload=best_cand['workload_pct'],
                candidate_skills=best_cand['matching_skills'],
                task_title=task.title,
                task_hours=task.estimated_effort_hours,
                task_deadline=task.deadline,
                candidate_rank_reason="lowest workload capacity to prioritize overdue work"
            )
            if reco:
                recommendations_generated.append(reco)

    # Trigger 7: Deadline conflicts
    # Check if any user has tasks due on the same day causing overloading overlap
    for u_id, wl_data in user_workloads.items():
        member_user = wl_data['user']
        member_tasks = open_tasks.filter(assignee=member_user)
        
        # Group tasks by due date
        by_date = {}
        for t in member_tasks:
            by_date.setdefault(t.deadline, []).append(t)
            
        for deadline, tasks_on_day in by_date.items():
            if len(tasks_on_day) > 1:
                # Sum effort due on that day
                total_day_effort = sum(t.estimated_effort_hours for t in tasks_on_day)
                # Let's say if it exceeds 8 hours (daily limit)
                if total_day_effort > 8:
                    # Select the task with lower priority or lower effort to reassign
                    conflict_task = min(tasks_on_day, key=lambda t: t.estimated_effort_hours)
                    
                    candidates = rank_reassignment_candidates(
                        conflict_task, team_members, project, sprint_start, sprint_end
                    )
                    if candidates:
                        best_cand = candidates[0]
                        best_user = best_cand['user']
                        
                        capacity = getattr(best_user, 'weekly_capacity_hours', 40) or 40
                        increment = (float(conflict_task.estimated_effort_hours) / float(capacity * sprint_weeks)) * 100
                        post_wl = best_cand['workload_pct'] + increment
                        
                        score, priority = determine_confidence_level(
                            len(best_cand['matching_skills']),
                            best_cand['required_skills_count'],
                            post_wl
                        )
                        
                        reco = create_recommendation_and_notify(
                            project=project,
                            task=conflict_task,
                            current_assignee=member_user,
                            suggested_assignee=best_user,
                            recommendation_type='deadline_conflict',
                            title=f"Resolve Deadline Conflict ({member_user.username})",
                            description=(
                                f"Reassign task '{conflict_task.title}' to {best_user.username} "
                                f"to resolve deadline overlap on {deadline}."
                            ),
                            confidence_score=score,
                            priority=priority,
                            overloaded_user_name=member_user.username,
                            overloaded_workload=wl_data['workload_pct'],
                            candidate_name=best_user.username,
                            candidate_workload=best_cand['workload_pct'],
                            candidate_skills=best_cand['matching_skills'],
                            task_title=conflict_task.title,
                            task_hours=conflict_task.estimated_effort_hours,
                            task_deadline=conflict_task.deadline,
                            candidate_rank_reason="skills matching and workload availability to resolve date conflict"
                        )
                        if reco:
                            recommendations_generated.append(reco)

    # Trigger 4: High-Risk Projects
    from apps.analytics.models import RiskScore
    recent_risk = RiskScore.objects.filter(project=project).order_by('-computed_at').first()
    if recent_risk and recent_risk.score >= 60:  # High or Critical
        reco = create_recommendation_and_notify(
            project=project,
            task=None,
            current_assignee=None,
            suggested_assignee=None,
            recommendation_type='high_risk_project',
            title="High Project Risk Alert",
            description=(
                f"The project risk level is currently high ({recent_risk.score:.1f}%). "
                "Review pending reassignments and unblock tasks immediately."
            ),
            confidence_score=50,  # general alert level
            priority='critical' if recent_risk.level == 'critical' else 'high',
            overloaded_user_name="Project Team",
            overloaded_workload=100,
            candidate_name="Manager Review",
            candidate_workload=0,
            candidate_skills=[],
            task_title="Entire Project",
            task_hours=0,
            task_deadline=project.deadline,
            candidate_rank_reason="escalated project-wide risk indices"
        )
        if reco:
            recommendations_generated.append(reco)

    return recommendations_generated


def accept_recommendation_service(recommendation, user):
    """
    Accept recommendation:
    1. Set status to accepted.
    2. Apply the reassignment (update task.assignee).
    3. Update task status from blocked/waiting if necessary.
    4. Log TaskStatusHistory and create notification for user.
    """
    if recommendation.status != 'pending':
        raise ValueError("Only pending recommendations can be accepted.")
        
    with transaction.atomic():
        recommendation.status = 'accepted'
        recommendation.accepted_by = user
        recommendation.accepted_at = timezone.now()
        recommendation.save()
        
        # Apply task reassignment if linked
        task = recommendation.task
        suggested = recommendation.suggested_assignee
        
        if task and suggested:
            old_assignee = task.assignee
            task.assignee = suggested
            
            # Reset unassigned tracker
            if task.unassigned_since:
                task.unassigned_since = None
                
            # If status is blocked or waiting_on_dependency, we can let it be or update it
            old_status = task.status
            task.save()
            
            # Log task status history
            TaskStatusHistory.objects.create(
                task=task,
                changed_by=user,
                previous_status=old_status,
                new_status=task.status
            )
            
            # Notify new assignee (FR-NOTIF-001)
            Notification.objects.create(
                user=suggested,
                notification_type='task_reassigned',
                title='New Task Assigned',
                message=f"Task '{task.title}' has been reassigned to you from {old_assignee.username if old_assignee else 'Unassigned'}.",
                project=recommendation.project,
                task=task
            )
            
    return recommendation


def dismiss_recommendation_service(recommendation, user=None):
    """
    Dismiss recommendation: set status to dismissed.
    """
    if recommendation.status != 'pending':
        raise ValueError("Only pending recommendations can be dismissed.")
        
    recommendation.status = 'dismissed'
    recommendation.dismissed_at = timezone.now()
    if user:
        recommendation.accepted_by = user  # Store who dismissed it in accepted_by
    recommendation.save()
    
    return recommendation
