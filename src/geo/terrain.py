import numpy as np
from geo import Object


class Terrain(Object):
    @staticmethod
    def plot_all():
        pass

    @staticmethod
    def data_to_terrain(data):
        raise NotImplementedError

    @staticmethod
    def terrain_to_data(out_data):
        raise NotImplementedError
