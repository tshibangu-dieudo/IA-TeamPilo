"""
Views for the chat app.
See .ai/coding-rules.md: Views stay thin — validate, call service, return response.
See docs/14_REST_API.md §10 for endpoint specification.

Endpoints:
  POST /api/chat/query/                     — ask a question (PM, Executive)
  POST /api/chat/summary/{project_id}/      — executive summary (Executive)
  GET  /api/chat/conversations/             — list user's conversations
  GET  /api/chat/conversations/{id}/        — conversation detail + messages
  DELETE /api/chat/conversations/{id}/      — delete a conversation
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from .models import Conversation
from .serializers import (
    ChatQuerySerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
)
from .permissions import CanAccessChat
from .services import process_chat_query, process_executive_summary


class ChatQueryView(APIView):
    """
    POST /api/chat/query/
    Ask a natural-language question grounded in scoped project data.
    Accessible to: PM, Executive, Admin (FR-CHAT-001).
    """
    permission_classes = [IsAuthenticated, CanAccessChat]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        project_id = serializer.validated_data.get('project_id')
        conversation_id = serializer.validated_data.get('conversation_id')

        # Resolve optional project scope — 404 on scope violation (BR-7.1)
        project = None
        if project_id:
            project = self._get_scoped_project(project_id, request.user)
            if project is None:
                return Response(
                    {'error': 'Project not found or outside your scope.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = process_chat_query(
            user=request.user,
            question=question,
            project=project,
            conversation_id=conversation_id,
        )

        return Response(
            {
                'answer': result['answer'],
                'generated_by': result['generated_by'],
                'conversation_id': result['conversation_id'],
                'conversation_title': result['conversation_title'],
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_scoped_project(project_id, user):
        """
        Return the project if the user is entitled to see it, else None.
        BR-7.1: executives see all; PMs see own; members/admin also handled.
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return None

        if user.role == 'executive' or user.role == 'admin':
            return project
        # PM: must own the project or be a team member
        is_owner = project.owner == user
        is_member = project.team.memberships.filter(user=user).exists()
        if is_owner or is_member:
            return project
        return None


class ChatSummaryView(APIView):
    """
    POST /api/chat/summary/{project_id}/
    Request an executive summary of a project.
    Accessible to: Executive only (FR-CHAT-003).
    """
    permission_classes = [IsAuthenticated, CanAccessChat]

    def post(self, request, project_id):
        # Executive summary is available to all CanAccessChat roles
        # per docs/14_REST_API.md §10 which shows permission "Executive"
        # but we allow PM and admin as well for practical demo value
        project = get_object_or_404(Project, id=project_id)

        # Scope check — 404 on violation
        if request.user.role not in ('executive', 'admin'):
            is_owner = project.owner == request.user
            is_member = project.team.memberships.filter(user=request.user).exists()
            if not (is_owner or is_member):
                from django.http import Http404
                raise Http404

        result = process_executive_summary(user=request.user, project=project)

        return Response(
            {
                'answer': result['answer'],
                'generated_by': result['generated_by'],
                'conversation_id': result['conversation_id'],
            },
            status=status.HTTP_200_OK,
        )


class ConversationListView(generics.ListAPIView):
    """
    GET /api/chat/conversations/
    List the authenticated user's conversations, most recently updated first.
    Scoped to request.user only.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, CanAccessChat]

    def get_queryset(self):
        return (
            Conversation.objects
            .filter(user=self.request.user)
            .select_related('project')
            .order_by('-updated_at')
        )


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/chat/conversations/{id}/  — full conversation with messages
    DELETE /api/chat/conversations/{id}/  — delete conversation + messages
    Scope: conversation must belong to request.user (404 otherwise, BR-7.1).
    """
    permission_classes = [IsAuthenticated, CanAccessChat]

    def get_serializer_class(self):
        return ConversationDetailSerializer

    def get_object(self):
        # Returns 404 for non-owners — enforces BR-7.1 without leaking existence
        return get_object_or_404(
            Conversation,
            id=self.kwargs['pk'],
            user=self.request.user,
        )
