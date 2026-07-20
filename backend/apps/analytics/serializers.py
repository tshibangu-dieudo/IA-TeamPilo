"""
Serializers for analytics app.
See docs/14_REST_API.md §7 for endpoint specification.
"""
from rest_framework import serializers
from .models import WorkloadSnapshot, RiskScore


class WorkloadSnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkloadSnapshot.
    """
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = WorkloadSnapshot
        fields = [
            'id',
            'user',
            'user_full_name',
            'workload_percentage',
            'status',
            'computed_at',
        ]
        read_only_fields = ['id', 'computed_at']


class RiskScoreSerializer(serializers.ModelSerializer):
    """
    Serializer for RiskScore.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = RiskScore
        fields = [
            'id',
            'project',
            'project_name',
            'score',
            'level',
            'overload_factor',
            'blocked_task_factor',
            'deadline_proximity_factor',
            'historical_velocity_factor',
            'explanation_text',
            'computed_at',
        ]
        read_only_fields = ['id', 'computed_at']
