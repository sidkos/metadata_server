"""Serializers for API representation of models."""

from rest_framework import serializers

from .models.user import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        model = User
        fields = ["id", "name", "phone", "address"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users enforcing id immutability.

    - `id` is read-only.
    - If `id` appears in the request body and differs from the instance id, return 400.
    - If `id` equals the existing instance id, allow it (some clients always send it).
    """

    class Meta:
        model = User
        fields = ["id", "name", "phone", "address"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validate update payload and enforce `id` immutability.

        Args:
            attrs: The validated attributes collected by the serializer for update.

        Returns:
            dict: The validated attributes to be used by the serializer.

        Raises:
            serializers.ValidationError: If the input payload attempts to change
                the immutable primary key `id`.
        """
        incoming = getattr(self, "initial_data", {}) or {}
        if "id" in incoming and self.instance is not None:
            # Allow if the provided id equals the current instance id
            if str(incoming.get("id")) != str(self.instance.id):
                raise serializers.ValidationError({"id": "Updating id is not allowed."})
        return super().validate(attrs)
