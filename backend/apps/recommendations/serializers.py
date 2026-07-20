from rest_framework import serializers
from .models import Recommendation
from apps.accounts.models import User
from apps.tasks.models import Task


class UserCompactSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class TaskCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title']


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Recommendation model.
    Exposes clean aliases and compact nested structures to match the REST API specs.
    """
    justification = serializers.CharField(source='explanation', read_only=True)
    confidence_level = serializers.SerializerMethodField()
    
    # Details placeholders used in custom serialization representation
    task_details = TaskCompactSerializer(source='task', read_only=True)
    current_assignee_details = UserCompactSerializer(source='current_assignee', read_only=True)
    suggested_assignee_details = UserCompactSerializer(source='suggested_assignee', read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            'id', 'project', 'task', 'task_details',
            'current_assignee', 'current_assignee_details',
            'suggested_assignee', 'suggested_assignee_details',
            'recommendation_type', 'title', 'description', 'explanation',
            'justification', 'confidence_score', 'confidence_level',
            'priority', 'status', 'generated_by', 'created_at', 'updated_at',
            'accepted_by', 'accepted_at', 'dismissed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'generated_by',
            'accepted_by', 'accepted_at', 'dismissed_at'
        ]

    def get_confidence_level(self, obj):
        score = obj.confidence_score
        if score >= 80:
            return 'HIGH'
        elif score >= 60:
            return 'MEDIUM'
        else:
            return 'LOW'

    def to_representation(self, instance):
        """
        Transform serialization payload to match JSON layout from REST_API.md §8:
        Injects nested JSON for task, current_assignee, and suggested_assignee.
        """
        data = super().to_representation(instance)
        
        # Replace task primary key with nested detailed dict
        if data.get('task_details'):
            data['task'] = data.pop('task_details')
        else:
            data.pop('task_details', None)
            
        # Replace current_assignee ID with nested user details
        if data.get('current_assignee_details'):
            data['current_assignee'] = data.pop('current_assignee_details')
        else:
            data.pop('current_assignee_details', None)
            
        # Replace suggested_assignee ID with nested user details
        if data.get('suggested_assignee_details'):
            data['suggested_assignee'] = data.pop('suggested_assignee_details')
        else:
            data.pop('suggested_assignee_details', None)
            
        return data
