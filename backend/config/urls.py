"""
URL configuration for IA TeamPilot.
Generated from .ai/architecture.md specifications.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/teams/', include('apps.teams.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/chat/', include('apps.chat.urls')),
]
