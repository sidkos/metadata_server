"""App configuration for the metadata manager Django app."""

from django.apps import AppConfig


class MetadataManagerConfig(AppConfig):
    """Application configuration for metadata_manager."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "metadata_manager"
