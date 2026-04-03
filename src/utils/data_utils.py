import pandas as pd
from datetime import date

def has_value(value) -> bool:
    """Checks if a value is not null and not empty.

    Args:
        value: Input value.

    Returns:
        bool: True if value is valid.
    """
    return pd.notna(value) and value != ""


def min_columns(v1, v2):
    """Computes the minimum of two values if they are of compatible types (numbers or dates).
    For strings, it returns the shorter one.

    Args:
        v1: First value.
        v2: Second value.

    Returns:
        Value or pd.NA: Minimum value or NA if incompatible.
    """
    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
        return min(v1, v2)
    elif isinstance(v1, date) and isinstance(v2, date):
        return min(v1, v2)
    elif isinstance(v1, str) and isinstance(v2, str):
        return min(v1, v2, key=len)
    else:
        return pd.NA


def max_columns(v1, v2):
    """Computes the maximum of two values if they are of compatible types (numbers or dates).
    For strings, it returns the longer one.

    Args:
        v1: First value.
        v2: Second value.

    Returns:
        Value or pd.NA: Minimum value or NA if incompatible.
    """
    if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
        return max(v1, v2)
    elif isinstance(v1, date) and isinstance(v2, date):
        return max(v1, v2)
    elif isinstance(v1, str) and isinstance(v2, str):
        return max(v1, v2, key=len)
    else:
        return pd.NA


def union_delimited(v1, v2, delimiter=","):
    """Combines two delimited values.

    Args:
        v1: First value.
        v2: Second value.
        delimiter (str): Delimiter string.

    Returns:
        str: Combined value.
    """
    if has_value(v1) and has_value(v2):
        return f"{v1}{delimiter}{v2}"
    elif has_value(v1):
        return v1
    elif has_value(v2):
        return v2
    else:
        return ""