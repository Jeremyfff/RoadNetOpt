import math
import numpy as np
import shapely.plotting
from matplotlib import pyplot as plt
from shapely import Point, LineString

def xywh2points(x, y, w, h):
    pt1 = (x - w / 2, y - h / 2)
    pt2 = (x - w / 2, y + h / 2)
    pt3 = (x + w / 2, y + h / 2)
    pt4 = (x + w / 2, y - h / 2)
    points = np.array([pt1, pt2, pt3, pt4])
    return points


def point_grid(xmin: float, ymin: float, xmax: float, ymax: float, gap: float):
    num_points_x, num_points_y = math.ceil(float(xmax - xmin) / gap) + 1, math.ceil(float(ymax - ymin) / gap) + 1
    num_points_x = 2 if num_points_x < 2 else num_points_x
    num_points_y = 2 if num_points_y < 2 else num_points_y
    x = np.linspace(xmin, xmax, num_points_x)
    y = np.linspace(ymin, ymax, num_points_y)
    X, Y = np.meshgrid(x, y)
    n = num_points_x * num_points_y
    X_reshaped = X.reshape(n, 1)
    Y_reshaped = Y.reshape(n, 1)

    points = np.hstack((X_reshaped, Y_reshaped))
    return points


def points_to_geo(points: np.ndarray):
    assert len(points.shape) == 2
    if points.shape[0] < 2:
        geometry = Point(points)
    else:
        geometry = LineString(points)
    return geometry

def plot_points(points: np.ndarray, values=None, sizes=None, show_values=False):
    x = points[:, 0]
    y = points[:, 1]
    plt.scatter(x, y, s=sizes, c=values, cmap='viridis')
    # plot values
    if show_values:
        for i in range(len(values)):
            plt.text(x[i], y[i], f'{values[i]:.2f}', fontsize=6, ha='center', va='bottom')


def points_in_radius(points: np.ndarray, target_point: np.ndarray, threshold: float) -> np.ndarray:
    distances = np.linalg.norm(points - target_point, axis=1)
    selected_points = points[distances < threshold]
    return selected_points


def offset_points(points, offset):
    return points + offset


def normalize_vector(vec):
    length = math.sqrt(vec[0] ** 2 + vec[1] ** 2)
    if length == 0:
        return np.array([0, 0])
    else:
        new_vec = vec / length
        return new_vec


def normalize_vectors(vec):
    lengths = np.linalg.norm(vec, axis=1)
    zero_length_indices = np.where(lengths == 0)
    new_vec = vec / lengths[:, np.newaxis]
    new_vec[zero_length_indices] = [0, 0]
    return new_vec


def v_rotate_vectors(vec):
    rotation_matrix = np.array([[0, -1], [1, 0]])
    rotated_vec = np.dot(vec, rotation_matrix)
    return rotated_vec

def vector_from_points(src, dst):
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    return (dx, dy)

def vector_dot(vec1, vec2):
    return vec1[0] * vec2[0] + vec1[1] * vec2[1]