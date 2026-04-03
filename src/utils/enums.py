from enum import Enum

class ENTITY_RESOLUTION_TYPES(Enum):
    """Strategies for resolving multiple values during entity matching."""

    NOTHING = 0
    """No resolution applied.

    Used when values are identical or when resolution is handled externally
    (e.g., platform is assumed equal before merging).
    """

    MIN = 1
    """Select the minimum value.

    - Numbers/dates: smallest or earliest value
    - Strings: shorter string
    """

    MAX = 2
    """Select the maximum value.

    - Numbers/dates: largest or latest value
    - Strings: longer string
    """

    UNION = 3
    """Merge values into a separated string.

    Used for multi-valued string fields (e.g., genres, summary).
    """