"""Pluggable code delivery. Default writes to the log; smtp/twilio are optional stubs.

Selected by the NOTIFIER env var (console | smtp | twilio).
"""
import logging

from django.conf import settings

logger = logging.getLogger("notifier")


class ConsoleNotifier:
    """Prints the code to the backend log — zero setup, visible in `docker compose logs`."""

    def send(self, *, channel, destination, code, purpose):
        logger.warning(
            "[notifier:console] %s code for %s via %s -> %s",
            purpose, destination, channel, code,
        )
        # Also print so it shows even if logging is quiet.
        print(f"\n*** {channel} code to {destination} ({purpose}): {code} ***\n", flush=True)


class SMTPNotifier:
    """Sends email codes via Django's email backend (configure SMTP_* env vars)."""

    def send(self, *, channel, destination, code, purpose):
        if channel != "EMAIL":
            return ConsoleNotifier().send(
                channel=channel, destination=destination, code=code, purpose=purpose
            )
        from django.core.mail import send_mail

        send_mail(
            subject="Your verification code",
            message=f"Your code is {code}. It expires in {settings.CODE_TTL_MINUTES} minutes.",
            from_email=None,
            recipient_list=[destination],
        )


class TwilioNotifier:
    """Sends SMS codes via Twilio (configure TWILIO_* env vars)."""

    def send(self, *, channel, destination, code, purpose):
        if channel != "SMS":
            return SMTPNotifier().send(
                channel=channel, destination=destination, code=code, purpose=purpose
            )
        import os

        from twilio.rest import Client  # imported lazily; only needed for this backend

        client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
        client.messages.create(
            body=f"Your code is {code} (expires in {settings.CODE_TTL_MINUTES} min).",
            from_=os.environ["TWILIO_FROM"],
            to=destination,
        )


_NOTIFIERS = {
    "console": ConsoleNotifier,
    "smtp": SMTPNotifier,
    "twilio": TwilioNotifier,
}


def get_notifier():
    return _NOTIFIERS.get(settings.NOTIFIER, ConsoleNotifier)()
