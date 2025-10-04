"""API views for the metadata manager app.

Includes user CRUD endpoints and a public health check endpoint.
"""

from __future__ import annotations

from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models.user import User
from .serializers import UserSerializer


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """User operations.

    Provides create, retrieve, and list operations for User resources.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["get"])
    def ids(self, request: Request) -> Response:
        """List all user IDs.

        Args:
            request (Request): The incoming request instance.

        Returns:
            Response: A list of user IDs (strings).
        """
        ids = list(self.get_queryset().values_list("id", flat=True))
        return Response(ids)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for the health check response.

    Fields:
        status (CharField): Service status string (e.g., "ok").
    """

    status = serializers.CharField()


class HealthCheck(generics.GenericAPIView):
    """Public health check endpoint.

    This endpoint does not require authentication and returns a simple status payload.
    """

    serializer_class = HealthCheckSerializer
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Return service status.

        Args:
            request (Request): The incoming request instance.
            *args: Unused positional arguments.
            **kwargs: Unused keyword arguments.

        Returns:
            Response: JSON body {"status": "ok"} with HTTP 200.
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
