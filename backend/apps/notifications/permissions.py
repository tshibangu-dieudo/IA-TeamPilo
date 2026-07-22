"""
Permission classes for notifications app.
See .ai/business-rules.md: scope violations return 404, not 403.
Ownership check is enforced at the queryset level (get_queryset filters to
request.user), so no additional object-level permission class is needed.
"""
from rest_framework.permissions import IsAuthenticated
