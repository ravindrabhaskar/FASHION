from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

api_router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_router.urls)),
    path("api/v1/auth/", include("accounts.urls.auth_urls")),
    path("api/v1/profile/", include("profiles.urls")),
    path("api/v1/plans/", include("subscriptions.urls")),
    path("api/v1/fashion/", include("fashion.urls")),
    path("api/v1/wardrobe/", include("wardrobe.urls")),
    path("api/v1/social/", include("social.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/designers/", include("designers.urls")),
    path("api/v1/brands/", include("brands.urls")),
    path("api/v1/marketplace/", include("marketplace.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/payments/", include("payments.urls")),
    path("api/v1/chat/", include("chat.urls")),
    path("api/v1/creators/", include("creators.urls")),
    path("api/v1/campaigns/", include("campaigns.urls")),
    path("api/v1/trends/", include("analytics.urls")),
    path("api/v1/ai/", include("ai.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
