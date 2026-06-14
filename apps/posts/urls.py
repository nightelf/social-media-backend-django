from rest_framework.routers import DefaultRouter

from .views import PostViewSet

# trailing_slash="" -> paths match the contract exactly (/api/posts, /api/posts/{id})
router = DefaultRouter(trailing_slash="")
router.register("posts", PostViewSet, basename="post")

urlpatterns = router.urls
