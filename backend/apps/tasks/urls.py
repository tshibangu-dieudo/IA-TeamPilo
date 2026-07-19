"""
URL configuration for tasks app.
See docs/14_REST_API.md §6 for endpoint specification.

Mounted at /api/tasks/ in config/urls.py.
Project-scoped task list is also mounted at /api/projects/<project_id>/tasks/
via config/urls.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Current user's tasks — GET /api/tasks/me/
    path('me/', views.MyTasksView.as_view(), name='my_tasks'),

    # Task detail, update, delete — GET/PATCH/DELETE /api/tasks/{id}/
    path('<uuid:pk>/', views.TaskDetailView.as_view(), name='task_detail'),

    # Status update — PATCH /api/tasks/{id}/status/
    path('<uuid:pk>/status/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),

    # Dependency management
    # GET/POST /api/tasks/{id}/dependencies/
    path('<uuid:pk>/dependencies/', views.TaskDependencyListCreateView.as_view(), name='task_dependencies'),
    # DELETE /api/tasks/{id}/dependencies/{dep_id}/
    path('<uuid:pk>/dependencies/<uuid:dep_pk>/', views.TaskDependencyDeleteView.as_view(), name='task_dependency_delete'),

    # Status history — GET /api/tasks/{id}/history/
    path('<uuid:pk>/history/', views.TaskStatusHistoryView.as_view(), name='task_history'),
]
