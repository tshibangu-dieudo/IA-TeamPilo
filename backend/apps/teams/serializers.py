"""
Serializers for teams app.
See .ai/coding-rules.md: Views stay thin, serializers handle data validation.
"""
from rest_framework import serializers
from .models import Team, Skill, TeamMembership


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for Skill model.
    """
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class TeamMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for TeamMembership model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'team', 'user', 'role', 'created_at', 'user_username', 'user_email', 'team_name']
        read_only_fields = ['id', 'created_at']


class TeamMembershipCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating TeamMembership.
    """
    class Meta:
        model = TeamMembership
        fields = ['team', 'user', 'role']


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for Team model.
    """
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'memberships', 'member_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.memberships.count()


class TeamDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Team with full membership information.
    """
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'memberships', 'member_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.memberships.count()
