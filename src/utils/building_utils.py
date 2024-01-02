from enum import Enum


class BuildingMovableType(Enum):
    NONDEMOLISHABLE = 0
    FLEXABLE = 1
    DEMOLISHABLE = 2
    UNDEFINED = -1


class BuildingStyle(Enum):
    HERITAGE = 0
    HISTORICAL = 1
    TRADITIONAL = 2
    NORMAL = 3
    UNDEFINED = -1


class BuildingQuality(Enum):
    GOOD = 0
    FAIR = 1
    POOR = 2
    UNDEFINED = -1
