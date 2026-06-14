"""Seed identical demo data. Run: python manage.py seed"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.posts.models import Comment, Like, Post
from apps.users.models import Follow, User

DEMO = [
    ("ada",   "ada@example.com",   "+15555550101", "Mathematician & first programmer."),
    ("alan",  "alan@example.com",  "+15555550102", "Computing, codebreaking, morphogenesis."),
    ("grace", "grace@example.com", "+15555550103", "Rear admiral. Found the first bug."),
    ("linus", "linus@example.com", "+15555550104", "I just like building kernels."),
]
PASSWORD = "hunter2x!"


class Command(BaseCommand):
    help = "Create demo users, posts, likes, comments, and follows."

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(username="ada").exists():
            self.stdout.write(self.style.WARNING("Demo data already present; skipping."))
            return

        users = {}
        for username, email, phone, bio in DEMO:
            u = User.objects.create_user(
                username=username, password=PASSWORD, email=email, phone=phone, bio=bio,
            )
            u.email_verified = True
            u.phone_verified = True
            u.is_active = True
            u.save()
            users[username] = u

        # superuser for /admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(username="admin", password="admin",
                                          email="admin@example.com")

        posts = [
            Post.objects.create(author=users["ada"], body="Hello world — my first post on Sigmagram!"),
            Post.objects.create(author=users["alan"], body="Can machines think? Asking for a friend."),
            Post.objects.create(author=users["grace"], body="Found a literal moth in the relay today."),
            Post.objects.create(author=users["ada"], body="Note G: the engine weaves algebraic patterns."),
            Post.objects.create(author=users["linus"], body="Released a small update. Talk is cheap."),
        ]

        Like.objects.create(user=users["alan"], post=posts[0])
        Like.objects.create(user=users["grace"], post=posts[0])
        Like.objects.create(user=users["ada"], post=posts[1])
        Like.objects.create(user=users["linus"], post=posts[2])

        Comment.objects.create(post=posts[0], author=users["grace"], body="Welcome aboard!")
        Comment.objects.create(post=posts[1], author=users["ada"], body="They can compute, at least.")
        Comment.objects.create(post=posts[2], author=users["linus"], body="Classic.")

        follows = [
            ("alan", "ada"), ("grace", "ada"), ("linus", "ada"),
            ("ada", "alan"), ("ada", "grace"),
        ]
        for follower, followed in follows:
            Follow.objects.get_or_create(follower=users[follower], followed=users[followed])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(users)} users, {len(posts)} posts. Demo login: ada / {PASSWORD}"
        ))
