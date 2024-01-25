import os.path
import traceback

import imgui
import osmnx as ox
from pympler.asizeof import asizeof
from graphic_module import GraphicManager
from geo import Road, Building, Region
from utils import io_utils, RoadCluster, BuildingCluster, RegionCluster

from gui.icon_module import IconManager, Spinner
from gui import components as imgui_c
from gui import global_var as g
from gui import common

mDataPath = '../data/VirtualEnv/try2.bin'
mData = None
mDataSize = 0
mConstEmptyData = {'version': 'N/A', 'roads': 'N/A', 'buildings': 'N/A', 'regions': 'N/A', 'height': 'N/A'}

mOSMNorth = 37.79
mOSMSouth = 37.78
mOSMEast = -122.41
mOSMWest = -122.43
mOSMGraph = None
mOSMNetworkTypes = ["all_private", "all", "bike", "drive", "drive_service", "walk"]
mOSMCurrentNetworkTypeIdx = 3

mRoadGDFCluster = RoadCluster()
mBuildingGDFCluster = BuildingCluster()
mRegionGDFCluster = RegionCluster()

print('geo page loaded')


def show():
    global mDataPath, mData, mDataSize
    global mOSMNorth, mOSMSouth, mOSMEast, mOSMWest, mOSMGraph, mOSMCurrentNetworkTypeIdx
    imgui.push_id('geo_page')
    if imgui.tree_node('[1] 加载数据', imgui.TREE_NODE_DEFAULT_OPEN):

        expanded, visible = imgui.collapsing_header('[1.1] data->GDFs', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            imgui.push_id('data_path')
            if not mData:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0.4, 0.4, 1)
                imgui.text('请先加载data!')
                imgui.pop_style_color()
            changed, mDataPath = imgui.input_text('', mDataPath)
            imgui_c.tooltip(os.path.abspath(mDataPath))
            imgui.pop_id()
            imgui.same_line()
            if imgui.button('...', width=45 * g.GLOBAL_SCALE):
                mDataPath = io_utils.open_file_window()
            imgui_c.tooltip('打开文件浏览器')
            if imgui.button('LOAD DATA', width=300 * g.GLOBAL_SCALE + 16, height=32 * g.GLOBAL_SCALE):
                Spinner.start('load_data', target=_load_data, args=())
            Spinner.spinner('load_data')
            imgui_c.tooltip('将二进制data加载到内存中')
            if imgui.button('Pop Data'):
                mData = None
                mDataSize = 0
            imgui_c.tooltip('数据转化为GDF后便可以释放了')
            imgui.same_line()
            imgui.text(f'占用内存: {mDataSize:.2f}MB')
            imgui.separator()
            imgui.text('data数据概览:')
            data_to_display = mData if mData else mConstEmptyData
            imgui_c.dict_viewer_component(data_to_display, 'Data', 'keys', 'info',
                                          lambda value: f'count={str(len(value))}' if isinstance(value, list) else str(
                                              value))
            imgui.separator()
            imgui.text('基于data生成GDFs:')
            if not mData:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0.4, 0.4, 1)
                imgui.text('没有data!')
                imgui.pop_style_color()
            if imgui.button('->Roads', 100 * g.GLOBAL_SCALE):
                # Road.data_to_roads(mData)
                Spinner.start('data_to_road', target=Road.data_to_roads, args=(mData,))
            Spinner.spinner('data_to_road')
            imgui.same_line()
            if imgui.button('->Buildings', 100 * g.GLOBAL_SCALE):
                Spinner.start('data_to_building', target=Building.data_to_buildings, args=(mData,))
            Spinner.spinner('data_to_building')
            imgui.same_line()
            if imgui.button('->Regions', 100 * g.GLOBAL_SCALE):
                Spinner.start('data_to_region', target=Region.data_to_regions, args=(mData,))
            Spinner.spinner('data_to_region')
            if imgui.button('->All', 300 * g.GLOBAL_SCALE + 16, 32 * g.GLOBAL_SCALE):
                Spinner.start('data_to_all', target=lambda _: (
                    Road.data_to_roads(mData), Building.data_to_buildings(mData), Region.data_to_regions(mData),GraphicManager.instance.main_texture.clear_cache()),
                              args=(0,))
            Spinner.spinner('data_to_all')

            imgui.text('')
        expanded, visible = imgui.collapsing_header('[1.2] OSM->GDFs', True)
        if expanded:
            imgui.text('使用osmnx下载数据:')
            # _, mOSMNorth = imgui.input_float('North', mOSMNorth)
            # _, mOSMSouth = imgui.input_float('South', mOSMSouth)
            # _, mOSMEast = imgui.input_float('East', mOSMEast)
            # _, mOSMWest = imgui.input_float('West', mOSMWest)
            _, (mOSMNorth, mOSMSouth, mOSMEast, mOSMWest) = imgui.input_float4('NSEW', mOSMNorth, mOSMSouth, mOSMEast, mOSMWest)
            _, mOSMCurrentNetworkTypeIdx = imgui.combo('Network Type', mOSMCurrentNetworkTypeIdx, mOSMNetworkTypes)
            if imgui.button('Download', 260 * g.GLOBAL_SCALE, 32 * g.GLOBAL_SCALE):
                Spinner.start('download_osm', target=
                lambda _: (
                    print('aaa'),
                    Road.from_graph(ox.graph_from_bbox(mOSMNorth, mOSMSouth, mOSMEast, mOSMWest,
                                                       network_type=mOSMNetworkTypes[mOSMCurrentNetworkTypeIdx])),
                    GraphicManager.instance.main_texture.clear_x_y_lim()
                ), args=(0,))
            Spinner.spinner('download_osm')
        imgui.tree_pop()
    if imgui.tree_node('[3] GDF操作工具', imgui.TREE_NODE_DEFAULT_OPEN):

        expanded, visible = imgui.collapsing_header('[2.2] GDFs操作', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            with imgui.begin_tab_bar('geo_op_tab_bar'):
                if imgui.begin_tab_item('Road').selected:
                    imgui.text('选择工具')
                    imgui.text('current selected: 0')
                    mRoadGDFCluster.show_imgui_cluster_editor_button()
                    imgui.text('详细操作')
                    if imgui.tree_node('创建删除'):
                        imgui.tree_pop()
                    if imgui.tree_node('获取查找'):
                        imgui.tree_pop()
                    if imgui.tree_node('编辑修改'):
                        imgui.button('add point to road')
                        imgui.button('add points to road')
                        imgui.button('split road')
                        imgui.button('merge road')
                        if imgui.button('simplify roads'):
                            try:
                                Road.simplify_roads()
                            except:
                                traceback.print_stack()
                        imgui.tree_pop()
                    if imgui.tree_node('绘图相关'):
                        imgui.tree_pop()
                    if imgui.tree_node('类型转换'):
                        imgui.tree_pop()
                    if imgui.tree_node('其他工具'):
                        imgui.tree_pop()
                    imgui.end_tab_item()

                if imgui.begin_tab_item('Building').selected:
                    imgui.text('1. 选择工具')
                    imgui.text('current selected: 0')
                    mBuildingGDFCluster.show_imgui_cluster_editor_button()
                    imgui.text('2. 详细操作')
                    if imgui.tree_node('创建删除'):
                        imgui.tree_pop()
                    if imgui.tree_node('获取查找'):
                        imgui.tree_pop()
                    if imgui.tree_node('编辑修改'):
                        imgui.tree_pop()
                    if imgui.tree_node('绘图相关'):
                        imgui.tree_pop()
                    if imgui.tree_node('类型转换'):
                        imgui.tree_pop()
                    if imgui.tree_node('其他工具'):
                        imgui.tree_pop()
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Region').selected:
                    imgui.text('1. 选择工具')
                    imgui.text('current selected: 0')
                    mRegionGDFCluster.show_imgui_cluster_editor_button()
                    imgui.text('2. 详细操作')
                    if imgui.tree_node('创建删除'):
                        imgui.tree_pop()
                    if imgui.tree_node('获取查找'):
                        imgui.tree_pop()
                    if imgui.tree_node('编辑修改'):
                        imgui.tree_pop()
                    if imgui.tree_node('绘图相关'):
                        imgui.tree_pop()
                    if imgui.tree_node('类型转换'):
                        imgui.tree_pop()
                    if imgui.tree_node('其他工具'):
                        imgui.tree_pop()
                    imgui.end_tab_item()
            imgui.text('')

        imgui.tree_pop()

    if imgui.tree_node('绘图工具', imgui.TREE_NODE_DEFAULT_OPEN):
        imgui.tree_pop()
    imgui.pop_id()


def _load_data():
    global mData, mDataSize
    mData = io_utils.load_data(mDataPath)
    mDataSize = asizeof(mData) / 1024 / 1024
