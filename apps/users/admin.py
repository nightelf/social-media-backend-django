from django.contrib import admin

from .models import Follow, User, VerificationCode


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "phone", "is_active",
                    "email_verified", "phone_verified", "created_at")
    search_fields = ("username", "email", "phone")


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "channel", "purpose", "expires_at", "consumed_at", "attempts")
    list_filter = ("channel", "purpose")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "followed", "created_at")
