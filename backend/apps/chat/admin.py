from django.contrib import admin
from .models import Conversation, ChatMessage


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'project', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'generated_by', 'project', 'created_at']
    list_filter = ['role', 'generated_by', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['id', 'created_at']
