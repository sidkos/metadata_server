"""Application URL routes.

Exposes:
- /api/users/ (list, create)
- /api/users/<id>/ (retrieve, update, partial_update, destroy)
- /api/health/ (public health check)
Additionally registers routes with a DRF router for the UserViewSet.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HealthCheck, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("users/", UserViewSet.as_view({"get": "list", "post": "create"})),
    path(
        "users/<str:pk>/",
        UserViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path("health/", HealthCheck.as_view()),
    path("", include(router.urls)),
]
