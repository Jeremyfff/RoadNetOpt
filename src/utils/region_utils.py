from enum import Enum


class RegionAccessibleType(Enum):
    ACCESSIBLE = 0
    RESTRICTED = 1
    INACCESSIBLE = 2
    UNDEFINED = -1


class RegionType(Enum):
    ARTIFICIAL = 0
    WATER = 1
    BOUNDARY = 2
    UNDEFINED = -1
