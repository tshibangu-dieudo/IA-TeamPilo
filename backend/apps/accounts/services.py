"""
Business logic for accounts app.
See .ai/coding-rules.md: Business logic lives in services.py, never in views.
"""
from django.contrib.auth import get_user_model
from .models import UserSkill

User = get_user_model()


def create_user_service(validated_data):
    """
    Create a new user with validated data.
    Called from RegisterView.
    """
    password = validated_data.pop('password')
    validated_data.pop('password_confirm', None)
    
    # Set default role to 'member' if not specified
    validated_data.setdefault('role', 'member')
    
    user = User.objects.create_user(password=password, **validated_data)
    return user


def add_user_skill_service(user, skill_name, proficiency_level):
    """
    Add a skill to a user's profile.
    """
    skill, created = UserSkill.objects.get_or_create(
        user=user,
        skill_name=skill_name,
        defaults={'proficiency_level': proficiency_level}
    )
    
    if not created:
        skill.proficiency_level = proficiency_level
        skill.save()
    
    return skill


def remove_user_skill_service(user, skill_name):
    """
    Remove a skill from a user's profile.
    """
    try:
        skill = UserSkill.objects.get(user=user, skill_name=skill_name)
        skill.delete()
        return True
    except UserSkill.DoesNotExist:
        return False
