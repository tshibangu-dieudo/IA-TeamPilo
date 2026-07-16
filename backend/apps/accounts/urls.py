from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    
    # User management (admin only)
    path('users/', views.UserListView.as_view(), name='user_list'),
    
    # User skills
    path('skills/', views.UserSkillViewSet.as_view({'get': 'list', 'post': 'create'}), name='user_skills'),
    path('skills/<uuid:pk>/', views.UserSkillViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='user_skill_detail'),
]
