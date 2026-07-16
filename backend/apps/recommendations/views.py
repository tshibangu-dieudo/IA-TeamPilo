from rest_framework import viewsets
from .models import Recommendation


class RecommendationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Recommendation management.
    """
    queryset = Recommendation.objects.all()
