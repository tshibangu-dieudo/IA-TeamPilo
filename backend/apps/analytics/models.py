from django.db import models
import uuid


class WorkloadSnapshot(models.Model):
    """
    Snapshot of user workload at a point in time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='workload_snapshots')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='workload_snapshots')
    workload_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        db_table = 'workload_snapshots'


class RiskScore(models.Model):
    """
    Project risk score calculation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='risk_scores')
    score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    
    # Component scores
    overload_component = models.DecimalField(max_digits=5, decimal_places=2)
    blocked_tasks_component = models.DecimalField(max_digits=5, decimal_places=2)
    deadline_proximity_component = models.DecimalField(max_digits=5, decimal_places=2)
    historical_velocity_component = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        db_table = 'risk_scores'
