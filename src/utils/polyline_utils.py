import numpy as np
from scipy.interpolate import interp1d


def split_by_distance(points, step_size):
    # 计算多段线上相邻点之间的累积距离
    distances = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
    cumulative_distances = np.insert(np.cumsum(distances), 0, 0)

    # 创建线性插值函数
    interp_func = interp1d(cumulative_distances, points, axis=0)

    # 指定每隔一定距离取点
    new_distances = np.arange(0, cumulative_distances[-1], step_size)

    # 使用线性插值函数获取新的点
    new_points = interp_func(new_distances)
    return new_points
