import math
import numpy as np
import shapely.plotting
from matplotlib import pyplot as plt


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


def plot_points(points: np.ndarray, values=None, sizes=None):
    x = points[:, 0]
    y = points[:, 1]
    plt.scatter(x, y, s=sizes, c=values, cmap='viridis')
    # plot values
    for i in range(len(values)):
        plt.text(x[i], y[i], f'{values[i]:.2f}', fontsize=6, ha='center', va='bottom')


def points_in_radius(points: np.ndarray, target_point: np.ndarray, threshold: float) -> np.ndarray:
    distances = np.linalg.norm(points - target_point, axis=1)
    selected_points = points[distances < threshold]
    return selected_points


def offset_points(points, offset):
    return points + offset

def normalize_point(point):
    length = math.sqrt(point[0]**2 + point[1]**2)
    if length == 0:
        return np.array([0, 0])  # 或者返回其他特定的值，根据实际需求
    else:
        new_point = point / length
        return new_point


def normalize_points(points):
    # 计算每个点的长度
    lengths = np.linalg.norm(points, axis=1)

    # 获取长度为0的点的索引
    zero_length_indices = np.where(lengths == 0)

    # 对长度不为0的点进行归一化处理
    new_points = points / lengths[:, np.newaxis]

    # 将长度为0的点设置为[0, 0]或者其他特定值
    new_points[zero_length_indices] = [0, 0]  # 或者根据实际需求设置其他值

    return new_points

def v_rotate_points(points):
    rotation_matrix = np.array([[0, -1], [1, 0]])
    rotated_points = np.dot(points, rotation_matrix)
    return rotated_points