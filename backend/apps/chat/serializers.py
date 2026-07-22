"""
Serializers for the chat app.
See docs/14_REST_API.md §10 for endpoint spec.
"""
from rest_framework import serializers
from .models import Conversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'generated_by', 'created_at']
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    """Summary serializer — no messages included (avoid N+1 on list)."""
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'project', 'project_name', 'created_at', 'updated_at']
        read_only_fields = fields


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Full serializer including all messages in chronological order."""
    messages = ChatMessageSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'project', 'project_name', 'messages', 'created_at', 'updated_at']
        read_only_fields = fields


class ChatQuerySerializer(serializers.Serializer):
    """
    Input serializer for POST /api/chat/query/
    See docs/14_REST_API.md §10.
    """
    question = serializers.CharField(
        min_length=1,
        max_length=1000,
        help_text="The natural-language question to ask the AI assistant.",
    )
    project_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional: scope the data snapshot to a specific project.",
    )
    conversation_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Optional: continue an existing conversation.",
    )


class ChatSummarySerializer(serializers.Serializer):
    """
    Input serializer for POST /api/chat/summary/{project_id}/
    See docs/14_REST_API.md §10.
    """
    # project_id comes from the URL — no body fields required
    pass
