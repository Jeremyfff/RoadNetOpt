from utils.road_utils import RoadLevel
from utils.building_utils import BuildingType

ROAD_COLOR_BY_LEVEL = {
    RoadLevel.MAIN: (0, 0, 0),
    RoadLevel.SECONDARY: (0.2, 0.2, 0.2),
    RoadLevel.BRANCH: (0.4, 0.4, 0.4),
    RoadLevel.ALLEY: (0.6, 0.6, 0.6),
    RoadLevel.CUSTOM: (0, 0, 0),
}

ROAD_WIDTH_BY_LEVEL = {
    RoadLevel.MAIN: 20,
    RoadLevel.SECONDARY: 10,
    RoadLevel.BRANCH: 5,
    RoadLevel.ALLEY: 2,
    RoadLevel.CUSTOM: 1,
}

BUILDING_COLOR_BY_BUILDING_TYPE = {
    BuildingType.NONDEMOLISHABLE: (0, 0, 0),
    BuildingType.FLEXABLE: (0.2, 0.2, 0.2),
    BuildingType.DEMOLISHABLE: (0.4, 0.4, 0.4)
}


def get_road_style(road):
    _add_points = False
    _color = ROAD_COLOR_BY_LEVEL[road.level]
    _linewidth = ROAD_WIDTH_BY_LEVEL[road.level]
    return {'color': _color, 'linewidth': _linewidth, 'add_points': _add_points}


def get_building_style(building):
    _add_points = False
    _color = BUILDING_COLOR_BY_BUILDING_TYPE[building.building_type]
    _linewidth = None
    _facecolor = BUILDING_COLOR_BY_BUILDING_TYPE[building.building_type]
    _edgecolor = BUILDING_COLOR_BY_BUILDING_TYPE[building.building_type]
    return {'color': _color, 'linewidth': _linewidth, 'add_points': _add_points, 'facecolor': _facecolor,
            'edgecolor': _edgecolor}
