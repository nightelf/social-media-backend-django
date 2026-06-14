from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager

EMAIL = "EMAIL"
SMS = "SMS"
CHANNEL_CHOICES = [(EMAIL, "Email"), (SMS, "SMS")]

PURPOSE_SIGNUP = "SIGNUP"
PURPOSE_LOGIN_2FA = "LOGIN_2FA"
PURPOSE_LOGIN_PASSWORDLESS = "LOGIN_PASSWORDLESS"
PURPOSE_CHOICES = [
    (PURPOSE_SIGNUP, "Signup verification"),
    (PURPOSE_LOGIN_2FA, "Login 2FA"),
    (PURPOSE_LOGIN_PASSWORDLESS, "Passwordless login"),
]


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    bio = models.TextField(blank=True, default="")

    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    # is_active stays False until every registered contact has been verified.
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.following.count()

    def verified_channels(self):
        channels = []
        if self.email and self.email_verified:
            channels.append(EMAIL)
        if self.phone and self.phone_verified:
            channels.append(SMS)
        return channels

    def destination_for(self, channel):
        return self.email if channel == EMAIL else self.phone

    def mark_channel_verified(self, channel):
        if channel == EMAIL:
            self.email_verified = True
        else:
            self.phone_verified = True

    def all_contacts_verified(self):
        ok = True
        if self.email:
            ok = ok and self.email_verified
        if self.phone:
            ok = ok and self.phone_verified
        return ok


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="codes")
    destination = models.CharField(max_length=255)
    channel = models.CharField(max_length=8, choices=CHANNEL_CHOICES)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    code_hash = models.CharField(max_length=255)
    # Plaintext is stored ONLY in dev so /api/dev/last-code can auto-fill the UI.
    dev_code = models.CharField(max_length=12, null=True, blank=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose", "consumed_at"])]

    def __str__(self):
        return f"{self.purpose} {self.channel} -> {self.destination}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="unique_follow")
        ]
