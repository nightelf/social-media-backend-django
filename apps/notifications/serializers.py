from rest_framework import serializers

from .models import Notification


class ActorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):

    actor = ActorSerializer(read_only=True)
    post_id = serializers.IntegerField(allow_null=True, read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'type', "post_id", 'seen_at', 'read_at', 'created_at']


class MarkReadInputSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField()