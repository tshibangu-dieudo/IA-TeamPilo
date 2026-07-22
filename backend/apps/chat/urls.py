"""
URL configuration for the chat app.
See docs/14_REST_API.md §10.
Mounted at /api/chat/ in config/urls.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    # POST /api/chat/query/
    path('query/', views.ChatQueryView.as_view(), name='chat_query'),

    # POST /api/chat/summary/{project_id}/
    path('summary/<uuid:project_id>/', views.ChatSummaryView.as_view(), name='chat_summary'),

    # GET /api/chat/conversations/
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),

    # GET /DELETE /api/chat/conversations/{id}/
    path('conversations/<uuid:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
]
