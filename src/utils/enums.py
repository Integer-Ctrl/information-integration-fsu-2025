from enum import Enum

class ENTITY_RESOLUTION_TYPES(Enum):
    # TODO: add description for each type
    NOTHING = 0
    MIN = 1
    MAX = 2
    UNION = 3
    LONGEST = 4