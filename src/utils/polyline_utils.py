import numpy as np
from scipy.interpolate import interp1d


def interpolate_by_t(points, t):
    distances = np.cumsum(np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1)))
    distances = np.insert(distances, 0, 0)
    normalized_distances = distances / distances[-1]

    interp_func = interp1d(normalized_distances, points, axis=0)

    interpolated_point = interp_func(t)
    return interpolated_point


def interpolate_by_distance(points, step_size):
    distances = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
    cumulative_distances = np.insert(np.cumsum(distances), 0, 0)

    interp_func = interp1d(cumulative_distances, points, axis=0)

    new_distances = np.arange(0, cumulative_distances[-1], step_size)

    new_points = interp_func(new_distances)
    return new_points


def get_closed_polyline(points):
    assert points.shape[0] > 1, "Only two points or more can form a polyline."
    distance = np.linalg.norm(points[0] - points[-1])
    if distance == 0:
        return points
    else:
        return np.concatenate((points, [points[0]]), axis=0)

