from utils import RoadLevel, RoadState
from utils import BuildingMovableType, BuildingStyle, BuildingQuality
from utils import RegionAccessibleType


ROAD_COLOR_BY_LEVEL = {
    RoadLevel.MAIN: (0, 0, 0),
    RoadLevel.SECONDARY: (0.2, 0.2, 0.2),
    RoadLevel.BRANCH: (0.4, 0.4, 0.4),
    RoadLevel.ALLEY: (0.6, 0.6, 0.6),
    RoadLevel.CUSTOM: (0, 0, 0),
}

ROAD_WIDTH_BY_LEVEL = {
    RoadLevel.MAIN: 5,
    RoadLevel.SECONDARY: 4,
    RoadLevel.BRANCH: 3,
    RoadLevel.ALLEY: 2,
    RoadLevel.CUSTOM: 1,
}

ROAD_COLOR_BY_STATE = {
    RoadState.RAW: (0, 0, 0),
    RoadState.OPTIMIZED: (0.2, 0.2, 0.2),
    RoadState.OPTIMIZING: (0.4, 0.4, 0.4),
}

BUILDING_COLOR_BY_MOVABLE_TYPE = {
    BuildingMovableType.NONDEMOLISHABLE: (0, 0, 0),
    BuildingMovableType.FLEXABLE: (0.2, 0.2, 0.2),
    BuildingMovableType.DEMOLISHABLE: (0.4, 0.4, 0.4),
    BuildingMovableType.UNDEFINED: (0.6, 0.6, 0.6)
}
BUILDING_COLOR_BY_STYLE = {
    BuildingStyle.HERITAGE: (0, 0, 0),
    BuildingStyle.HISTORICAL: (0.2, 0.2, 0.2),
    BuildingStyle.TRADITIONAL: (0.4, 0.4, 0.4),
    BuildingStyle.NORMAL: (0.6, 0.6, 0.6),
    BuildingStyle.UNDEFINED: (0.8, 0.8, 0.8),
}

BUILDING_COLOR_BY_QUALITY = {
    BuildingQuality.GOOD: (0, 0, 0),
    BuildingQuality.FAIR: (0.2, 0.2, 0.2),
    BuildingQuality.POOR: (0.4, 0.4, 0.4),
    BuildingQuality.UNDEFINED: (0.6, 0.6, 0.6)
}


REGION_COLOR_BY_ACCESSIBLE = {
    RegionAccessibleType.ACCESSIBLE: (0, 0, 0, 0.3),
    RegionAccessibleType.RESTRICTED: (0.2, 0.2, 0.2, 0.3),
    RegionAccessibleType.INACCESSIBLE: (0.4, 0.4, 0.4, 0.3),
    RegionAccessibleType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
}
REGION_COLOR_BY_TYPE = {
    RegionAccessibleType.ACCESSIBLE: (0, 0, 0, 0.3),
    RegionAccessibleType.RESTRICTED: (0.2, 0.2, 0.2, 0.3),
    RegionAccessibleType.INACCESSIBLE: (0.4, 0.4, 0.4, 0.3),
    RegionAccessibleType.UNDEFINED: (0.6, 0.6, 0.6, 0.3)
}
def get_road_plot_style(road, by='level'):
    if by == 'level':
        _add_points = False
        _color = ROAD_COLOR_BY_LEVEL[road.level]
        _linewidth = ROAD_WIDTH_BY_LEVEL[road.level]
    elif by == 'state':
        _add_points = False
        _color = ROAD_COLOR_BY_STATE[road.state]
        _linewidth = ROAD_WIDTH_BY_LEVEL[road.level]
    else:
        _add_points = False
        _color = None
        _linewidth = None
    # return {'color': _color, 'linewidth': _linewidth, 'add_points': _add_points}
    return {'color': _color, 'linewidth': _linewidth}



def get_building_plot_style(building, by='movable'):
    if by == 'movable':
        _add_points = False
        _color = BUILDING_COLOR_BY_MOVABLE_TYPE[building.movable]
        _linewidth = None
        _facecolor = BUILDING_COLOR_BY_MOVABLE_TYPE[building.movable]
        _edgecolor = BUILDING_COLOR_BY_MOVABLE_TYPE[building.movable]
    elif by == 'style':
        _add_points = False
        _color = BUILDING_COLOR_BY_STYLE[building.style]
        _linewidth = None
        _facecolor = BUILDING_COLOR_BY_STYLE[building.style]
        _edgecolor = BUILDING_COLOR_BY_STYLE[building.style]
    elif by == 'quality':
        _add_points = False
        _color = BUILDING_COLOR_BY_QUALITY[building.quality]
        _linewidth = None
        _facecolor = BUILDING_COLOR_BY_QUALITY[building.quality]
        _edgecolor = BUILDING_COLOR_BY_QUALITY[building.quality]
    else:
        _add_points = False
        _color = None
        _linewidth = None
        _facecolor = None
        _edgecolor = None
    # return {'color': _color, 'linewidth': _linewidth, 'add_points': _add_points, 'facecolor': _facecolor,
    #         'edgecolor': _edgecolor}
    return {'color': _color, 'linewidth': _linewidth, 'facecolor': _facecolor,
            'edgecolor': _edgecolor}


def get_region_plot_style(region, by='accessible'):
    if by == 'accessible':
        _add_points = False
        _color = REGION_COLOR_BY_ACCESSIBLE[region.accessible]
        _linewidth = 1
        _facecolor = REGION_COLOR_BY_ACCESSIBLE[region.accessible]
        _edgecolor = REGION_COLOR_BY_ACCESSIBLE[region.accessible]
    elif by == 'type':
        _add_points = False
        _color = REGION_COLOR_BY_TYPE[region.region_type]
        _linewidth = 1
        _facecolor = REGION_COLOR_BY_TYPE[region.region_type]
        _edgecolor = REGION_COLOR_BY_TYPE[region.region_type]
    else:
        _add_points = False
        _color = None
        _linewidth = None
        _facecolor = None
        _edgecolor = None
    return {'color': _color, 'linewidth': _linewidth, 'facecolor': _facecolor,
            'edgecolor': _edgecolor}

