from django.urls import path
from . import views

urlpatterns = [
    # Projects
    path('projects/', views.ProjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='project_list'),
    path('projects/<uuid:pk>/', views.ProjectViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='project_detail'),
    path('my-projects/', views.MyProjectsView.as_view(), name='my_projects'),
]
