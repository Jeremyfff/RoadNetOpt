import time
import imgui
import pandas as pd
import pygame
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl

import sys
import numpy as np
from graphic_module import GraphicManager
from geo import Road, Building, Region
from utils import io_utils
from utils import RoadLevel, RoadState, BuildingMovableType, BuildingStyle, BuildingQuality, RegionAccessibleType, RegionType
import ctypes

# ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放

"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html
"""
mMainWindowWidth = 400
mMainWindowHeight = 800
mDxfPath = r'D:/M.Arch/2024Spr/RoadNetworkOptimization/RoadNetOpt/data/和县/simplified_data.dxf'
mLoadDxfNextFrame = False
mDxfDoc = None
mDxfLayers = None

mDataPath = 'D:/M.Arch/2024Spr/RoadNetworkOptimization/RoadNetOpt/data/和县/simplified_data.bin'
mData = None
mConstEmptyData = {'version' : 'N/A', 'roads': 'N/A', 'buildings':'N/A', 'regions':'N/A', 'height':'N/A'}
mGDFData = {}
mRoadGDFCluster = {'level':{key: True for key in RoadLevel}, 'state':{key :True for key in RoadState}}
mBuildingGDFCluster = {'movable':{key:True for key in BuildingMovableType}, 'style':{key:True for key in BuildingStyle}, 'quality':{key:True for key in BuildingQuality}}
mRegionGDFCluster = {'accessible':{key:True for key in RegionAccessibleType}, 'region_type':{key:True for key in RegionType}}

mTmpPopupInputValue = ''




def imgui_image_window():
    textures_to_delete = set()
    for texture in graphic_manager.textures.values():
        if texture.name == 'main':
            flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOUSE_INPUTS
            imgui.set_next_window_size(*pygame.display.get_window_size())
            imgui.set_next_window_position(0, 0)
        else:
            flags = imgui.WINDOW_NO_RESIZE
        expanded, opened = imgui.begin(f"{texture.name}",True, flags=flags)
        imgui.image(texture.texture_id, texture.width, texture.height)
        imgui.text(f'(last updated:{texture.last_update_time})')
        imgui.end()
        if not opened:
            textures_to_delete.add(texture.name)
    for name in textures_to_delete:
        graphic_manager.del_texture(name)


def imgui_main_window():
    global lst_time
    # imgui.set_next_window_size(300, 600)
    expanded, opened = imgui.begin("路网优化开发工具", True)
    imgui.push_id('main_window')
    if expanded:

        frame_time = (time.time() - lst_time)
        lst_time = time.time()
        if frame_time == 0:
            frame_time += 1e-5
        imgui.text(f'fps {(1.0 / frame_time):.1f}')
        # put your trees here
        imgui_dxf_op_tree()
        imgui_geo_op_tree()
        imgui_agent_op_tree()
        imgui_graphic_tree()
        # end trees
    imgui.pop_id()
    imgui.end()


def imgui_dxf_op_tree():
    global mDxfPath, mDxfDoc, mLoadDxfNextFrame, mDxfLayers
    imgui.push_id('dxf_op')
    if imgui.tree_node('dxf文件转换工具'):
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
        imgui.tree_pop()
    imgui.pop_id()


def imgui_dict_viewer_component(target_dict: dict, dict_name, key_name, value_name, value_op=None):
    if imgui.begin_table(dict_name, 2):
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


def imgui_geo_op_tree():
    global mDataPath, mData
    imgui.push_id('geo_op')
    if imgui.tree_node('几何体工具'):

        if imgui.collapsing_header('data导入工具'):
            imgui.push_id('data_path')
            changed, mDataPath = imgui.input_text('', mDataPath)
            imgui.pop_id()
            imgui.same_line()
            if imgui.button('...'):
                mDataPath = io_utils.open_file_window()
            if imgui.button('load data'):
                mData = io_utils.load_data(mDataPath)

            imgui.text('data数据概览:')
            data_to_display = mData if mData else mConstEmptyData
            imgui_dict_viewer_component(data_to_display, 'Data', 'keys', 'info',
                                        lambda value: f'count={str(len(value))}' if isinstance(value, list) else str(
                                            value))
            if mData:
                imgui.text('data to gdfs')
                if imgui.button('data to roads'):
                    Road.data_to_roads(mData)
                imgui.same_line()
                if imgui.button('data to buildings'):
                    Building.data_to_buildings(mData)
                imgui.same_line()
                if imgui.button('data to regions'):
                    Region.data_to_regions(mData)
                if imgui.button('data to gdfs'):
                    Road.data_to_roads(mData)
                    Building.data_to_buildings(mData)
                    Region.data_to_regions(mData)

        if imgui.collapsing_header('gdf操作'):
            imgui.text('gdf信息:')
            update_mGDFData()
            imgui_dict_viewer_component(mGDFData, 'dgf info', 'GDF Type', 'count', lambda value: str(value))

            imgui_item_selector_component('road level cluster', mRoadGDFCluster['level'])
            imgui.same_line()
            imgui_item_selector_component('road state cluster', mRoadGDFCluster['state'])

            imgui_item_selector_component('building movable cluster', mBuildingGDFCluster['movable'])
            imgui_item_selector_component('building style cluster', mBuildingGDFCluster['style'])
            imgui_item_selector_component('building quality cluster', mBuildingGDFCluster['quality'])

            imgui_item_selector_component('region accessible cluster', mRegionGDFCluster['accessible'])
            imgui_item_selector_component('region type cluster', mRegionGDFCluster['region_type'])


            if imgui.button('plot all roads'):
                graphic_manager.plot_to('roads', Road.get_all_roads())
            imgui.same_line()
            if imgui.button('plot all buildings'):
                graphic_manager.plot_to('buildings', Building.get_all_buildings())
            imgui.same_line()
            if imgui.button('plot all regions'):
                graphic_manager.plot_to('regions', Region.get_all_regions())

            if imgui.button('plot all gdf'):
                graphic_manager.plot_to('all', [Road.get_all_roads(), Building.get_all_buildings(), Region.get_all_regions()])


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
                graphic_manager.plot_to('roads', Road.get_all_roads().loc[common_uid])

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
                graphic_manager.plot_to('buildings', Building.get_all_buildings().loc[common_uid])

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
                graphic_manager.plot_to('regions', Region.get_all_regions().loc[common_uid])

            if imgui.button('update main'):
                graphic_manager.update_main()

        imgui.tree_pop()
    imgui.pop_id()

def update_mGDFData():
    global mGDFData
    mGDFData['Roads'] = len(Road.get_all_roads())
    mGDFData['Buildings'] = len(Building.get_all_buildings())
    mGDFData['Regions'] = len(Region.get_all_regions())

def imgui_agent_op_tree():
    imgui.push_id('agent_op')
    if imgui.tree_node('agent op'):
        imgui.tree_pop()
    imgui.pop_id()
def imgui_graphic_tree():
    imgui.push_id('graphic')
    if imgui.tree_node('graphic'):
        imgui.text('graphic textures')
        imgui.listbox('', 0, [texture.name for texture in graphic_manager.textures.values()])
        imgui_popup_modal_input_ok_cancel_component('_add_texture', 'add texture', 'name?',
                                                    'please type in texture name',
                                                    lambda name: graphic_manager.get_or_create_texture(name))
        imgui.tree_pop()
    imgui.pop_id()

def imgui_item_selector_component(label, dict):
    if imgui.button(label):
        imgui.open_popup(f'{label} selector')
    if imgui.begin_popup(f'{label} selector'):
        for key in dict:
            opened, dict[key] = imgui.selectable(str(key), dict[key])
        imgui.end_popup()



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

    imgui.style_colors_light()
    imgui.push_style_color(imgui.COLOR_TEXT, 0,0,0,1)
    graphic_manager = GraphicManager()

    lst_time = time.time()
    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            impl.process_event(event)
        impl.process_inputs()
        # update graphic
        # time.sleep(0.1)
        # graphic_manager.update_main()

        # draw imgui windows
        imgui.new_frame()
        with imgui.font(chinese_font):
            # put your windows here
            imgui_image_window()
            imgui_main_window()

        # render and display
        gl.glClearColor(1, 1, 1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        pygame.display.flip()
