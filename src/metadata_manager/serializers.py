from rest_framework import serializers

from .models.user import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = ["id", "name", "phone", "address"]
