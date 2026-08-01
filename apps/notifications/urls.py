from rest_framework.routers import DefaultRouter

from .views import NotificationsViewSet

router = DefaultRouter(trailing_slash="")
router.register("notifications", NotificationsViewSet, basename="notification")

urlpatterns = router.urls