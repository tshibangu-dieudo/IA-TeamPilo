from django.contrib import admin
from .models import WorkloadSnapshot, RiskScore


@admin.register(WorkloadSnapshot)
class WorkloadSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'workload_percentage', 'created_at']


@admin.register(RiskScore)
class RiskScoreAdmin(admin.ModelAdmin):
    list_display = ['project', 'score', 'created_at']
