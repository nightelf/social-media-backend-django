from rest_framework import viewsets, mixins

from .models import Notification
from .serializers import NotificationSerializer


# Create your views here.
class NotificationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("actor")
