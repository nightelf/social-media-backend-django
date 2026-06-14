from django.db.models import Count, Exists, OuterRef
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common import exceptions as err

from .models import Comment, Like, Post
from .serializers import CommentSerializer, PostSerializer


class PostViewSet(viewsets.ModelViewSet):
    """Feed CRUD + like + comments. Paths match the contract (no trailing slash via router)."""

    serializer_class = PostSerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Post.objects.select_related("author")
            .annotate(
                like_count=Count("likes", distinct=True),
                comment_count=Count("comments", distinct=True),
                liked_by_me=Exists(
                    Like.objects.filter(post=OuterRef("pk"), user=user.id)
                ),
            )
        )
        if self.action == "list" and self.request.query_params.get("scope") == "following":
            qs = qs.filter(author__followers__follower=user)
        # Explicit, deterministic newest-first ordering (annotate() can drop Meta.ordering).
        return qs.order_by("-created_at", "-id")

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        post = Post.objects.create(author=request.user, body=s.validated_data["body"])
        out = self.get_queryset().get(pk=post.pk)
        return Response(self.get_serializer(out).data, status=201)

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise err.forbidden("You can only delete your own posts.")
        instance.delete()

    @action(detail=True, methods=["post", "delete"], url_path="like")
    def like(self, request, pk=None):
        post = self.get_object()
        if request.method == "POST":
            Like.objects.get_or_create(user=request.user, post=post)
            liked, status_code = True, 201
        else:
            Like.objects.filter(user=request.user, post=post).delete()
            liked, status_code = False, 200
        return Response({"liked_by_me": liked, "like_count": post.likes.count()},
                        status=status_code)

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "POST":
            s = CommentSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            comment = Comment.objects.create(
                post=post, author=request.user, body=s.validated_data["body"]
            )
            return Response(CommentSerializer(comment).data, status=201)

        qs = post.comments.select_related("author").all()
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(CommentSerializer(page, many=True).data)
