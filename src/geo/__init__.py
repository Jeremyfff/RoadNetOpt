class ObjectMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if not hasattr(cls, 'registry'):
            cls.registry = []
        else:
            cls.registry.append(cls)

    def plot_all(cls):
        for c in cls.registry:
            c.plot_all()


class Object(metaclass=ObjectMeta):
    def __init__(self):
        pass




from geo.building import Building
from geo.road import Road
from geo.terrain import Terrain
from geo.region import Region
