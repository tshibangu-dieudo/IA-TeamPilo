"""
URL configuration for analytics app.
See docs/14_REST_API.md §7 for endpoint specification.

Mounted at /api/analytics/ in config/urls.py.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Workload endpoints
    # GET /api/analytics/workload/{user_id}/
    path('workload/<uuid:user_id>/', views.WorkloadDetailView.as_view(), name='workload_detail'),
    # GET /api/analytics/workload/{user_id}/history
    path('workload/<uuid:user_id>/history/', views.WorkloadHistoryView.as_view(), name='workload_history'),
    # GET /api/analytics/workload/team/{team_id}/
    path('workload/team/<uuid:team_id>/', views.TeamWorkloadView.as_view(), name='team_workload'),
    
    # Risk score endpoints
    # GET /api/analytics/risk/{project_id}/
    path('risk/<uuid:project_id>/', views.RiskScoreDetailView.as_view(), name='risk_detail'),
    # GET /api/analytics/risk/{project_id}/history
    path('risk/<uuid:project_id>/history/', views.RiskScoreHistoryView.as_view(), name='risk_history'),
    # GET /api/analytics/risk/portfolio
    path('risk/portfolio/', views.PortfolioRiskView.as_view(), name='portfolio_risk'),
]
