"""
Models for the chat app.
See .ai/coding-rules.md: UUID PKs, created_at/updated_at where mutable.
See docs/13_AI_Architecture.md §3.3: conversation history for Chain 3.
See docs/09_Database_Design.md §15: Chat has no dedicated schema entry —
  the Conversation/ChatMessage pair implements the history contract
  from docs/13_AI_Architecture.md.

Conversation groups messages by session so history can be passed to
the LLM. Users own their own conversations (BR-7.1 scope isolation).
"""
import uuid
from django.db import models


class Conversation(models.Model):
    """
    Groups a sequence of ChatMessages for a user, optionally scoped to a project.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='conversations',
    )
    # Optional: scope to a specific project for context assembly
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
    )
    # Auto-generated title from first user message (truncated)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(
                fields=['user', 'updated_at'],
                name='conv_user_updated_idx',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.title or 'Untitled'}"


class ChatMessage(models.Model):
    """
    A single message in a conversation (user turn or assistant turn).
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    # Track whether this assistant message came from Granite or fallback
    generated_by = models.CharField(max_length=30, blank=True)

    # Kept for backward compatibility — mirrors the conversation's project FK
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages',
    )

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(
                fields=['conversation', 'created_at'],
                name='msg_conv_time_idx',
            ),
        ]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
