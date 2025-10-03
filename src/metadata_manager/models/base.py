from django.db import models

# Place for common base models/mixins


class BaseModel(models.Model):
    """Abstract base model for common logic.

    Extend this for shared fields or methods in all models.

    Attributes:
        None by default; add common fields in subclass as needed.
    """

    class Meta:
        abstract = True
