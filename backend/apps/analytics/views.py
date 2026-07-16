from rest_framework import viewsets
from .models import WorkloadSnapshot, RiskScore


class WorkloadSnapshotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for WorkloadSnapshot management.
    """
    queryset = WorkloadSnapshot.objects.all()


class RiskScoreViewSet(viewsets.ModelViewSet):
    """
    API endpoint for RiskScore management.
    """
    queryset = RiskScore.objects.all()
