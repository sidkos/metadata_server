"""Utility helpers for test data and validation.

Provides functions to:
- Generate valid Israeli IDs
- Validate Israeli IDs
- Generate random valid E.164 phone numbers (IL)
"""

import random

import phonenumbers


def generate_random_phone_number() -> str:
    """Generate a random valid Israeli phone number in E.164 format.

    Returns:
        str: A valid phone number string (e.g., "+97286XXXXXX").
    """
    while True:
        phone_number = f"+97286{random.randint(100000, 999999)}"
        try:
            phone = phonenumbers.parse(phone_number)
            if phonenumbers.is_valid_number(phone):
                return phone_number
        except phonenumbers.NumberParseException:
            continue


def is_valid_israeli_id(id_str: str, from_right: bool = True) -> bool:
    """Validate a 9-digit Israeli ID (Teudat Zehut).

    Applies the standard checksum algorithm.

    Args:
        id_str (str): String of 9 digits (leading zeros allowed).
        from_right (bool, optional): If True, alternate weights starting from the
            rightmost digit; if False, from the leftmost. Defaults to True.

    Returns:
        bool: True if the ID is valid, False otherwise.
    """
    if not (id_str.isdigit() and len(id_str) == 9):
        return False

    total = 0
    for idx, ch in enumerate(id_str):
        digit = int(ch)
        pos = len(id_str) - 1 - idx if from_right else idx
        weight = 1 if (pos % 2 == 0) else 2
        product = digit * weight
        total += product if product < 10 else product - 9

    return total % 10 == 0


def generate_israeli_id(from_right: bool = True) -> str:
    """Generate a random valid 9-digit Israeli ID.

    Args:
        from_right (bool, optional): Whether the checksum alternation starts from
            the rightmost digit (True) or the leftmost digit (False). Defaults to True.

    Returns:
        str: A 9-digit string that passes the checksum validation.

    Raises:
        RuntimeError: If a valid check digit cannot be computed (unexpected).
    """

    first8 = [random.randint(0, 9) for _ in range(8)]
    # Try check digit 0..9 to make whole 9-digit valid
    for check in range(10):
        digits = first8 + [check]
        candidate = "".join(str(d) for d in digits)
        if is_valid_israeli_id(candidate, from_right=from_right):
            return candidate

    raise RuntimeError("Failed to compute a check digit (unexpected)")
