import time
import matplotlib.pyplot as plt


class RoadLevel(enumerate):
    MAIN = 0,
    SECONDARY = 1,
    BRANCH = 2,
    ALLEY = 3,
    CUSTOM = 4


class RoadState(enumerate):
    RAW = 0,
    OPTIMIZED = 1,
    OPTIMIZING = 2


all_highway_types = {'service', 'residential', 'footway', 'secondary', 'pedestrian', 'primary',
                     'tertiary', 'trunk', 'unclassified', 'secondary_link', 'busway', 'steps', 'cycleway'}

main_types = {'trunk', 'primary'}
secondary_types = {'secondary'}
branch_types = {'tertiary'}
alley_types = {'residential', 'footway', 'cycleway', 'steps', 'pedestrian'}


def highway_to_level(highway):
    if highway in main_types:
        return RoadLevel.MAIN
    elif highway in secondary_types:
        return RoadLevel.SECONDARY
    elif highway in branch_types:
        return RoadLevel.BRANCH
    elif highway in alley_types:
        return RoadLevel.ALLEY
    else:
        return RoadLevel.CUSTOM
