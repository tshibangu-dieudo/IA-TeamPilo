"""
Admin configuration for projects app.
"""
from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date', 'owner', 'team', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'start_date', 'end_date']
    search_fields = ['name', 'description', 'owner__username', 'owner__email', 'team__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
