from collections import defaultdict
from typing import TypeVar, Callable, Any
from utils import graphic_uitls
from geo import Road, Building, Region

DataProcessFunc = TypeVar('DataProcessFunc', bound=Callable[[int], bool])


class Resource:
    def __init__(self, name: str, get_data_func: Callable):
        self.name = name
        self.get_data_func: Callable = get_data_func
        self.cached_data = None

    def get_data(self, *args, **kwargs) -> Any:
        if self.cached_data is not None:
            return self.cached_data
        data = self.get_data_func(*args, **kwargs)
        self.cached_data = data
        return data

    def clear_data(self):
        self.cached_data = None


class ResourcesManager:
    def __init__(self):
        self.resources: dict[str:Resource] = {}

    def create_resource(self, name: str, get_data_func: Callable) -> Resource:
        self.resources[name] = Resource(name, get_data_func)
        return self.resources[name]

    def get_data(self, name: str, *args, **kwargs) -> Any:
        return self.resources[name].get_data(*args, **kwargs)

    def clear_data(self, name: str):
        self.resources[name].clear_data()


if __name__ == '__main__':
    rm = ResourcesManager()


    def get_road_data(number):
        print('getting road data')
        return number


    def get_building_data():
        print('getting building data')
        return 2


    def get_mixed_data():
        print('getting mixed data')
        road_data = rm.get_data('road')
        building_data = rm.get_data('building')
        return road_data + building_data


    rm.create_resource('road', get_road_data)
    rm.create_resource('building', get_building_data)
    rm.create_resource('mixed', get_mixed_data)

    print('epoch 1 ====================')
    mixed_data = rm.get_data('mixed')
    print(mixed_data)
    print('epoch 2 ====================')
    mixed_data = rm.get_data('mixed')
    print(mixed_data)
    print('epoch 3 ====================')
