"""All /api/auth/* endpoints implementing the shared auth contract."""
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common import exceptions as err

from . import services
from .models import (
    PURPOSE_LOGIN_2FA,
    PURPOSE_LOGIN_PASSWORDLESS,
    PURPOSE_SIGNUP,
    User,
    VerificationCode,
)
from .serializers import RegisterSerializer


def find_user(identifier):
    return User.objects.filter(
        Q(username=identifier) | Q(email=identifier) | Q(phone=identifier)
    ).first()


def user_summary(user):
    return {
        "id": user.id,
        "username": user.username,
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email"),
            phone=data.get("phone"),
        )

        challenges = []
        if user.email:
            challenges.append(services.issue_code(user, channel="EMAIL", purpose=PURPOSE_SIGNUP))
        if user.phone:
            challenges.append(services.issue_code(user, channel="SMS", purpose=PURPOSE_SIGNUP))

        return Response(
            {
                "user_id": user.id,
                "challenges": [services.challenge_payload(c) for c in challenges],
            },
            status=201,
        )


class VerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        challenge_id = request.data.get("challenge_id")
        code = str(request.data.get("code", ""))
        vc = VerificationCode.objects.filter(id=challenge_id).select_related("user").first()
        if not vc:
            raise err.not_found("Unknown challenge.")

        services.check_code(vc, code)
        user = vc.user

        if vc.purpose == PURPOSE_SIGNUP:
            user.mark_channel_verified(vc.channel)
            user.save(update_fields=["email_verified", "phone_verified"])

            if user.all_contacts_verified():
                if not user.is_active:
                    user.is_active = True
                    user.save(update_fields=["is_active"])
                return Response({"status": "complete", **services.tokens_for(user),
                                 "user": user_summary(user)})

            remaining = (
                VerificationCode.objects.filter(
                    user=user, purpose=PURPOSE_SIGNUP, consumed_at__isnull=True
                )
                .values("id", "channel")
            )
            return Response({
                "status": "pending",
                "remaining": [{"challenge_id": r["id"], "channel": r["channel"]} for r in remaining],
            })

        # LOGIN_2FA / LOGIN_PASSWORDLESS -> issue tokens
        return Response({"status": "complete", **services.tokens_for(user),
                         "user": user_summary(user)})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier", "")
        password = request.data.get("password", "")
        user = find_user(identifier)
        if not user or not check_password(password, user.password):
            raise err.invalid_credentials()
        if not user.is_active:
            raise err.not_verified()
        return Response({
            "user_id": user.id,
            "channels": [{"channel": c} for c in user.verified_channels()],
        })


class LoginCodeView(APIView):
    """Passwordless: identifier must be a verified email/phone."""

    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier", "")
        user = find_user(identifier)
        if not user or not user.is_active or not user.verified_channels():
            raise err.invalid_credentials()
        return Response({
            "user_id": user.id,
            "channels": [{"channel": c} for c in user.verified_channels()],
        })


class ChallengeView(APIView):
    """Send a code to a chosen verified channel after login / login-code."""

    permission_classes = [AllowAny]

    def post(self, request):
        user = User.objects.filter(id=request.data.get("user_id")).first()
        channel = request.data.get("channel")
        purpose = request.data.get("purpose", PURPOSE_LOGIN_2FA)
        if not user:
            raise err.not_found("Unknown user.")
        if purpose not in (PURPOSE_LOGIN_2FA, PURPOSE_LOGIN_PASSWORDLESS):
            raise err.ContractError("validation_error", "Invalid purpose.", 422)
        if channel not in user.verified_channels():
            raise err.forbidden("That channel is not verified.")
        vc = services.issue_code(user, channel=channel, purpose=purpose)
        return Response(services.challenge_payload(vc), status=201)


class ResendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        old = VerificationCode.objects.filter(
            id=request.data.get("challenge_id")
        ).select_related("user").first()
        if not old:
            raise err.not_found("Unknown challenge.")
        vc = services.issue_code(old.user, channel=old.channel, purpose=old.purpose)
        return Response(services.challenge_payload(vc), status=201)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get("refresh"))
        except TokenError:
            raise err.ContractError("unauthenticated", "Invalid refresh token.", 401)
        return Response({"access": str(token.access_token)})


class DevLastCodeView(APIView):
    """Dev-only: return the latest plaintext code so the UI can auto-fill."""

    permission_classes = [AllowAny]

    def get(self, request):
        if settings.ENV != "dev":
            raise err.not_found()
        vc = VerificationCode.objects.filter(id=request.query_params.get("challenge_id")).first()
        if not vc or not vc.dev_code:
            raise err.not_found("No code for that challenge.")
        return Response({"challenge_id": vc.id, "code": vc.dev_code})
