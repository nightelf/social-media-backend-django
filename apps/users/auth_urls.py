from django.urls import path

from . import auth_views as v

# mounted at /api/auth/
urlpatterns = [
    path("register", v.RegisterView.as_view()),
    path("verify", v.VerifyView.as_view()),
    path("login", v.LoginView.as_view()),
    path("login/code", v.LoginCodeView.as_view()),
    path("challenge", v.ChallengeView.as_view()),
    path("resend", v.ResendView.as_view()),
    path("refresh", v.RefreshView.as_view()),
]
