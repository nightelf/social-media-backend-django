from django.db.models.functions import Now
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer, MarkReadInputSerializer


# Create your views here.
class NotificationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("actor")

    @action(detail=False, methods=['get'], url_path="unseen-count")
    def unseen_count(self, request):
        count = self.get_queryset().filter(seen_at__isnull=True).count()
        return Response({"count": count})

    @action(detail=False, methods=['post'])
    def seen(self, request):
        self.get_queryset().filter(seen_at__isnull=True).update(seen_at=Now())
        return Response({"count": 0})

    @action(detail=False, methods=['post'])
    def read(self, request):
        s = MarkReadInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        nid = s.validated_data["notification_id"]

        notification = get_object_or_404(Notification, id=nid, recipient=request.user)
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])

        return Response({"read_at": notification.read_at})