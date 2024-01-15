<<<<<<< Updated upstream
<<<<<<< HEAD
=======
=======
>>>>>>> Stashed changes


import os
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
import time

start_time = time.time()
import imgui
import pygame
from PIL import Image
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl
from OpenGL.GL import *
import threading
import sys
<<<<<<< HEAD
import numpy as np
<<<<<<< Updated upstream
from graphic_module import GraphicManager, create_texture_from_array, update_texture
=======
from utils.common_utils import timer

import numpy as np
import graphic_module
from graphic_module import GraphicManager
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
from geo import Road, Building, Region
=======
import osmnx as ox
import graphic_module
from graphic_module import GraphicManager
from geo import Road, Building, Region
from utils.common_utils import timer

import numpy as np
import osmnx as ox
import graphic_module
from graphic_module import GraphicManager
from geo import Road, Building, Region
>>>>>>> Stashed changes

from utils import io_utils
from utils import graphic_uitls
from utils import RoadLevel, RoadState, BuildingMovableType, BuildingStyle, BuildingQuality, RegionAccessibleType, \
<<<<<<< HEAD
    RegionType
=======
    RegionType, RoadCluster, BuildingCluster, RegionCluster

from gui.icon_module import IconManager, Spinner

<<<<<<< Updated upstream
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
>>>>>>> Stashed changes
from pympler.asizeof import asizeof
from style_module import StyleManager, PlotStyle
import ctypes
# ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放
print(f'import完成，耗时{time.time() - start_time}s')
"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html
"""

LEFT_WINDOW_WIDTH = 400
BOTTOM_WINDOW_HEIGHT = 32

mDxfWindowOpened = False
mInfoWindowOpened = True
mLoggingWindowOpened = False

mImageWindowSize = (0, 0)
mImageWindowPos = (0, 0)
mImageWindowInnerSize = (0, 0)
mImageWindowInnerPos = (0, 0)
mImageWindowMousePos = (0, 0)

mHoveringImageWindow = False
mHoveringInfoSubWindow = False
mHoveringDxfSubWindow = False
mHoveringLoggingSubWindow = False
mHoveringMainTextureSubWindow = False

mSelectedRoads = {}  # 被选中的道路 dict{uid:road}

mDxfPath = r'../data/和县/simplified_data.dxf'
mLoadDxfNextFrame = False
mDxfDoc = None
mDxfLayers = None

mDataPath = '../data/和县/simplified_data.bin'
mData = None
mDataSize = 0
mConstEmptyData = {'version': 'N/A', 'roads': 'N/A', 'buildings': 'N/A', 'regions': 'N/A', 'height': 'N/A'}

mOSMNorth = 37.79
mOSMSouth = 37.78
mOSMEast = -122.41
mOSMWest = -122.43

mOSMNetworkTypes = ["all_private", "all", "bike", "drive", "drive_service", "walk"]
mOSMCurrentNetworkType = "drive"

mOSMGraph = None

mGDFInfo = {}
mGraphicCacheInfo = {}
mTextureInfo = {}

mRoadGDFCluster = {'level': {key: True for key in RoadLevel}, 'state': {key: True for key in RoadState}}
mBuildingGDFCluster = {'movable': {key: True for key in BuildingMovableType},
                       'style': {key: True for key in BuildingStyle}, 'quality': {key: True for key in BuildingQuality}}
mRegionGDFCluster = {'accessible': {key: True for key in RegionAccessibleType},
                     'region_type': {key: True for key in RegionType}}

mRoadDisplayOptions = ['level', 'state']
mCurrentRoadDisplayOption = 0
mBuildingDisplayOptions = ['movable', 'style', 'quality']
mCurrentBuildingDisplayOption = 0
mRegionDisplayOptions = ['accessible', 'quality', 'region_type']
mCurrentRegionDisplayOption = 0

mTmpPopupInputValue = ''
mShowHelpInfo = True
mFrameTime = 0
mFirstLoop = True

<<<<<<< Updated upstream
<<<<<<< HEAD
=======

>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======

>>>>>>> Stashed changes

def imgui_main_window():
    global lst_time, mDxfWindowOpened
    screen_width, screen_height = pygame.display.get_window_size()
    imgui.set_next_window_size(LEFT_WINDOW_WIDTH, screen_height - BOTTOM_WINDOW_HEIGHT)
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    expanded, opened = imgui.begin("路网优化开发工具", False, flags=flags)
    imgui.push_id('main_window')
    if expanded:
        with imgui.begin_tab_bar('main_tab_bar'):
            if imgui.begin_tab_item('Home').selected:
                imgui_home_page()
                imgui.end_tab_item()
            if imgui.begin_tab_item('Geo').selected:
                imgui_geo_page()
                imgui.end_tab_item()
            if imgui.begin_tab_item('Training').selected:
                imgui_training_page()
                imgui.end_tab_item()
            if imgui.begin_tab_item('Tools').selected:
                imgui_tool_page()
                imgui.end_tab_item()
            if imgui.begin_tab_item('Settings').selected:
                imgui_settings_page()
                imgui.end_tab_item()

        # end trees
    imgui.pop_id()
    imgui.end()


def imgui_image_window():
    global mImageWindowSize, mImageWindowPos, mImageWindowInnerSize, mImageWindowInnerPos, mImageWindowMousePos, mHoveringImageWindow
    screen_width, screen_height = pygame.display.get_window_size()
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.set_next_window_size(screen_width - LEFT_WINDOW_WIDTH, screen_height - BOTTOM_WINDOW_HEIGHT)
    imgui.set_next_window_position(LEFT_WINDOW_WIDTH, 0)
    imgui.begin("image window", False, flags=flags)
    mImageWindowPos = (int(imgui.get_window_position()[0]), int(imgui.get_window_position()[1]))
    mImageWindowSize = (int(imgui.get_window_size()[0]), int(imgui.get_window_size()[1]))
    mImageWindowInnerSize = (mImageWindowSize[0] - 16, mImageWindowSize[1] - 34)
    mImageWindowInnerPos = (mImageWindowPos[0] + 8, mImageWindowPos[1] + 34)
    vec1 = (int(imgui.get_mouse_position()[0]), int(imgui.get_mouse_position()[1]))
    vec2 = mImageWindowInnerPos
    mImageWindowMousePos = (vec1[0] - vec2[0], vec1[1] - vec2[1])
    mHoveringImageWindow = is_hovering_window()
    textures_to_delete = set()
    flags = imgui.TAB_BAR_AUTO_SELECT_NEW_TABS | imgui.TAB_BAR_TAB_LIST_POPUP_BUTTON
    with imgui.begin_tab_bar('image_tab_bar', flags=flags):
        for texture in GraphicManager.instance.textures.values():
            if not texture.exposed:
                continue
            selected, opened = imgui.begin_tab_item(texture.name, imgui.TAB_ITEM_TRAILING)
            if selected:
                imgui.image(texture.texture_id, texture.width, texture.height)

                imgui_main_texture_subwindow()
                mTextureInfo['last updated'] = str(texture.last_update_time)
                mTextureInfo['texture size'] = f"{texture.width} , {texture.height}"
                mTextureInfo['x_lim'] = str(texture.x_lim)
                mTextureInfo['y_lim'] = str(texture.y_lim)
                imgui_dict_viewer_component(mTextureInfo, 'texture info', 'key', 'value', None, 800)
                if texture.cached_data is not None:
                    if imgui.button('save'):
                        image = Image.fromarray(texture.cached_data.astype('uint8'))  # 将图像数据缩放到 0-255 范围并转换为 uint8 类型
                        try:
                            image.save(
                                io_utils.save_file_window(defaultextension='.png', filetypes=[('Image File', '.png')]))
                        except:
                            pass
                imgui.end_tab_item()
            if not opened:
                textures_to_delete.add(texture.name)
    imgui.end()

    for name in textures_to_delete:
        GraphicManager.instance.del_texture(name)


def imgui_bottom_window():
    global mInfoWindowOpened, mLoggingWindowOpened
    screen_width, screen_height = pygame.display.get_window_size()
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.set_next_window_size(screen_width, BOTTOM_WINDOW_HEIGHT)
    imgui.set_next_window_position(0, screen_height - BOTTOM_WINDOW_HEIGHT)

    imgui.begin("bottom window", False, flags=flags)
    imgui.text('some information')
    imgui.same_line()
    if imgui.button('信息窗口'):
        mInfoWindowOpened = True
    imgui.same_line()
    if imgui.button('输出窗口'):
        mLoggingWindowOpened = True

    imgui.end()


def imgui_main_texture_subwindow():
    global mCurrentRoadDisplayOption, mCurrentBuildingDisplayOption, mCurrentRegionDisplayOption, mHoveringMainTextureSubWindow
    if mFirstLoop:
        imgui.set_next_window_position(*mImageWindowInnerPos)

    flags = imgui.WINDOW_NO_TITLE_BAR
    expanded, _ = imgui.begin('main texture', False, flags)
    mHoveringMainTextureSubWindow = is_hovering_window()
<<<<<<< Updated upstream
<<<<<<< HEAD
    StyleManager.instance.display_style.show_imgui_style_editor(
        road_style_change_callback=GraphicManager.instance.main_texture.clear_cache,
        building_style_change_callback=None,
        region_style_change_callback=None,
    )

=======
=======
>>>>>>> Stashed changes
    if imgui.image_button(IconManager.instance.icons['paint-fill'], 20, 20):
        imgui.open_popup('display_style_editor')
    if imgui.is_item_hovered():
        imgui.set_tooltip('显示样式设置')
    if imgui.begin_popup('display_style_editor'):
        mHoveringMainTextureSubWindow = True
        StyleManager.instance.display_style.show_imgui_style_editor(
            road_style_change_callback=GraphicManager.instance.main_texture.clear_road_data,
            building_style_change_callback=GraphicManager.instance.main_texture.clear_building_data,
            region_style_change_callback=GraphicManager.instance.main_texture.clear_region_data,
        )
        imgui.end_popup()
    if imgui.image_button(IconManager.instance.icons['stack-fill'], 20,20):
        imgui.open_popup('display_layer_editor')
    if imgui.is_item_hovered():
        imgui.set_tooltip('显示图层设置')
    if imgui.begin_popup('display_layer_editor'):
        mHoveringMainTextureSubWindow = True
        GraphicManager.instance.main_texture.show_imgui_display_editor()
        imgui.end_popup()
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
    imgui.end()


def imgui_dxf_subwindow():
    global mDxfWindowOpened, mDxfPath, mDxfDoc, mLoadDxfNextFrame, mDxfLayers, mHoveringDxfSubWindow

    if mDxfWindowOpened:
        expanded, mDxfWindowOpened = imgui.begin('dxf文件转换工具', True)
        mHoveringDxfSubWindow = is_hovering_window()
        imgui.text('DXF path')
        imgui.push_id('dxf_path')
        changed, mDxfPath = imgui.input_text('', mDxfPath)
        imgui.pop_id()
        imgui.same_line()
        if imgui.button('...'):
            mDxfPath = io_utils.open_file_window()
        if mLoadDxfNextFrame:
            mDxfDoc = io_utils.load_dxf(mDxfPath)
            mDxfLayers = io_utils.get_dxf_layers(mDxfDoc)
            mLoadDxfNextFrame = False
        if imgui.button('Load dxf'):
            imgui.text('loading...')
            mLoadDxfNextFrame = True
        if mDxfDoc is not None:
            imgui.text("dxf loaded")
            if imgui.tree_node('layer mappings[readonly]'):
                imgui.text_wrapped('暂不支持动态更改，请前往utils.io_utils.py编辑修改')
                target_dicts = [io_utils.road_layer_mapper,
                                io_utils.road_state_mapper,
                                io_utils.building_movable_mapper,
                                io_utils.building_style_mapper,
                                io_utils.building_quality_mapper,
                                io_utils.region_accessible_mapper,
                                io_utils.region_type_mapper]
                target_dict_names = ['road_level',
                                     'road_state',
                                     'building_movable',
                                     'building_style',
                                     'building_quality',
                                     'region_accessible',
                                     'region_type']
                for dict_idx in range(len(target_dicts)):
                    target_dict = target_dicts[dict_idx]
                    target_dict_name = target_dict_names[dict_idx]
                    imgui_dict_viewer_treenode_component(target_dict, target_dict_name, 'dxf_layer', target_dict_name,
                                                         value_op=lambda value: str(value).split('.')[-1])
                imgui.tree_pop()
            if imgui.button('convert to data and save'):
                data = io_utils.dxf_to_data(mDxfDoc)
                io_utils.save_data(data, io_utils.save_file_window(defaultextension='.bin',
                                                                   filetypes=[('Binary Files', '.bin')]))
            if imgui.button('release dxf'):
                mDxfDoc = None
        imgui.end()


def imgui_info_subwindow():
    global mInfoWindowOpened, mFrameTime, mHoveringInfoSubWindow
    if mInfoWindowOpened:
        if mFirstLoop:
            window_width = 400
            windows_height = 400
            screen_width, screen_height = pygame.display.get_window_size()
            imgui.set_next_window_position(screen_width - window_width, 32)
            imgui.set_next_window_size(window_width, windows_height)
        expanded, mInfoWindowOpened = imgui.begin('信息窗口', True)
        mHoveringInfoSubWindow = is_hovering_window()
        if mFrameTime == 0:
            mFrameTime += 1e-4
        imgui.text(f'fps {(1.0 / mFrameTime):.1f}')
        imgui.separator()
        imgui.text('gdf信息:')
        update_mGDFInfo()
        imgui_dict_viewer_component(mGDFInfo, 'dgf info', 'GDF Type', 'count', lambda value: str(value))

        imgui.text(f'selected roads {len(mSelectedRoads)}')

        imgui.text('')
        imgui.text('图像缓冲区:')
        mGraphicCacheInfo[
            'cached highlighted img'] = GraphicManager.instance.main_texture.cached_highlighted_road_data is not None
        mGraphicCacheInfo['cached road img'] = GraphicManager.instance.main_texture.cached_road_data is not None
        mGraphicCacheInfo['cached road idx img'] = GraphicManager.instance.main_texture.cached_road_idx is not None
        imgui_dict_viewer_component(mGraphicCacheInfo, 'graphic cache info', 'cache type', 'has data',
                                    lambda value: str(value))
        imgui.end()


def imgui_logging_subwindow():
    global mLoggingWindowOpened, mHoveringLoggingSubWindow
    if mLoggingWindowOpened:
        expanded, mLoggingWindowOpened = imgui.begin('日志窗口', True)
        mHoveringLoggingSubWindow = is_hovering_window()
        imgui.text('功能待实现')
        imgui.end()


def imgui_home_page():
    imgui.push_id('home_page')
    imgui.text("welcome to road net opt")
    imgui.text_wrapped("交互式街区路网织补工具")
    imgui.text("""
  _____                 _ _   _      _    ____        _   
 |  __ \               | | \ | |    | |  / __ \      | |  
 | |__) |___   __ _  __| |  \| | ___| |_| |  | |_ __ | |_ 
 |  _  // _ \ / _` |/ _` | . ` |/ _ \ __| |  | | '_ \| __|
 | | \ \ (_) | (_| | (_| | |\  |  __/ |_| |__| | |_) | |_ 
 |_|  \_\___/ \__,_|\__,_|_| \_|\___|\__|\____/| .__/ \__|
                                               | |        
                                               |_|       
    """)
    imgui.text('version:0.1')
    imgui.text('冯以恒， 武文忻， 邱淑冰')
    imgui.pop_id()


def _load_data():
    global mData, mDataSize
    mData = io_utils.load_data(mDataPath)
    mDataSize = asizeof(mData) / 1024 / 1024


def imgui_geo_page():
    global mDxfWindowOpened, mDataPath, mData, mDataSize
    global mOSMNorth, mOSMSouth, mOSMEast, mOSMWest, mOSMGraph
    imgui.push_id('geo_page')

    if imgui.tree_node('[1] DXF工具'):
        if imgui.button('DXF转换工具'):
            mDxfWindowOpened = True
        if imgui.is_item_hovered():
            imgui.set_tooltip('dxf转换工具能够将dxf文件的内容转换为本软件所需的二进制文件交换格式')
        imgui.tree_pop()
    if imgui.tree_node('[2] 数据加载工具', imgui.TREE_NODE_DEFAULT_OPEN):

        expanded, visible = imgui.collapsing_header('[2.1] data->GDFs', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            imgui.push_id('data_path')
            if not mData:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0.4, 0.4, 1)
                imgui.text('请先加载data!')
                imgui.pop_style_color()
            changed, mDataPath = imgui.input_text('', mDataPath)
            imgui.pop_id()
            imgui.same_line()
            if imgui.button('...'):
                mDataPath = io_utils.open_file_window()
            if imgui.button('load data'):

                Spinner.start('load_data', target=_load_data, args=())
            Spinner.spinner('load_data')
            if imgui.is_item_hovered():
                imgui.set_tooltip('将二进制data加载到内存中')
            imgui.same_line()
            if imgui.button('pop data'):
                mData = None
                mDataSize = 0
            imgui.same_line()
            imgui.text(f'占用内存: {mDataSize:.2f}MB')
            imgui.separator()
            imgui.text('data数据概览:')
            data_to_display = mData if mData else mConstEmptyData
            imgui_dict_viewer_component(data_to_display, 'Data', 'keys', 'info',
                                        lambda value: f'count={str(len(value))}' if isinstance(value, list) else str(
                                            value))
            imgui.separator()
            imgui.text('基于data生成GDFs')
            if not mData:
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0.4, 0.4, 1)
                imgui.text('没有data!')
                imgui.pop_style_color()
            if imgui.button('->Roads', 100):
                # Road.data_to_roads(mData)
                Spinner.start('data_to_road', target=Road.data_to_roads, args=(mData,))
            Spinner.spinner('data_to_road')
            imgui.same_line()
            if imgui.button('->Buildings', 100):
                Spinner.start('data_to_building', target=Building.data_to_buildings, args=(mData,))
            Spinner.spinner('data_to_building')
            imgui.same_line()
            if imgui.button('->Regions', 100):
                Spinner.start('data_to_region', target=Region.data_to_regions, args=(mData,))
            Spinner.spinner('data_to_region')
            if imgui.button('->All', 316, 32):
                Spinner.start('data_to_all', target=lambda _: (
                    Road.data_to_roads(mData), Building.data_to_buildings(mData), Region.data_to_regions(mData)),
                                    args=(0,))
            Spinner.spinner('data_to_all')

            imgui.text('')
        expanded, visible = imgui.collapsing_header('[2.2] osm->GDFs', True)
        if expanded:
            _, mOSMNorth = imgui.input_float('north', mOSMNorth)
            _, mOSMSouth = imgui.input_float('south', mOSMSouth)
            _, mOSMEast = imgui.input_float('east', mOSMEast)
            _, mOSMWest = imgui.input_float('west', mOSMWest)
            if imgui.button('download'):
                Spinner.start('download_osm', target=
                lambda _:(
                    Road.from_graph(ox.graph_from_bbox(mOSMNorth, mOSMSouth, mOSMEast, mOSMWest, network_type='drive')),
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
                    imgui_item_selector_component('road level cluster', mRoadGDFCluster['level'])
                    imgui_item_selector_component('road state cluster', mRoadGDFCluster['state'])
                    imgui.text('详细操作')
                    if imgui.tree_node('创建删除'):
                        imgui.button('add road')
                        imgui.button('delete road')
                        imgui.tree_pop()
                    if imgui.tree_node('获取查找'):
                        imgui.button('get road by uid')
                        imgui.button('get road by index')
                        imgui.button('get roads by attr and value')
                        imgui.button('get nodes by attr and value')
                        imgui.button('get first road')
                        imgui.button('get last road')
                        imgui.button('get all roads')
                        imgui.button('get roads by node')
                        imgui.tree_pop()
                    if imgui.tree_node('编辑修改'):
                        imgui.button('add point to road')
                        imgui.button('add points to road')
                        imgui.button('split road')
                        imgui.button('merge road')
                        imgui.button('simplify roads')

                        imgui.tree_pop()
                    if imgui.tree_node('绘图相关'):
                        imgui.button('plot roads')
                        imgui.button('plot all')
                        imgui.tree_pop()
                    if imgui.tree_node('类型转换'):
                        imgui.button('to graph')
                        imgui.button('from graph')
                        imgui.button('to data')
                        imgui.button('from data')
                        imgui.tree_pop()
                    if imgui.tree_node('其他工具'):
                        imgui.button('quick roads')
                        imgui.button('show info')
                        imgui.tree_pop()
                    imgui.end_tab_item()

                if imgui.begin_tab_item('Building').selected:
                    imgui.text('1. 选择工具')
                    imgui.text('current selected: 0')
                    imgui_item_selector_component('building movable cluster', mBuildingGDFCluster['movable'])
                    imgui_item_selector_component('building style cluster', mBuildingGDFCluster['style'])
                    imgui_item_selector_component('building quality cluster', mBuildingGDFCluster['quality'])
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
                    imgui_item_selector_component('region accessible cluster', mRegionGDFCluster['accessible'])
                    imgui_item_selector_component('region type cluster', mRegionGDFCluster['region_type'])
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
        expanded, visible = imgui.collapsing_header('常规绘图', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            imgui.text('plotting')
            if imgui.button('plot all roads'):
                GraphicManager.instance.plot_to('roads', Road.get_all_roads())
            imgui.same_line()
            if imgui.button('plot all buildings'):
                GraphicManager.instance.plot_to('buildings', Building.get_all_buildings())
            imgui.same_line()
            if imgui.button('plot all regions'):
                GraphicManager.instance.plot_to('regions', Region.get_all_regions())

            if imgui.button('plot all gdf'):
                GraphicManager.instance.plot_to('all',
                                                [Road.get_all_roads(), Building.get_all_buildings(),
                                                 Region.get_all_regions()])

            if imgui.button('plot by idx'):
                GraphicManager.instance.plot_to2('roads', Road.plot_using_idx, roads=Road.get_all_roads())
        expanded, visible = imgui.collapsing_header('使用cluster绘图', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            if imgui.button('plot roads by cluster'):
                uid_sets_by_attr = []
                cluster = mRoadGDFCluster
                for attr in cluster:
                    gdfs = []
                    for key in cluster[attr]:
                        if cluster[attr][key]:
                            _gdfs = Road.get_roads_by_attr_and_value(attr, key)
                            gdfs.append(_gdfs)
                    gdf = pd.concat(gdfs, ignore_index=False)
                    uid_sets_by_attr.append(set(gdf.index))
                common_uid = list(set.intersection(*uid_sets_by_attr))
                GraphicManager.instance.plot_to('roads', Road.get_all_roads().loc[common_uid])

            if imgui.button('plot buildings by cluster'):
                uid_sets_by_attr = []
                cluster = mBuildingGDFCluster
                for attr in cluster:
                    gdfs = []
                    for key in cluster[attr]:
                        if cluster[attr][key]:
                            _gdfs = Building.get_buildings_by_attr_and_value(attr, key)
                            gdfs.append(_gdfs)
                    gdf = pd.concat(gdfs, ignore_index=False)
                    uid_sets_by_attr.append(set(gdf.index))
                common_uid = list(set.intersection(*uid_sets_by_attr))
                GraphicManager.instance.plot_to('buildings', Building.get_all_buildings().loc[common_uid])

            if imgui.button('plot regions by cluster'):
                uid_sets_by_attr = []
                cluster = mRegionGDFCluster
                for attr in cluster:
                    gdfs = []
                    for key in cluster[attr]:
                        if cluster[attr][key]:
                            _gdfs = Region.get_regions_by_attr_and_value(attr, key)
                            gdfs.append(_gdfs)
                    gdf = pd.concat(gdfs, ignore_index=False)
                    uid_sets_by_attr.append(set(gdf.index))
                common_uid = list(set.intersection(*uid_sets_by_attr))
                GraphicManager.instance.plot_to('regions', Region.get_all_regions().loc[common_uid])

        expanded, visible = imgui.collapsing_header('其他', True, imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:
            if imgui.button('update main'):
                update_main_graphic()
            if imgui.button('show cached road data'):
                GraphicManager.instance.bilt_to('cached road data',
                                                GraphicManager.instance.main_texture.cached_road_data)
            if imgui.button('show cached road idx data'):
                GraphicManager.instance.bilt_to('cached road idx data',
                                                GraphicManager.instance.main_texture.cached_road_idx)
            if imgui.button('show cached highlighted road data'):
                GraphicManager.instance.bilt_to('cached highlighted road data',
                                                GraphicManager.instance.main_texture.cached_highlighted_road_data)
        imgui.tree_pop()
    imgui.pop_id()


def imgui_training_page():
    imgui.push_id('agent_op')
    if imgui.tree_node('agent op'):
        imgui.tree_pop()
    imgui.pop_id()


def imgui_tool_page():
    pass


def imgui_settings_page():
    imgui.show_style_selector('style selector')
    if imgui.tree_node('graphic settings'):
        imgui.text('graphic textures')
        imgui.listbox('', 0, [texture.name for texture in GraphicManager.instance.textures.values()])
        imgui_popup_modal_input_ok_cancel_component('_add_texture', 'add texture', 'name?',
                                                    'please type in texture name',
                                                    lambda name: GraphicManager.instance.get_or_create_texture(name))
        imgui.tree_pop()
    if imgui.tree_node('style settings'):
        imgui.show_style_editor()
        imgui.tree_pop()
    if imgui.button('show user guide'):
        imgui.show_user_guide()
    if imgui.button('show demo window'):
        imgui.show_demo_window()
    if imgui.button('show about window'):
        imgui.show_about_window()


def update_mGDFInfo():
    global mGDFInfo
    mGDFInfo['Roads'] = len(Road.get_all_roads())
    mGDFInfo['Buildings'] = len(Building.get_all_buildings())
    mGDFInfo['Regions'] = len(Region.get_all_regions())


def imgui_dict_viewer_component(target_dict: dict, dict_name, key_name, value_name, value_op=None, width: float = 0):
    if imgui.begin_table(dict_name, 2, outer_size_width=width):
        imgui.table_setup_column(key_name)
        imgui.table_setup_column(value_name)
        imgui.table_headers_row()
        for key in target_dict.keys():
            imgui.table_next_row()
            imgui.table_next_column()
            imgui.text(str(key))
            imgui.table_next_column()
            value = target_dict[key]
            if value_op is not None:
                value = value_op(value)
            imgui.text(value)
        imgui.end_table()


def imgui_dict_viewer_treenode_component(target_dict, dict_name, key_name, value_name, value_op=None):
    if imgui.tree_node(dict_name, flags=imgui.TREE_NODE_DEFAULT_OPEN):
        imgui_dict_viewer_component(target_dict, dict_name, key_name, value_name, value_op)
        imgui.tree_pop()


<<<<<<< Updated upstream
def imgui_item_selector_component(label, dict):
    if imgui.button(label):
        imgui.open_popup(f'{label} selector')
    if imgui.begin_popup(f'{label} selector'):
        for key in dict:
            opened, dict[key] = imgui.selectable(str(key), dict[key])
        imgui.end_popup()


=======
>>>>>>> Stashed changes
def imgui_popup_modal_input_ok_cancel_component(id, button_label, title, content, ok_callback):
    global mTmpPopupInputValue
    imgui.push_id(f'{id}')
    if imgui.button(button_label):
        imgui.open_popup(title)
    if imgui.begin_popup_modal(title).opened:
        imgui.text(content)
        changed, mTmpPopupInputValue = imgui.input_text('', mTmpPopupInputValue)
        imgui.separator()
        if imgui.button('ok'):
            ok_callback(mTmpPopupInputValue)
            mTmpPopupInputValue = ''
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button('cancel'):
            imgui.close_current_popup()
        imgui.end_popup()
    imgui.pop_id()




<<<<<<< Updated upstream
<<<<<<< HEAD
def imgui_spinner(name, width=20, height=20):
    if name not in mSpinStartTime:
        return
    if not mSpinThread[name].is_alive():
        imgui_end_spinner(name)
        return
    start_time = mSpinStartTime[name]
    t = (time.time() - start_time) % SPIN_TIME / SPIN_TIME
    idx = int(t * SPIN_ANI_FRAME)
    if idx != mSpinLastIdx[name]:
        update_texture(mSpinTextureId[name], mSpinImageArray[idx])
        mSpinLastIdx[name] = idx
    imgui.same_line()
    imgui.image(mSpinTextureId[name], width, height)


def imgui_start_spinner(name, target, args):
    mSpinStartTime[name] = time.time()
    mSpinLastIdx[name] = 0
    mSpinTextureId[name] = create_texture_from_array(mSpinImageArray[0])
    thread = threading.Thread(target=target, args=args)
    mSpinThread[name] = thread
    thread.start()


def imgui_end_spinner(name):
    mSpinStartTime.pop(name)
    mSpinLastIdx.pop(name)
    mSpinTextureId.pop(name)
    mSpinThread.pop(name)


def imgui_init_spinner():
    global mSpinImageArray
    mSpinImageArray = []
    original_image = Image.open("../textures/spinner_light.png")
    # 对图像进行旋转操作
    for i in range(SPIN_ANI_FRAME):
        rotated_image = original_image.rotate(360 / SPIN_ANI_FRAME * i, expand=False, fillcolor=(0, 0, 0, 0))
        mSpinImageArray.append(np.array(rotated_image))
=======
>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======
>>>>>>> Stashed changes


def update_main_graphic():
    global mSelectedRoads
    if imgui.is_key_pressed(imgui.KEY_ESCAPE):
        if len(mSelectedRoads) > 0:
            print('[GUI][update_main_graphic] clear highlight data')
            GraphicManager.instance.main_texture.clear_highlight_data()
            mSelectedRoads = {}
    if imgui.is_key_pressed(imgui.KEY_DELETE):
        print('[GUI][update_main_graphic] redraw all')
        GraphicManager.instance.main_texture.clear_cache()

    if imgui.is_mouse_clicked(
            imgui.MOUSE_BUTTON_LEFT) and mHoveringImageWindow and not mHoveringMainTextureSubWindow and not mHoveringInfoSubWindow and not mHoveringDxfSubWindow:
        on_road, idx = GraphicManager.instance.main_texture.on_left_mouse_click(mImageWindowMousePos)
        if on_road:
            try:
                road = Road.get_road_by_index(idx)
                uid = road['uid']
                mSelectedRoads[uid] = road
            except:
                pass

    GraphicManager.instance.main_texture.update(window_size=mImageWindowSize,
                                                selected_roads=mSelectedRoads)


def is_hovering_window():
    _min = imgui.get_window_position()
    _size = imgui.get_window_size()
    _max = (_min[0] + _size[0], _min[1] + _size[1])
    return imgui.is_mouse_hovering_rect(_min[0], _min[1], _max[0], _max[1])


def init():
    pass

if __name__ == "__main__":
    pygame.init()
    size = (1920, 1080)
    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption('road net opt window')

    imgui.create_context()
    impl = PygameRenderer()




    io = imgui.get_io()
    io.display_size = size
    font_scaling_factor = 1
    font_size_in_pixels = 16
    chinese_font = io.fonts.add_font_from_file_ttf(
        "../fonts/Unifont.ttf", font_size_in_pixels * font_scaling_factor,
        glyph_ranges=io.fonts.get_glyph_ranges_chinese_full()
    )
    io.font_global_scale /= font_scaling_factor
    impl.refresh_font_texture()
    imgui.style_colors_dark()
    imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.10, 0.10, 0.10, 1.00)
    imgui.push_style_color(imgui.COLOR_BORDER, 0.32, 0.32, 0.32, 0.50)
    imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, 0.30, 0.30, 0.30, 0.54)
    imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND, 0.21, 0.21, 0.21, 1.00)
    imgui.push_style_color(imgui.COLOR_BUTTON, 0.43, 0.43, 0.43, 0.40)
    imgui.push_style_color(imgui.COLOR_HEADER, 0.55, 0.55, 0.55, 0.31)
    imgui.push_style_color(imgui.COLOR_SEPARATOR, 0.54, 0.54, 0.54, 0.50)
    imgui.push_style_color(imgui.COLOR_TAB, 0.32, 0.32, 0.32, 0.86)
    imgui.push_style_color(imgui.COLOR_TAB_HOVERED, 0.25, 0.61, 1.00, 0.80)
    imgui.push_style_color(imgui.COLOR_TAB_ACTIVE, 0.20, 0.41, 0.64, 1.00)

    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 8)
    imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 4)

<<<<<<< Updated upstream
<<<<<<< HEAD
    imgui_init_spinner()
=======

>>>>>>> 8f55c28 (Merge branch 'main' of https://github.com/Jeremyfff/RoadNetOpt)
=======

>>>>>>> Stashed changes
    graphic_manager = GraphicManager()
    icon_manager = IconManager()
    Spinner.init(True)

    lst_time = time.time()
    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            impl.process_event(event)
        impl.process_inputs()
        # update graphic

        update_main_graphic()

        # draw imgui windows
        imgui.new_frame()
        with imgui.font(chinese_font):
            # put your windows here
            imgui_image_window()
            imgui_main_window()
            imgui_bottom_window()
            imgui_dxf_subwindow()
            imgui_info_subwindow()
            imgui_logging_subwindow()

        mFrameTime = (time.time() - lst_time)
        lst_time = time.time()
        mFirstLoop = False

        # render and display
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()
