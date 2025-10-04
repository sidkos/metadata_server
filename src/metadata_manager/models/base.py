"""Base model mixins and shared abstractions for ORM models."""
from django.db import models


class BaseModel(models.Model):
    """Abstract base model for common logic.

    Extend this for shared fields or methods in all models.

    Attributes:
        None by default; add common fields in subclass as needed.
    """

    class Meta:
        abstract = True
