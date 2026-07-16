from django.contrib import admin
from .models import User, UserSkill


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'created_at']
    list_filter = ['role', 'created_at']


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_name', 'proficiency_level']
    list_filter = ['skill_name', 'proficiency_level']
