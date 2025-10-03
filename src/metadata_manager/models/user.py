import phonenumbers
from django.core.exceptions import ValidationError
from django.db import models

from .base import BaseModel


def validate_israeli_id(value: str) -> None:
    """Validate that given value is a valid Israeli ID.

    Args:
        value (str): The ID value to validate.

    Raises:
        ValidationError: If the ID is not valid (wrong length, non-digit, bad checksum).
    """
    id_num = value.zfill(9)
    if not id_num.isdigit() or not (5 <= len(value) <= 9):
        raise ValidationError("ID must be a string of 5-9 digits")
    total = 0
    for idx, char in enumerate(id_num):
        digit = int(char)
        multiplied = digit * (1 if idx % 2 == 0 else 2)
        if multiplied > 9:
            multiplied -= 9
        total += multiplied
    if total % 10 != 0:
        raise ValidationError("Invalid Israeli ID checksum")


def validate_phone(value: str) -> None:
    """Validate that given value is a valid phone number in E.164 format.

    Args:
        value (str): Phone number in string format.

    Raises:
        ValidationError: If the phone number is not valid or not in E.164 format.
    """
    try:
        phone = phonenumbers.parse(value)
        if not phonenumbers.is_possible_number(phone) or not phonenumbers.is_valid_number(phone):
            raise ValidationError("Phone number is not valid.")
    except Exception as exc:
        raise ValidationError("Phone number must be in valid international format (e.g., +972...)") from exc


class User(BaseModel):
    """User model with Israeli ID, name, phone, and address.

    Attributes:
        objects (models.Manager[User]): The default manager for User.
        id (models.CharField): Israeli ID, used as primary key.
        name (models.CharField): Full name.
        phone (models.CharField): Phone number in E.164 format.
        address (models.CharField): Street address.
    """

    objects: models.Manager["User"]

    id: models.CharField
    name: models.CharField
    phone: models.CharField
    address: models.CharField

    id = models.CharField(
        primary_key=True,
        unique=True,
        max_length=9,
        validators=[validate_israeli_id],
        help_text="Israeli ID (string, 5-9 digits, valid checksum)",
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name (required).",
    )
    phone = models.CharField(
        max_length=20,
        validators=[validate_phone],
        help_text="Phone number in E.164 format (e.g., +972...).",
    )
    address = models.CharField(
        max_length=255,
        help_text="Street address (required).",
    )

    def __str__(self) -> str:
        """Return a string representation of the user.

        Returns:
            str: User name and ID in format 'Name (ID)'.
        """
        return f"{self.name} ({self.id})"
