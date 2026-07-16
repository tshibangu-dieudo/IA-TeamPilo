from django.contrib import admin
from .models import Task, TaskDependency, TaskStatusHistory


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['priority', 'status', 'project']


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = ['task', 'depends_on', 'created_at']


@admin.register(TaskStatusHistory)
class TaskStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['task', 'old_status', 'new_status', 'changed_by', 'created_at']
