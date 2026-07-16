from rest_framework import viewsets
from .models import Notification


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Notification management.
    """
    queryset = Notification.objects.all()
