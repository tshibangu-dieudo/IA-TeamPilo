from rest_framework import viewsets
from .models import ChatMessage


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ChatMessage management.
    """
    queryset = ChatMessage.objects.all()
