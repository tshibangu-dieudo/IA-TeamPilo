from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# The trailing slash will be automatically managed by the router
router.register(r'', views.RecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]
