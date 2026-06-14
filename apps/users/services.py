"""Auth domain logic: issuing/verifying codes, masking, token minting."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common import exceptions as err
from apps.common.notifiers import get_notifier

from .models import EMAIL, VerificationCode


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def mask_destination(channel: str, destination: str) -> str:
    if channel == EMAIL and "@" in destination:
        name, domain = destination.split("@", 1)
        head = name[0] if name else ""
        return f"{head}***@{domain}"
    # phone -> show last 4
    digits = "".join(c for c in destination if c.isdigit())
    return f"***{digits[-4:]}" if len(digits) >= 4 else "***"


def issue_code(user, *, channel, purpose) -> VerificationCode:
    """Create + send a fresh code to the given channel."""
    destination = user.destination_for(channel)
    code = generate_code()
    vc = VerificationCode.objects.create(
        user=user,
        channel=channel,
        purpose=purpose,
        destination=destination,
        code_hash=make_password(code),
        dev_code=code if settings.ENV == "dev" else None,
        expires_at=timezone.now() + timedelta(minutes=settings.CODE_TTL_MINUTES),
    )
    get_notifier().send(channel=channel, destination=destination, code=code, purpose=purpose)
    return vc


def check_code(vc: VerificationCode, code: str) -> None:
    """Validate a submitted code against a challenge; raises ContractError on failure."""
    if vc.consumed_at is not None:
        raise err.code_invalid()
    if timezone.now() >= vc.expires_at:
        raise err.code_expired()
    if vc.attempts >= settings.CODE_MAX_ATTEMPTS:
        raise err.code_max_attempts()

    if not check_password(code, vc.code_hash):
        vc.attempts += 1
        vc.save(update_fields=["attempts"])
        if vc.attempts >= settings.CODE_MAX_ATTEMPTS:
            raise err.code_max_attempts()
        raise err.code_invalid()

    vc.consumed_at = timezone.now()
    vc.save(update_fields=["consumed_at"])


def tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def challenge_payload(vc: VerificationCode) -> dict:
    return {
        "challenge_id": vc.id,
        "channel": vc.channel,
        "destination": mask_destination(vc.channel, vc.destination),
    }
