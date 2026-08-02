"""Signal trigger tests: creating/deleting Like/Comment/Follow rows drives notifications.

These exercise the signals directly via the ORM (the Django-idiomatic way — the trigger is a
model hook, not endpoint code, so saving the row is what fires it)."""
import pytest

from apps.posts.models import Comment, Like
from apps.users.models import Follow
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_like_creates_notification_for_post_author(make_user, make_post):
    author = make_user()
    actor = make_user()
    post = make_post(author)

    Like.objects.create(user=actor, post=post)

    n = Notification.objects.get(recipient=author)
    assert n.type == "LIKE"
    assert n.actor_id == actor.id
    assert n.post_id == post.id


def test_unlike_removes_notification(make_user, make_post):
    author = make_user()
    actor = make_user()
    post = make_post(author)

    like = Like.objects.create(user=actor, post=post)
    assert Notification.objects.filter(recipient=author, type="LIKE").exists()

    like.delete()
    assert not Notification.objects.filter(recipient=author, type="LIKE").exists()


def test_liking_own_post_notifies_no_one(make_user, make_post):
    author = make_user()
    post = make_post(author)

    Like.objects.create(user=author, post=post)
    assert not Notification.objects.filter(recipient=author).exists()


def test_each_comment_creates_its_own_notification(make_user, make_post):
    author = make_user()
    actor = make_user()
    post = make_post(author)

    Comment.objects.create(author=actor, post=post, body="one")
    Comment.objects.create(author=actor, post=post, body="two")

    assert Notification.objects.filter(recipient=author, type="COMMENT").count() == 2


def test_deleting_one_comment_removes_one_notification(make_user, make_post):
    author = make_user()
    actor = make_user()
    post = make_post(author)

    c1 = Comment.objects.create(author=actor, post=post, body="one")
    Comment.objects.create(author=actor, post=post, body="two")
    assert Notification.objects.filter(recipient=author, type="COMMENT").count() == 2

    c1.delete()
    assert Notification.objects.filter(recipient=author, type="COMMENT").count() == 1


def test_follow_creates_then_unfollow_removes(make_user):
    followed = make_user()
    follower = make_user()

    f = Follow.objects.create(follower=follower, followed=followed)
    assert Notification.objects.filter(recipient=followed, type="FOLLOW").exists()

    f.delete()
    assert not Notification.objects.filter(recipient=followed, type="FOLLOW").exists()
