from django.db import models
from django.conf import settings


# Create your models here.
class Notification(models.Model):
    class Meta:
        ordering = ['-created_at', '-id']

    class NotificationType(models.TextChoices):
        LIKE = "LIKE", 'Like'
        COMMENT = "COMMENT", 'Comment'
        FOLLOW = "FOLLOW", 'Follow'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="notifications")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='notifications_sent')
    type = models.CharField(
        max_length=8,
        choices=NotificationType.choices
    )
    post = models.ForeignKey(settings.POST_MODEL, on_delete=models.CASCADE,
                             related_name='notifications', null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
