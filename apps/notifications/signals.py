from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.posts.models import Comment, Like
from apps.users.models import Follow
from .models import Notification


@receiver(post_save, sender=Comment)
def create_notification_from_comment(sender, instance, created, **kwargs):

    if not created:
        return
    if instance.post.author == instance.author:
        return

    Notification.objects.create(
        recipient=instance.post.author,
        actor=instance.author,
        type=Notification.NotificationType.COMMENT,
        post=instance.post
    )


@receiver(post_delete, sender=Comment)
def remove_notification_from_deleted_comment(sender, instance, **kwargs):

    if instance.post.author == instance.author:
        return

    one_notification = Notification.objects.filter(
        recipient=instance.post.author,
        actor=instance.author,
        type=Notification.NotificationType.COMMENT,
        post=instance.post
    ).first()

    if one_notification:
        one_notification.delete()


@receiver(post_save, sender=Like)
def create_notification_from_like(sender, instance, created, **kwargs):

    if not created:
        return
    if instance.user == instance.post.author:
        return

    Notification.objects.create(
        recipient=instance.post.author,
        actor=instance.user,
        type=Notification.NotificationType.LIKE,
        post=instance.post
    )


@receiver(post_delete, sender=Like)
def remove_notification_from_unlike(sender, instance, **kwargs):

    if instance.user == instance.post.author:
        return

    Notification.objects.filter(
        recipient=instance.post.author,
        actor=instance.user,
        type=Notification.NotificationType.LIKE,
        post=instance.post
    ).delete()


@receiver(post_save, sender=Follow)
def create_notification_from_follow(sender, instance,created, **kwargs):

    if not created:
        return
    if instance.followed == instance.follower:
        return

    Notification.objects.create(
        recipient=instance.followed,
        actor=instance.follower,
        type=Notification.NotificationType.FOLLOW,
    )


@receiver(post_delete, sender=Follow)
def remove_notification_from_unfollow(sender, instance, **kwargs):

    if instance.followed == instance.follower:
        return

    Notification.objects.filter(
        recipient=instance.followed,
        actor=instance.follower,
        type=Notification.NotificationType.FOLLOW,
    ).delete()