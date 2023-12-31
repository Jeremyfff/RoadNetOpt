
class Geometry:
    """
    几何对象的基类， 包括道路、建筑等可以画图的
    """
    __all_geometries = set()

    def __init__(self):
        pass

    def plot(self, *args, **kwargs):
        pass

    @staticmethod
    def register(obj):
        Geometry.__all_geometries.add(obj)

    @staticmethod
    def plot_all(*args, **kwargs):
        for geo in Geometry.__all_geometries:
            geo.plot(*args, **kwargs)


from geo.building import Building
from geo.road import Road
from geo.terrain import Terrain
