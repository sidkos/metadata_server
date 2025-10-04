"""Data models and validators for the metadata manager app.

Includes the User model and helper validators for Israeli ID and phone numbers.
"""

from __future__ import annotations

from typing import Any

import phonenumbers
from django.core.exceptions import ValidationError
from django.db import models


def validate_israeli_id(value: str) -> None:
    """
    Validate that given value is a valid Israeli ID.

    Args:
        value (str): The ID value to validate.

    Raises:
        ValidationError: If not a valid Israeli ID.
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
    """
    Validate that given value is a valid phone number in E.164 format.

    Args:
        value (str): Phone number.

    Raises:
        ValidationError: If not a valid phone number.
    """
    try:
        phone = phonenumbers.parse(value)
        if not phonenumbers.is_possible_number(phone) or not phonenumbers.is_valid_number(phone):
            raise ValidationError("Phone number is not valid.")
    except Exception as exc:
        raise ValidationError("Phone number must be in valid international format (e.g., +972...)") from exc


class User(models.Model):
    """
    User model with Israeli ID, name, phone, and address.

    The ID is the primary key and must be a valid Israeli ID.
    Phone is stored in E.164 format and validated.
    """

    objects: models.Manager["User"]

    id: models.CharField[Any, Any]
    name: models.CharField[Any, Any]
    phone: models.CharField[Any, Any]
    address: models.CharField[Any, Any]

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
        """Return a human-readable representation.

        Returns:
            str: The user's name with ID in the format "Name (ID)".
        """
        return f"{self.name} ({self.id})"
