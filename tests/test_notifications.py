"""Behavior tests for the notifications endpoints (Django/DRF).
Mirrors the FastAPI test matrix so the two backends are proven behaviorally identical."""
import pytest
from rest_framework.test import APIClient

from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db

NT = Notification.NotificationType


# ---- GET /api/notifications ----------------------------------------------

def test_only_shows_own_notifications(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)
    make_notification(recipient=bob, actor=alice, type_=NT.FOLLOW)

    data = client_as(alice).get("/api/notifications").json()
    assert data["total"] == 1
    assert data["results"][0]["actor"]["username"] == bob.username


def test_requires_authentication():
    resp = APIClient().get("/api/notifications")
    assert resp.status_code == 401


def test_response_shape(client_as, make_user, make_post, make_notification):
    alice = make_user()
    bob = make_user()
    post = make_post(alice)
    make_notification(recipient=alice, actor=bob, type_=NT.LIKE, post=post)
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)  # no post

    results = client_as(alice).get("/api/notifications").json()["results"]
    by_type = {r["type"]: r for r in results}

    assert set(by_type) == {"LIKE", "FOLLOW"}
    assert by_type["LIKE"]["post_id"] == post.id
    assert by_type["FOLLOW"]["post_id"] is None
    assert by_type["LIKE"]["read_at"] is None
    assert by_type["LIKE"]["actor"] == {"id": bob.id, "username": bob.username}


def test_newest_first(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    for _ in range(3):
        make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)

    ids = [r["id"] for r in client_as(alice).get("/api/notifications").json()["results"]]
    assert ids == sorted(ids, reverse=True)


def test_pagination(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    for _ in range(25):
        make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)

    p1 = client_as(alice).get("/api/notifications?page=1&page_size=20").json()
    assert p1["total"] == 25
    assert p1["total_pages"] == 2
    assert len(p1["results"]) == 20

    p2 = client_as(alice).get("/api/notifications?page=2&page_size=20").json()
    assert len(p2["results"]) == 5


def test_empty(client_as, make_user):
    data = client_as(make_user()).get("/api/notifications").json()
    assert data["total"] == 0
    assert data["results"] == []


# ---- GET /api/notifications/unseen-count ---------------------------------

def test_unseen_count_excludes_seen(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW, seen=False)
    make_notification(recipient=alice, actor=bob, type_=NT.LIKE, seen=False)
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW, seen=True)  # excluded

    assert client_as(alice).get("/api/notifications/unseen-count").json() == {"count": 2}


def test_unseen_count_keys_off_seen_not_read(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.LIKE, read=True, seen=False)
    assert client_as(alice).get("/api/notifications/unseen-count").json() == {"count": 1}


def test_unseen_count_recipient_scoped(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)
    make_notification(recipient=bob, actor=alice, type_=NT.FOLLOW)
    assert client_as(alice).get("/api/notifications/unseen-count").json()["count"] == 1


# ---- POST /api/notifications/seen ----------------------------------------

def test_mark_seen_clears_count(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)
    make_notification(recipient=alice, actor=bob, type_=NT.LIKE)
    client = client_as(alice)

    resp = client.post("/api/notifications/seen")
    assert resp.status_code == 200
    assert resp.json() == {"count": 0}
    assert client.get("/api/notifications/unseen-count").json() == {"count": 0}


def test_mark_seen_only_own(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)
    make_notification(recipient=bob, actor=alice, type_=NT.FOLLOW)

    client_as(alice).post("/api/notifications/seen")
    assert client_as(bob).get("/api/notifications/unseen-count").json()["count"] == 1


def test_mark_seen_does_not_touch_read_at(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    n = make_notification(recipient=alice, actor=bob, type_=NT.LIKE)

    client_as(alice).post("/api/notifications/seen")
    n.refresh_from_db()
    assert n.seen_at is not None   # marked seen
    assert n.read_at is None       # stays unread


# ---- POST /api/notifications/read ----------------------------------------

def test_mark_read(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    n = make_notification(recipient=alice, actor=bob, type_=NT.FOLLOW)

    resp = client_as(alice).post("/api/notifications/read", {"notification_id": n.id}, format="json")
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None
    n.refresh_from_db()
    assert n.read_at is not None


def test_mark_read_missing_id_is_422(client_as, make_user):
    resp = client_as(make_user()).post("/api/notifications/read", {}, format="json")
    assert resp.status_code == 422


def test_mark_read_not_mine_is_404(client_as, make_user, make_notification):
    alice = make_user()
    bob = make_user()
    n = make_notification(recipient=bob, actor=alice, type_=NT.FOLLOW)  # bob's, not alice's

    resp = client_as(alice).post("/api/notifications/read", {"notification_id": n.id}, format="json")
    assert resp.status_code == 404
