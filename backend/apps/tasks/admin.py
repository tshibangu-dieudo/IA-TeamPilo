"""
Admin configuration for tasks app.
"""
from django.contrib import admin
from .models import Task, TaskDependency, TaskStatusHistory


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'assignee', 'priority', 'status',
        'estimated_effort_hours', 'deadline', 'created_at', 'updated_at',
    ]
    list_filter = ['priority', 'status', 'project', 'deadline']
    search_fields = ['title', 'description', 'assignee__username', 'project__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'blocked_at', 'unassigned_since']
    date_hierarchy = 'created_at'
    raw_id_fields = ['project', 'assignee']


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = ['task', 'depends_on_task', 'created_at']
    search_fields = ['task__title', 'depends_on_task__title']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['task', 'depends_on_task']


@admin.register(TaskStatusHistory)
class TaskStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['task', 'previous_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'previous_status']
    search_fields = ['task__title', 'changed_by__username']
    readonly_fields = ['id', 'created_at', 'changed_at']
    raw_id_fields = ['task', 'changed_by']
