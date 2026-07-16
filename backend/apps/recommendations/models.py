from django.db import models
import uuid


class Recommendation(models.Model):
    """
    AI-generated task reassignment recommendation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    CONFIDENCE_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='recommendations')
    from_user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recommendations_from')
    to_user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recommendations_to')
    
    confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # AI-generated justification
    justification = models.TextField()
    
    # Fallback template used if AI was unavailable
    used_fallback = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'recommendations'
