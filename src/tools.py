import random

import phonenumbers


def generate_random_phone_number() -> str:
    while True:
        phone_number = f"+97286{random.randint(100000, 999999)}"
        try:
            phone = phonenumbers.parse(phone_number)
            if phonenumbers.is_valid_number(phone):
                return phone_number
        except phonenumbers.NumberParseException:
            continue


def is_valid_israeli_id(id_str: str, from_right: bool = True) -> bool:
    """
    Validate a 9-digit Israeli ID (Teudat Zehut) using the checksum algorithm.
    - id_str: string of 9 digits (leading zeros allowed)
    - from_right: if True, weights 1/2 alternate starting from the RIGHTmost digit;
                  if False, start alternating from the LEFTmost digit.
    Returns True if valid.
    """
    if not (id_str.isdigit() and len(id_str) == 9):
        return False

    total = 0
    # Process digits and weights
    # We'll index digits left-to-right, but compute weight depending on from_right.
    for idx, ch in enumerate(id_str):
        digit = int(ch)
        # position_from_right = (len-1 - idx)
        if from_right:
            pos = len(id_str) - 1 - idx
        else:
            pos = idx
        weight = 1 if (pos % 2 == 0) else 2
        product = digit * weight
        # sum of product digits: same as product if < 10 else product - 9
        total += product if product < 10 else product - 9

    return total % 10 == 0


def generate_israeli_id(from_right: bool = True) -> str:
    """
    Generate one random, checksum-valid 9-digit Israeli ID.
    from_right parameter must match your validator's convention.
    """
    # Generate first 8 digits
    first8 = [random.randint(0, 9) for _ in range(8)]
    # Try check digit 0..9 to make whole 9-digit valid
    for check in range(10):
        digits = first8 + [check]
        candidate = "".join(str(d) for d in digits)
        if is_valid_israeli_id(candidate, from_right=from_right):
            return candidate
    # Should never happen, but fall back to deterministic compute (safe)
    raise RuntimeError("Failed to compute a check digit (unexpected)")
