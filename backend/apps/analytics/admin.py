"""
Admin configuration for analytics app.
"""
from django.contrib import admin
from .models import WorkloadSnapshot, RiskScore

@admin.register(WorkloadSnapshot)
class WorkloadSnapshotAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkloadSnapshot.
    """
    list_display = ['user', 'workload_percentage', 'status', 'computed_at']
    list_filter = ['status', 'computed_at']
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['computed_at']
    date_hierarchy = 'computed_at'
    raw_id_fields = ['user']
@admin.register(RiskScore)
class RiskScoreAdmin(admin.ModelAdmin):
    """
    Admin interface for RiskScore.
    """
    list_display = ['project', 'score', 'level', 'overload_factor', 'blocked_task_factor', 'computed_at']
    list_filter = ['level', 'project', 'computed_at']
    search_fields = ['project__name']
    readonly_fields = ['computed_at', 'explanation_text']
    date_hierarchy = 'computed_at'
    raw_id_fields = ['project']
