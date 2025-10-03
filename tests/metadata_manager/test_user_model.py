import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from metadata_manager.models.user import User, validate_israeli_id, validate_phone

pytestmark = pytest.mark.django_db


def test_validate_israeli_id_valid():
    """Test that valid Israeli IDs pass validation.

    Args:
        None

    Raises:
        AssertionError: If a valid ID fails validation.
    """
    for valid_id in ["123456782", "295857213", "000000019"]:
        validate_israeli_id(valid_id)  # Should not raise


@pytest.mark.parametrize(
    "bad_id",
    [
        "123456780",  # Bad checksum
        "12345678A",  # Non-numeric
        "123",  # Too short
        "1000000000",  # Too long
    ],
)
def test_validate_israeli_id_invalid(bad_id):
    """Test that invalid Israeli IDs raise ValidationError."""
    with pytest.raises(ValidationError):
        validate_israeli_id(bad_id)


def test_validate_phone_valid():
    """Test that valid phone numbers pass validation."""
    valid = [
        "+972501234567",
        "+12025550123",
        "+441632960961",
    ]
    for phone in valid:
        validate_phone(phone)  # Should not raise


@pytest.mark.parametrize(
    "bad_phone",
    [
        "0501234567",
        "+1 202-555-0123x123",
        "12345",
        "abcdefg",
        "+97212345",
    ],
)
def test_validate_phone_invalid(bad_phone):
    """Test that invalid phone numbers raise ValidationError."""
    with pytest.raises(ValidationError):
        validate_phone(bad_phone)


def test_create_user_valid(db):
    """Test creating a user with all valid fields."""
    User.objects.create(id="123456782", name="John Doe", phone="+972501234567", address="Tel Aviv")
    fetch = User.objects.get(id="123456782")
    assert fetch.name == "John Doe"
    assert fetch.phone == "+972501234567"
    assert fetch.address == "Tel Aviv"


@pytest.mark.parametrize("field,value", [("name", ""), ("address", "")])
def test_user_required_fields(field, value):
    """Test that required fields cannot be blank."""
    fields = dict(id="123456782", name="Test Name", phone="+972501234567", address="Somewhere")
    fields[field] = value
    with pytest.raises((ValidationError, IntegrityError)):
        user = User(**fields)
        user.full_clean()
