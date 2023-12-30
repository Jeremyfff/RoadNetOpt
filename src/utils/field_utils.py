from scipy.spatial import cKDTree
from sklearn.preprocessing import MinMaxScaler


class FieldOverlayMode(enumerate):
    ADD = 0
    MUL = 1


def distance_field(points, point_cloud):
    tree = cKDTree(point_cloud)  # 构建KD树
    distances, indices = tree.query(points, k=1)
    return distances


def normalize_field(values):
    normalized_values = MinMaxScaler().fit_transform(values.reshape(-1, 1)).reshape(-1)
    return normalized_values
