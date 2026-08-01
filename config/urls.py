from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health, name="health"),
    path("api/auth/", include("apps.users.auth_urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.posts.urls")),
    path("api/", include("apps.notifications.urls")),
    # OpenAPI docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
