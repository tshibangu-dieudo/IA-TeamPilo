"""
Serializers for accounts app.
See .ai/coding-rules.md: Views stay thin, serializers handle data validation.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserSkill


class UserSkillSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSkill model.
    """
    class Meta:
        model = UserSkill
        fields = ['id', 'skill_name', 'proficiency_level', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for User with skills.
    """
    skills = UserSkillSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'created_at', 'skills']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login - username/email and password.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
