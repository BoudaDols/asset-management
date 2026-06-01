"""Shared validation functions for the Municipal Asset Management System.

All functions are pure (no side effects, no database access) and deterministic
(same input always produces the same output).

These validators enforce format rules for codes, names, and structural constraints
used across catalog entries, asset instances, and imports.
"""

import re

# Precompiled patterns for performance
_CODE_FORMAT_PATTERN = re.compile(r"^[A-Z0-9_]{1,50}$")
_INSTANCE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,50}$")


def validate_code_format(code: str) -> bool:
    """Validate that a catalog code matches the required format.

    Catalog codes must be uppercase alphanumeric plus underscore,
    between 1 and 50 characters.

    Pattern: ^[A-Z0-9_]{1,50}$

    Args:
        code: The code string to validate.

    Returns:
        True if the code matches the required pattern, False otherwise.
    """
    return bool(_CODE_FORMAT_PATTERN.match(code))


def validate_name(name: str) -> bool:
    """Validate that a name field is non-empty, non-whitespace-only, and within length limits.

    Name fields must contain at least 1 non-whitespace character
    and must not exceed 255 characters total.

    Args:
        name: The name string to validate.

    Returns:
        True if the name is valid, False otherwise.
    """
    if len(name) > 255:
        return False
    if len(name.strip()) == 0:
        return False
    return True


def validate_instance_code(code: str) -> bool:
    """Validate that an asset instance code matches the required format.

    Instance codes allow alphanumeric (upper and lower case), underscore,
    and hyphen, between 1 and 50 characters.

    Pattern: ^[A-Za-z0-9_\\-]{1,50}$

    Args:
        code: The instance code string to validate.

    Returns:
        True if the code matches the required pattern, False otherwise.
    """
    return bool(_INSTANCE_CODE_PATTERN.match(code))


def validate_xor_catalog_ref(
    prim: str | None, seco: str | None, tert: str | None
) -> bool:
    """Validate that exactly one catalog reference is provided (XOR constraint).

    An asset instance must reference exactly one catalog level:
    primaire, secondaire, or tertiaire. This function enforces that
    exactly one of the three values is non-null.

    Args:
        prim: The primaire catalog code, or None.
        seco: The secondaire catalog code, or None.
        tert: The tertiaire catalog code, or None.

    Returns:
        True if exactly one of the three values is non-null, False otherwise.
    """
    count = sum(1 for ref in (prim, seco, tert) if ref is not None)
    return count == 1
