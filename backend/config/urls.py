"""
URL configuration for IA TeamPilot.
Generated from .ai/architecture.md specifications.
"""
from django.contrib import admin
from django.urls import path, include
from apps.tasks.views import ProjectTaskListCreateView
from apps.analytics.dashboard_views import DashboardSummaryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/teams/', include('apps.teams.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/projects/<uuid:project_id>/tasks/', ProjectTaskListCreateView.as_view(), name='project_tasks'),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
]
