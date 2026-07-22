"""
Views for notifications app.
See .ai/coding-rules.md: Views stay thin — validate request, call service, return response.
See docs/14_REST_API.md §9 for endpoint specification.

Endpoints:
  GET  /api/notifications/            — list current user's notifications (scoped)
  PATCH /api/notifications/{id}/read/ — mark single notification as read
  PATCH /api/notifications/read-all/  — mark all as read, returns {"marked_read": N}
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer
from .services import mark_notification_read_service, mark_all_read_service


class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    Returns the authenticated user's notifications ordered by created_at DESC.
    Scoped to request.user only — other users' notifications are invisible (BR-7.1).
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .filter(user=self.request.user)
            .select_related('project', 'task')
            .order_by('-created_at')
        )


class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/{id}/read/
    Mark a single notification as read.
    Returns 404 if the notification does not belong to the authenticated user
    (scope violation, per .ai/business-rules.md — 404 not 403).
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # get_object_or_404 on the user-scoped queryset enforces the 404 rule
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification = mark_notification_read_service(notification)
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )


class NotificationMarkAllReadView(APIView):
    """
    PATCH /api/notifications/read-all/
    Mark all unread notifications for the authenticated user as read.
    Returns {"marked_read": N} where N is the count of records updated.
    Idempotent: returns {"marked_read": 0} when all are already read.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        count = mark_all_read_service(request.user)
        return Response({'marked_read': count}, status=status.HTTP_200_OK)
