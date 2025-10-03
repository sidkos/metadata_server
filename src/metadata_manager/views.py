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
    """
    ViewSet for creating, retrieving, and listing users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["get"])
    def ids(self, request: Request) -> Response:
        """
        List all user IDs.
        """
        ids = list(self.get_queryset().values_list("id", flat=True))
        return Response(ids)


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheck(generics.GenericAPIView):
    """
    Simple health check endpoint.
    """

    serializer_class = HealthCheckSerializer
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Health check GET method.
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
