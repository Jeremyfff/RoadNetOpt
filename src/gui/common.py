import os
import pickle

import imgui
import numpy as np
import pygame
from PIL import Image
from graphic_module import GraphicManager
from geo import Road
from utils import io_utils
from gui import global_var as g
from gui import components as imgui_c
from utils import graphic_uitls


def update_main_graphic():
    if not g.mShowingMainTextureWindow:
        return
    # 主界面交互
    handle_inputs()
    GraphicManager.instance.main_texture.update()


def handle_inputs():
    normal_mode = not g.mAddNodeMode
    # handle keyboards
    handle_common_keyboard_interation()
    if normal_mode:
        handle_normal_keyboard_interation()
    elif g.mAddNodeMode:
        handle_add_mode_keyboard_interation()

    # handle mouse
    if is_hovering_image_window():
        if normal_mode:
            handle_normal_mouse_interaction()
        elif g.mAddNodeMode:
            handle_add_mode_mouse_interation()


def handle_common_keyboard_interation():
    if imgui.is_key_pressed(imgui.KEY_ESCAPE):
        clear_selected_roads_and_update_graphic()
    if imgui.is_key_pressed(imgui.KEY_BACKSPACE):
        GraphicManager.instance.main_texture.clear_cache()
    if imgui.is_key_pressed(imgui.KEY_DELETE):
        for road in g.mSelectedRoads.values():
            Road.delete_road_by_uid(road['uid'])
        clear_selected_roads_and_update_graphic()


def handle_normal_keyboard_interation():
    pass


def handle_add_mode_keyboard_interation():
    if imgui.is_key_pressed(imgui.KEY_ENTER):
        g.mAddNodeMode = False


def handle_normal_mouse_interaction():
    if imgui.is_mouse_clicked(0):  # left
        if imgui.get_io().key_shift:
            select_or_deselect_road_by_current_mouse_pos()
        elif imgui.get_io().key_ctrl:
            select_road_by_current_mouse_pos(add_mode=True)
        else:
            select_road_by_current_mouse_pos(add_mode=False)

    if imgui.is_mouse_dragging(2):
        print('dragging')


def handle_add_mode_mouse_interation():
    if g.mCurrentEditingRoad is None:
        return
    if imgui.is_mouse_clicked(0):
        read_point = graphic_uitls.image_space_to_world_space(g.mMousePosInImage[0],
                                                              g.mMousePosInImage[1],
                                                              GraphicManager.instance.main_texture.x_lim,
                                                              GraphicManager.instance.main_texture.y_lim,
                                                              g.mImageSize[0],
                                                              g.mImageSize[1])
        read_point_np = np.array([[read_point[0], read_point[1]]])
        g.mCurrentEditingRoad = Road.add_point_to_road(g.mCurrentEditingRoad, read_point_np)


def is_hovering_image_window():
    return g.mHoveringImageWindow and \
        not g.mHoveringMainTextureSubWindow and \
        not g.mHoveringInfoSubWindow and \
        not g.mHoveringDxfSubWindow


def get_road_by_current_mouse_pos():
    idx = GraphicManager.instance.main_texture.get_road_idx_by_mouse_pos(g.mMousePosInImage)
    if idx is None:
        return None
    try:
        road = Road.get_road_by_index(idx)
        return road
    except Exception as e:
        return None


def select_road_by_current_mouse_pos(add_mode=False):
    road = get_road_by_current_mouse_pos()
    if road is None:
        if not add_mode:
            clear_selected_roads_and_update_graphic()
        return
    uid = road['uid']
    if not add_mode:
        g.mSelectedRoads = {}
    g.mSelectedRoads[uid] = road
    GraphicManager.instance.main_texture.clear_highlight_data()


def select_or_deselect_road_by_current_mouse_pos():
    road = get_road_by_current_mouse_pos()
    if road is None:
        return
    uid = road['uid']
    if uid in g.mSelectedRoads.keys():
        g.mSelectedRoads.pop(uid)
    else:
        g.mSelectedRoads[uid] = road
    GraphicManager.instance.main_texture.clear_highlight_data()


def deselect_road_by_current_mouse_pos():
    road = get_road_by_current_mouse_pos()
    if road is None:
        return
    uid = road['uid']
    g.mSelectedRoads.pop(uid)
    GraphicManager.instance.main_texture.clear_highlight_data()


def clear_selected_roads_and_update_graphic():
    if len(g.mSelectedRoads) > 0:
        GraphicManager.instance.main_texture.clear_highlight_data()
        g.mSelectedRoads = {}


def save_selected_roads():
    geo_hashes = [road['geohash'] for road in g.mSelectedRoads.values()]
    print(f'geo hashes = {geo_hashes}')
    file_path = io_utils.save_file_window(defaultextension='.geohash',
                                          filetypes=[('Geometry Hash', '.geohash')])
    if file_path is None or file_path == '':
        return

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'wb') as file:
        pickle.dump(geo_hashes, file)
    print(f'geohash saved to {file_path}')


def load_selected_road_from_file(add_mode=False):
    file_path = io_utils.open_file_window(filetypes=[('Geometry Hash', '.geohash')])
    print(f'loading geohash from {file_path}')
    if file_path is None or file_path == '':
        return
    with open(file_path, 'rb') as file:
        geo_hashes: list = pickle.load(file)
        print(f'found {len(geo_hashes)} road hashes in file')
        try:
            selected_roads = Road.get_roads_by_hashes(geo_hashes)
            if not add_mode:
                g.mSelectedRoads = {}
            for uid, road in selected_roads.iterrows():
                g.mSelectedRoads[uid] = road
                GraphicManager.instance.main_texture.clear_highlight_data()
        except Exception as e:
            print(str(e))
