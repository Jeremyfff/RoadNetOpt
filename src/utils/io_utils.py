import os.path
import pickle
import time

import ezdxf
import numpy as np
import xml.etree.ElementTree as ET
from utils import building_utils, road_utils, INFO_VERSION
from utils import RoadLevel, RoadState, RegionAccessibleType, RegionType, BuildingStyle, BuildingQuality, \
    BuildingMovableType
from utils.common_utils import timer
import tkinter as tk
from tkinter import filedialog

# 指定要提取的图层名称
road_layer_mapper = {
    '车行-主干道': RoadLevel.MAIN,
    '车行-支路': RoadLevel.SECONDARY,
    '车行-次干道': RoadLevel.SECONDARY,
    '车行-街巷': RoadLevel.BRANCH,
    '人行-街巷': RoadLevel.ALLEY
}

road_state_mapper = {
    '车行-主干道': RoadState.RAW,
    '车行-支路': RoadState.RAW,
    '车行-次干道': RoadState.RAW,
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
def load_dxf(path):
    # 打开 CAD 文件
    print('reading file...')
    doc = ezdxf.readfile(path)
    return doc

def get_dxf_layers(doc):
    layers = set()
    msp = doc.modelspace()
    for entity in msp:
        layers.add(entity.dxf.layer)
    return layers
@timer
def dxf_to_data(doc):
    msp = doc.modelspace()
    data = {'version': INFO_VERSION, 'roads': [], 'buildings': [], 'regions': [], 'height': []}
    print('parsing entities...')
    for entity in msp:
        # ROADS
        if entity.dxf.layer in road_layer_mapper.keys():
            if entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                points = _get_entity_points_auto(entity)
                road_data = {
                    'points': points,
                    'level': road_layer_mapper[entity.dxf.layer],
                    'state': road_state_mapper[entity.dxf.layer]
                }
                data['roads'].append(road_data)
        # HEIGHT
        elif entity.dxf.layer == height_layer:
            if entity.dxftype() == 'TEXT':  # 判断实体类型为文本
                # text_content = entity.dxf.text  # 获取文字内容
                insertion_point = entity.dxf.insert
                data['height'].append(insertion_point.xyz)
        # BUILDINGS
        elif entity.dxf.layer in building_style_mapper.keys():
            if (entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE') and entity.is_closed:
                points = _get_entity_points_auto(entity)
                building_data = {
                    'points': points,
                    'style': building_style_mapper[entity.dxf.layer],
                    'movable': building_movable_mapper[entity.dxf.layer],
                    'quality': building_quality_mapper[entity.dxf.layer]
                }
                data['buildings'].append(building_data)
        # REGIONS
        elif entity.dxf.layer in region_accessible_mapper.keys():
            if entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                points = _get_entity_points_auto(entity)
                region_data = {
                    'points': points,
                    'accessible': region_accessible_mapper[entity.dxf.layer],
                    'region_type': region_type_mapper[entity.dxf.layer],
                }
                data['regions'].append(region_data)
    print('complete.')
    return data

def _get_entity_points_auto(entity):
    if entity.dxftype() == 'LWPOLYLINE':
        points = np.array(entity.get_points())
        points = points[:, :2].tolist()
        return points
    elif entity.dxftype() == 'POLYLINE':
        points = []
        for point in entity.points():
            points.append([point.xyz[0], point.xyz[1]])
        return points
    else:
        raise Exception('不支持的类型')

@timer
def save_data(data, path):
    if path == '':
        return
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'wb') as file:
        pickle.dump(data, file)
    print(f'data wrote to {path}')


@timer
def load_data(path):
    with open(path, 'rb') as file:
        data = pickle.load(file)
    return data


def open_file_window(**kwargs):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(**kwargs)
    return file_path

def save_file_window(**kwargs):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfile(**kwargs)
    print(file_path.name)
    return file_path.name

if __name__ == "__main__":
    dxf_path = "../../data/和县/现状条件.dxf"
    dxf_doc = load_dxf(dxf_path)
    data = dxf_to_data(dxf_doc)
    save_data(data, os.path.join(os.path.dirname(dxf_path), 'data.bin'))
