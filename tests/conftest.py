"""Test harness (pytest-django). pytest-django manages the test database and wraps each
`@pytest.mark.django_db` test in a transaction that rolls back — no manual setup needed.
Auth uses DRF's `force_authenticate` (bypasses the JWT flow)."""
import uuid

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client_as():
    """Return an APIClient authenticated as the given user."""
    def _for(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    return _for


@pytest.fixture
def make_user():
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def _make(username=None):
        uid = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=username or f"user_{uid}", password="pw", email=f"{uid}@example.com"
        )
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user

    return _make


@pytest.fixture
def make_post():
    from apps.posts.models import Post

    def _make(author, body="hello"):
        return Post.objects.create(author=author, body=body)

    return _make


@pytest.fixture
def make_notification():
    from django.utils import timezone

    from apps.notifications.models import Notification

    def _make(recipient, actor, type_, post=None, seen=False, read=False):
        now = timezone.now()
        return Notification.objects.create(
            recipient=recipient, actor=actor, type=type_, post=post,
            seen_at=now if seen else None, read_at=now if read else None,
        )

    return _make
