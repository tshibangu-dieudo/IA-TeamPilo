"""
Serializers for projects app.
See .ai/coding-rules.md: Views stay thin, serializers handle data validation.
"""
from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'status', 
                  'owner', 'team', 'created_at', 'updated_at', 'owner_username', 
                  'owner_email', 'team_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate that end_date is after start_date."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        
        return attrs


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating projects.
    """
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'owner', 'team']
    
    def validate(self, attrs):
        """Validate that end_date is after start_date."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        
        return attrs


class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Project with full information.
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'status',
                  'owner', 'team', 'created_at', 'updated_at', 'owner_username',
                  'owner_email', 'team_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
