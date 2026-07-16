from django.db import models
import uuid


class ChatMessage(models.Model):
    """
    Chat messages for the AI assistant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    
    # Optional: link to project for scoped context
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
