from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['task', 'from_user', 'to_user', 'confidence', 'status', 'created_at']
    list_filter = ['confidence', 'status', 'created_at']
