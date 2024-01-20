import os.path
import pickle
import ezdxf
import numpy as np
from utils import INFO_VERSION
from utils import RoadLevel, RoadState, RegionAccessibleType, RegionType, BuildingStyle, BuildingQuality, \
    BuildingMovableType
from utils.common_utils import timer
import tkinter as tk
from tkinter import filedialog

# 指定要提取的图层名称
road_layer_mapper = {
    '车行-主干道': RoadLevel.TRUNK,
    '车行-次干道': RoadLevel.PRIMARY,
    '车行-支路': RoadLevel.SECONDARY,
    '车行-街巷': RoadLevel.TERTIARY,
    '人行-街巷': RoadLevel.FOOTWAY
}

road_state_mapper = {
    '车行-主干道': RoadState.RAW,
    '车行-次干道': RoadState.RAW,
    '车行-支路': RoadState.RAW,
    '车行-街巷': RoadState.RAW,
    '人行-街巷': RoadState.RAW
}
height_layer = '高程点'

building_style_mapper = {
    'DX-地形': BuildingStyle.NORMAL,
    '000历史建筑': BuildingStyle.HISTORICAL,
    '000文保单位': BuildingStyle.HERITAGE,
}
building_movable_mapper = {
    'DX-地形': BuildingMovableType.UNDEFINED,
    '000历史建筑': BuildingMovableType.NONDEMOLISHABLE,
    '000文保单位': BuildingMovableType.NONDEMOLISHABLE,
}
building_quality_mapper = {
    'DX-地形': BuildingQuality.UNDEFINED,
    '000历史建筑': BuildingQuality.UNDEFINED,
    '000文保单位': BuildingQuality.UNDEFINED,
}

region_accessible_mapper = {
    '000-封闭小区边界线': RegionAccessibleType.INACCESSIBLE,
    'XZ-E1': RegionAccessibleType.INACCESSIBLE,
    '外水E1': RegionAccessibleType.INACCESSIBLE,
}
region_type_mapper = {
    '000-封闭小区边界线': RegionType.ARTIFICIAL,
    'XZ-E1': RegionType.WATER,
    '外水E1': RegionType.WATER
}


@timer
def load_dxf(_path):
    # 打开 CAD 文件
    print('reading file...')
    _doc = ezdxf.readfile(_path)
    return _doc


def get_dxf_layers(_doc):
    _layers = set()
    _msp = _doc.modelspace()
    for _entity in _msp:
        _layers.add(_entity.dxf.layer)
    return _layers


@timer
def dxf_to_data(_doc):
    _msp = _doc.modelspace()
    _data = {'version': INFO_VERSION, 'roads': [], 'buildings': [], 'regions': [], 'height': []}
    print('parsing entities...')
    for _entity in _msp:
        # ROADS
        if _entity.dxf.layer in road_layer_mapper.keys():
            if _entity.dxftype() == 'LWPOLYLINE' or _entity.dxftype() == 'POLYLINE' or _entity.dxftype() == 'LINE':
                _points = _get_entity_points_auto(_entity)
                _road_data = {
                    'points': _points,
                    'level': road_layer_mapper[_entity.dxf.layer],
                    'state': road_state_mapper[_entity.dxf.layer]
                }
                _data['roads'].append(_road_data)
        # HEIGHT
        elif _entity.dxf.layer == height_layer:
            if _entity.dxftype() == 'TEXT':  # 判断实体类型为文本
                # text_content = entity.dxf.text  # 获取文字内容
                _insertion_point = _entity.dxf.insert
                _data['height'].append(_insertion_point.xyz)
        # BUILDINGS
        elif _entity.dxf.layer in building_style_mapper.keys():
            if (_entity.dxftype() == 'LWPOLYLINE' or _entity.dxftype() == 'POLYLINE') and _entity.is_closed:
                _points = _get_entity_points_auto(_entity)
                _building_data = {
                    'points': _points,
                    'style': building_style_mapper[_entity.dxf.layer],
                    'movable': building_movable_mapper[_entity.dxf.layer],
                    'quality': building_quality_mapper[_entity.dxf.layer]
                }
                _data['buildings'].append(_building_data)
        # REGIONS
        elif _entity.dxf.layer in region_accessible_mapper.keys():

            if _entity.dxftype() == 'LWPOLYLINE' or _entity.dxftype() == 'POLYLINE':
                _points = _get_entity_points_auto(_entity)
                _region_data = {
                    'points': _points,
                    'accessible': region_accessible_mapper[_entity.dxf.layer],
                    'region_type': region_type_mapper[_entity.dxf.layer],
                }
                _data['regions'].append(_region_data)
    print('complete.')
    return _data


def _get_entity_points_auto(_entity):
    if _entity.dxftype() == 'LWPOLYLINE':
        _points = np.array(_entity.get_points())
        _points = _points[:, :2].tolist()
        return _points
    elif _entity.dxftype() == 'POLYLINE':
        _points = []
        for _pt in _entity.points():
            _points.append([_pt.xyz[0], _pt.xyz[1]])
        return _points
    elif _entity.dxftype() == 'LINE':

        return [(_entity.dxf.start.xyz[0], _entity.dxf.start.xyz[1]),
                (_entity.dxf.end.xyz[0], _entity.dxf.end.xyz[1])]
    else:
        raise Exception('不支持的类型')



def save_data(_data, _path):
    if _path == '' or _path is None:
        return
    if not os.path.exists(os.path.dirname(_path)):
        os.makedirs(os.path.dirname(_path))
    with open(_path, 'wb') as f:
        pickle.dump(_data, f)
    print(f'data wrote to {_path}')



def load_data(_path):
    with open(_path, 'rb') as f:
        _data = pickle.load(f)
    if _data['version'] != INFO_VERSION:
        print(f"data数据版本（ {_data['version']} ）与现有版本({INFO_VERSION})不匹配，可能导致未知错误，请更新data")
    return _data


def open_file_window(**kwargs):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(**kwargs)
    return file_path


def save_file_window(**kwargs):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfile(**kwargs)
    if file_path is None:
        return None
    print(file_path.name)
    return file_path.name


if __name__ == "__main__":
    dxf_path = "../../data/和县/excluded/现状条件.dxf"
    dxf_doc = load_dxf(dxf_path)
    data = dxf_to_data(dxf_doc)
    save_data(data, os.path.join(os.path.dirname(dxf_path), 'data.bin'))
