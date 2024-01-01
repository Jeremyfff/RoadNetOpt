class ParentMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if not hasattr(cls, 'registry'):
            cls.registry = []
        else:
            cls.registry.append(cls)

    def plot_all(cls):
        for c in cls.registry:
            c.plot_all()


class Object(metaclass=ParentMeta):
    """
    几何对象的基类， 包括道路、建筑等可以画图的
    """

    def __init__(self):
        pass

    def plot(self, *args, **kwargs):
        pass



from geo.building import Building
from geo.road import Road
from geo.terrain import Terrain
