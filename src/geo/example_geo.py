from geo import Geometry
import numpy as np
from utils import BuildingType


class ExampleGeo(Geometry):
    """
    This is an example of a minimized geometric class
    """
    __all_example_geo = set()

    def __init__(self):
        super().__init__()
        Geometry.register(self)
        ExampleGeo.register(self)
        # do your stuff

    def plot(self, *args, **kwargs):
        super(ExampleGeo, self).plot(*args, **kwargs)
        # do your plot stuff

    @staticmethod
    def register(obj):
        ExampleGeo.__all_example_geo.add(obj)

    @staticmethod
    def plot_all(*args, **kwargs):
        for geo in ExampleGeo.__all_example_geo:
            geo.plot(*args, **kwargs)
