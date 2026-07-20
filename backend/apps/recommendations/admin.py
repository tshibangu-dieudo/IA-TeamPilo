from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'project',
        'recommendation_type',
        'confidence_score',
        'priority',
        'status',
        'generated_by',
        'created_at',
    ]
    list_filter = ['status', 'recommendation_type', 'priority', 'generated_by']
    search_fields = ['title', 'description', 'explanation', 'project__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = [
        'project',
        'task',
        'current_assignee',
        'suggested_assignee',
        'accepted_by',
    ]
