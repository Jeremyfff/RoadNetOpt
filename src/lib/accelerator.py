import clr
import os

import numpy as np

clr.AddReference(os.path.abspath(r'lib/RoadNetOptAccelerator/bin/Debug/RoadNetOptAccelerator'))
from RoadNetOptAccelerator import CAccelerator, RoadAccelerator
from RoadNetOptAccelerator import RoadManager, Road, NodeManager, Node, Common
from RoadNetOptAccelerator import cImGUI

cAccelerator = CAccelerator
cRoadAccelerator = RoadAccelerator

cAccelerator.SetMaxChunks(16)
cAccelerator.SetMinGeoPerChunk(4)

cRoadAccelerator.SetMaxChunks(4)
cRoadAccelerator.SetMinGeoPerChunk(1)

cRoadManager = RoadManager
cNodeManager = NodeManager
cRoad = Road
cNode = Node
cCommon = Common
cRoadType = type(cRoad())
cNodeType = type(cNode())
cGuidType = type(cCommon.GenGuid())
cNull = cCommon.GenNull()
cNullType = type(cNull)
cImGui = cImGUI


def arr_addr_len(arr: np.ndarray, name=""):
    """获取np array的内存地址和长度"""
    if not arr.flags['C_CONTIGUOUS']:
        raise Exception(f'arr {name}  is not contiguous')
    # arr = arr.reshape(-1)
    address = arr.__array_interface__['data'][0]
    length = len(arr)
    return address, length


def arrs_addr_len(*args):
    params = []
    for i, arr in enumerate(args):
        if not arr.flags['C_CONTIGUOUS']:
            raise Exception(f'arr is not contiguous')
        address = arr.__array_interface__['data'][0]
        params.append(address)
        params.append(len(arr))
    return tuple(params)


def int_list_to_cIntArr(int_list: list[int]):
    arr = np.array(int_list, dtype=np.int32)
    cIntArr = cCommon.NumpyToArrayInt(*arrs_addr_len(arr))
    return cIntArr


def coords_to_cCoords(coords: np.ndarray):
    assert len(coords.shape) == 2, '提供的coords数组维度必须为2，例如(n, 2)， 其中n表示点的个数'
    assert coords.shape[1] == 2
    coords_x = coords[:, 0]
    coords_y = coords[:, 1]

    cCoords = cCommon.NumpyToCoords(*arrs_addr_len(coords_x, coords_y))
    return cCoords


def coords_list_to_cCoordsList(coords_list: list[np.ndarray]):
    all_coords = np.vstack(coords_list)
    coords_x = all_coords[:, 0]
    coords_y = all_coords[:, 1]
    first = np.empty(len(coords_list))
    num = np.empty(len(coords_list))
    total = 0
    for i in range(len(coords_list)):
        first[i] = total
        n = len(coords_list[i])
        num[i] = n
        total += n
    params = arrs_addr_len(coords_x, coords_y, first, num)
    cCoordsList = cCommon.NumpyToCoordsList(*params)
    return cCoordsList
