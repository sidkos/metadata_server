from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HealthCheck, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("users/", UserViewSet.as_view({"get": "list", "post": "create"})),
    path("users/<str:pk>/", UserViewSet.as_view({"get": "retrieve"})),
    path("health/", HealthCheck.as_view()),
    path("", include(router.urls)),
]
