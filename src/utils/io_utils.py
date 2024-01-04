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


def get_entity_points_auto(entity):
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
def dxf_to_data(path, cache=True, use_cache=True):
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

    # 打开 CAD 文件

    print('reading file...')
    start_time = time.time()
    doc = ezdxf.readfile(path)
    print(f"加载dxf耗时: {(time.time() - start_time)}s ")
    msp = doc.modelspace()
    data = {'version': INFO_VERSION, 'roads': [], 'buildings': [], 'regions': [], 'height': []}
    print('parsing entities...')
    start_time = time.time()
    for entity in msp:
        # ROADS
        if entity.dxf.layer in road_layer_mapper.keys():
            if entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                points = get_entity_points_auto(entity)
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
                points = get_entity_points_auto(entity)
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
                points = get_entity_points_auto(entity)
                region_data = {
                    'points': points,
                    'accessible': region_accessible_mapper[entity.dxf.layer],
                    'type': region_type_mapper[entity.dxf.layer],
                }
                data['regions'].append(region_data)
    print(f"解析耗时: {(time.time() - start_time)}s ")
    print('complete.')
    return data


def _dict_to_xml(dictionary, parent):
    """递归"""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            _dict_to_xml(value, ET.SubElement(parent, key))
        else:
            ET.SubElement(parent, key).text = str(value)


def _xml_to_dict(element):
    """递归"""
    dictionary = {}
    for child in element:
        if child:
            value = _xml_to_dict(child)
        else:
            value = child.text
        if child.tag in dictionary:
            if type(dictionary[child.tag]) is list:
                dictionary[child.tag].append(value)
            else:
                dictionary[child.tag] = [dictionary[child.tag], value]
        else:
            dictionary[child.tag] = value
    return dictionary


def data_to_xml(data: dict, path: str):
    """
    将地图data保存为xml文件
    :param data:
    :param path:
    :return:
    """
    root = ET.Element("data")
    _dict_to_xml(data, root)

    # 创建 ElementTree 对象
    tree = ET.ElementTree(root)

    # 保存为 XML 文件
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f'data wrote to {path}')


def xml_to_data(path: str) -> dict:
    # 从 XML 文件中读取数据
    tree = ET.parse(path)
    root = tree.getroot()
    data = _xml_to_dict(root)
    return data


@timer
def save_data(data, path):
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


if __name__ == "__main__":
    dxf_path = "../../data/和县/现状条件.dxf"
    data = dxf_to_data(dxf_path)
    save_data(data, os.path.join(os.path.dirname(dxf_path), 'data.bin'))
