from django.urls import path
from . import views

urlpatterns = [
    # Teams
    path('teams/', views.TeamViewSet.as_view({'get': 'list', 'post': 'create'}), name='team_list'),
    path('teams/<uuid:pk>/', views.TeamViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='team_detail'),
    path('my-teams/', views.MyTeamsView.as_view(), name='my_teams'),
    
    # Skills
    path('skills/', views.SkillViewSet.as_view({'get': 'list', 'post': 'create'}), name='skill_list'),
    path('skills/<uuid:pk>/', views.SkillViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='skill_detail'),
    
    # Team Memberships
    path('memberships/', views.TeamMembershipViewSet.as_view({'get': 'list', 'post': 'create'}), name='membership_list'),
    path('memberships/<uuid:pk>/', views.TeamMembershipViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='membership_detail'),
]
