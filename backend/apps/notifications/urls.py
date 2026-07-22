"""
URL configuration for notifications app.
See docs/14_REST_API.md §9.

Mounted at /api/notifications/ in config/urls.py.

IMPORTANT: read-all must be declared BEFORE <uuid:pk>/read/ so Django
matches the literal 'read-all' path before treating it as a UUID.
"""
from django.urls import path
from . import views

urlpatterns = [
    # GET  /api/notifications/
    path('', views.NotificationListView.as_view(), name='notification_list'),

    # PATCH /api/notifications/read-all/
    # Must come before the {pk}/read/ pattern
    path('read-all/', views.NotificationMarkAllReadView.as_view(), name='notification_read_all'),

    # PATCH /api/notifications/{id}/read/
    path('<uuid:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_read'),
]
