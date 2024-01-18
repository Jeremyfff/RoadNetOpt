from collections import defaultdict


class Resource:
    def __init__(self, parents):
        self.parents: list['Resource'] = parents
        self.data = None

    def get_data(self):
        for parent in self.parents:
            parent.get_data()

    def clear_data(self):
        pass


class ResourcesManager:
    def __init__(self):
        self.cache_space = defaultdict(lambda: None)

    def cache(self, name, data):
        self.cache_space[name] = data

    def get(self, name):
        return self.cache_space[name]

    def clear(self, name):
        self.cache_space[name] = None


class EnvResourcesManager(ResourcesManager):
    def __init__(self):
        super().__init__()

    def get_building_img(self):
        pass

    def get_raw_road_img(self):
        pass
