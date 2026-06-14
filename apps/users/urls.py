from django.urls import path

from .auth_views import DevLastCodeView
from .views import FollowView, MeView, PublicProfileView

# mounted at /api/
urlpatterns = [
    path("dev/last-code", DevLastCodeView.as_view()),
    path("users/me", MeView.as_view()),
    path("users/<str:username>", PublicProfileView.as_view()),
    path("users/<str:username>/follow", FollowView.as_view()),
]
