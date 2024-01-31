import logging

import numpy as np
import time
import imgui
import shapely
from shapely import Polygon
from shapely.ops import triangulate
import geopandas as gpd
from geovoronoi import voronoi_regions_from_coords


def get_arg(kwargs: dict, name: str, default: any = None):
    if name in kwargs:
        return kwargs[name]
    else:
        return default


def gaussian(x, mu, sigma):
    return np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * np.sqrt(2 * np.pi))


encode_ratio = 3


def id_to_rgb(i):
    ii = i * encode_ratio
    # 最大可编码16,777,216 / 3个数
    b = (ii % 256) / 256
    g = ((ii // 256) % 256) / 256
    r = ((ii // 256 // 256) % 256) / 256
    # print(f'i = {i}, r = {r}, g = {g}, b = {b}')
    return (r, g, b)


def rgb_to_id(color):
    id = color[0] * 256 * 256 + color[1] * 256 + color[2]
    id = round(id / encode_ratio)
    return id


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"函数 {func.__name__} 执行时间为: {execution_time} 秒")
        return result

    return wrapper


def to_triangles(polygon):
    delauney: list[Polygon] = triangulate(polygon)
    triangles = []
    for triangle in delauney:
        if shapely.within(triangle.centroid, polygon):
            triangles.append(triangle)
    return triangles





class DuplicateFilter:
    """
    Filters away duplicate log messages.
    Modified version of: https://stackoverflow.com/a/31953563/965332
    """

    def __init__(self, logger):
        self.last_msg = ""
        self.duplicate_count = 1
        self.logger = logger

    def filter(self, record):
        msg = str(record.msg)
        is_duplicate = (msg == self.last_msg)
        if not is_duplicate:
            if self.duplicate_count != 1:
                print(f"(the above msg repeated {self.duplicate_count} times)")
            self.last_msg = msg
            self.duplicate_count = 1
        else:
            self.duplicate_count += 1

        return not is_duplicate

    def __enter__(self):
        self.logger.addFilter(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.duplicate_count != 1:
            print(f"(the above msg repeated {self.duplicate_count} times)")
        self.logger.removeFilter(self)


def duplicate_filter(logger):
    def decorator(func):
        def wrapper(*args, **kwargs):
            duplicate_filter = DuplicateFilter(logger)
            with duplicate_filter:
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


if __name__ == '__main__':
    # 创建 logger 对象
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建自定义过滤器对象
    duplicate_filter = DuplicateFilter(logger)

    # 使用上下文管理器
    with duplicate_filter:
        logging.info("Hello")
        logging.info("Hello")
        logging.info("World")
