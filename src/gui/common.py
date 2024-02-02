import os
import pickle
import traceback
import imgui
import numpy as np
from graphic_module import GraphicManager
from geo import Road
from utils import io_utils
from gui import global_var as g
from utils import graphic_uitls


def update_main_graphic():
    """自定义图形和交互的主循环"""
    if not g.mShowingMainTextureWindow: return
    handle_mouse_event()
    # 键盘事件在GUI.py WindowEvents 的key_event中处理
    GraphicManager.I.MainTexture.update()
    if g.ENABLE_WINDOW_BLUR:
        GraphicManager.I.ImguiBlurLayer.update()


def handle_mouse_event():
    """处理鼠标事件"""
    # 全局鼠标事件
    _handle_global_common_mouse_interaction()
    if not g.mShowingMainTextureWindow: return
    # 以下为主图形窗口显示时的交互
    _handle_main_texture_common_mouse_interaction()
    if not _is_hovering_image_window(): return
    # 以下为鼠标落在主图形窗口中的交互
    normal_mode = not g.mAddNodeMode
    if normal_mode:
        _handle_main_texture_normal_mode_mouse_interaction()
    elif g.mAddNodeMode:
        _handle_main_texture_add_mode_mouse_interation()


def handle_key_event(key, action, modifiers):
    """处理键盘事件"""
    # 全局键盘事件
    _handle_global_common_keyboard_interation(key, action, modifiers)
    if not g.mShowingMainTextureWindow: return
    # 以下为主图形窗口显示时的交互
    normal_mode = not g.mAddNodeMode
    _handle_main_texture_common_keyboard_interation(key, action, modifiers)
    if normal_mode:
        _handle_main_texture_normal_mode_keyboard_interation(key, action, modifiers)
    elif g.mAddNodeMode:
        _handle_main_texture_add_mode_keyboard_interation(key, action, modifiers)


def _handle_global_common_mouse_interaction():
    """全局通用鼠标事件"""
    pass


mLastTextureSpaceDeltaX = 0
mLastTextureSpaceDeltaY = 0
mIsMouseDragging = False
mSelectedRoadsBeforeDrag = {}
mSelectedNodesBeforeDrag = {}


def _handle_main_texture_common_mouse_interaction():
    """main texture窗口显示时的鼠标交互， 鼠标可在窗口外面"""
    global mLastTextureSpaceDeltaX, mLastTextureSpaceDeltaY, mIsMouseDragging
    # 鼠标中键 拖拽
    if imgui.is_mouse_dragging(2):
        if not mIsMouseDragging and _is_hovering_image_window():  # start point
            imgui.reset_mouse_drag_delta(2)
            mIsMouseDragging = True
            return
        if mIsMouseDragging:
            screen_space_mouse_delta = imgui.get_mouse_drag_delta(2)
            texture_space_delta_x = screen_space_mouse_delta[0] / float(g.TEXTURE_SCALE)
            texture_space_delta_y = screen_space_mouse_delta[1] / float(g.TEXTURE_SCALE)
            GraphicManager.I.MainTexture.pan(
                (texture_space_delta_x - mLastTextureSpaceDeltaX,
                 texture_space_delta_y - mLastTextureSpaceDeltaY)
            )
            mLastTextureSpaceDeltaX = texture_space_delta_x
            mLastTextureSpaceDeltaY = texture_space_delta_y
    if imgui.is_mouse_released(2):
        mIsMouseDragging = False
        mLastTextureSpaceDeltaX = 0
        mLastTextureSpaceDeltaY = 0
        imgui.reset_mouse_drag_delta(2)
    # 鼠标左键 拖拽
    if imgui.is_mouse_dragging(0):
        if not mIsMouseDragging and _is_hovering_image_window():
            imgui.reset_mouse_drag_delta(0)
            mIsMouseDragging = True
            _start_drag_selection()
            return
        if mIsMouseDragging:
            if g.mShift:
                _select_roads_or_nodes_by_drag_selection(add_mode=True)
            elif g.mCtrl:
                _select_roads_or_nodes_by_drag_selection(add_mode=True)
            elif g.mAlt:
                _deselect_roads_or_nodes_by_drag_selection()
            else:
                _select_roads_or_nodes_by_drag_selection(add_mode=False)
    if imgui.is_mouse_released(0):
        _end_drag_selection()
        mIsMouseDragging = False
        imgui.reset_mouse_drag_delta(0)


def _handle_main_texture_normal_mode_mouse_interaction():
    """main texture窗口显示，并且鼠标在窗口内部的交互 普通模式"""
    # 鼠标左键 点击
    if imgui.is_mouse_clicked(0):
        if g.mShift:
            _select_or_deselect_road_or_node_by_current_mouse_pos()
        elif g.mCtrl:
            _select_road_or_node_by_current_mouse_pos(add_mode=True)
        else:
            _select_road_or_node_by_current_mouse_pos(add_mode=False)
    # 鼠标滚轮滚动
    mouse_scroll_y = imgui.get_io().mouse_wheel
    if mouse_scroll_y != 0:
        GraphicManager.I.MainTexture.zoom(g.mMousePosInImage, 1.0 - mouse_scroll_y * 0.1)


def _handle_main_texture_add_mode_mouse_interation():
    """main texture窗口显示，手动添加道路模式，并且鼠标在窗口内部的交互"""
    if g.mCurrentEditingRoad is None: return
    # 鼠标左键点击
    if imgui.is_mouse_clicked(0):
        mouse_point_world_space = graphic_uitls.image_space_to_world_space(
            g.mMousePosInImage[0], g.mMousePosInImage[1],
            GraphicManager.I.MainTexture.x_lim, GraphicManager.I.MainTexture.y_lim,
            g.mImageSize[0], g.mImageSize[1]
        )
        road_point = np.array([[mouse_point_world_space[0], mouse_point_world_space[1]]])
        g.mCurrentEditingRoad = Road.add_point_to_road(g.mCurrentEditingRoad, road_point)


def _handle_global_common_keyboard_interation(key, action, modifiers):
    """全局有效的键盘事件"""
    keys = g.mWindowEvent.wnd.keys
    if action == keys.ACTION_PRESS:
        if modifiers.ctrl:
            g.mCtrl = True
        if modifiers.shift:
            g.mShift = True
        if modifiers.alt:
            g.mAlt = True
        if modifiers.ctrl and key == keys.Q:
            g.mWindowEvent.wnd.close()
    elif action == keys.ACTION_RELEASE:
        g.mCtrl = False
        g.mShift = False
        g.mAlt = False


def _handle_main_texture_common_keyboard_interation(key, action, modifiers):
    """main texture 显示时通用的键盘事件"""
    keys = g.mWindowEvent.wnd.keys
    if action == keys.ACTION_PRESS:
        # 按下的事件
        # delete键 删除
        if key == keys.DELETE:
            for road in g.mSelectedRoads.values():
                Road.delete_road_by_uid(road['uid'])
            clear_selected_roads_or_nodes_and_update_graphic()
        # ctrl R 刷新
        elif modifiers.ctrl and key == keys.R:
            GraphicManager.I.MainTexture.clear_cache()
        # ctrl A 全选
        elif modifiers.ctrl and key == keys.A:
            if g.mSelectRoadsMode:
                for uid, road in Road.get_roads_by_cluster(GraphicManager.I.MainTexture.road_cluster).iterrows():
                    g.mSelectedRoads[uid] = road
            else:
                for uid, node in Road.get_all_nodes().iterrows():
                    g.mSelectedNodes[uid] = node

            GraphicManager.I.MainTexture.clear_highlight_data()
    elif action == keys.ACTION_RELEASE:
        # 抬起的事件
        pass


def _handle_main_texture_normal_mode_keyboard_interation(key, action, modifiers):
    """main texture显示时， 普通模式的键盘事件"""
    pass


def _handle_main_texture_add_mode_keyboard_interation(key, action, modifiers):
    """main texture显示时， 手动添加路网模式的键盘事件"""
    if imgui.is_key_pressed(imgui.KEY_ENTER):
        g.mAddNodeMode = False


def _is_hovering_image_window():
    return g.mHoveringImageWindow and \
        not g.mHoveringMainTextureSubWindow and \
        not g.mHoveringInfoSubWindow and \
        not g.mHoveringDxfSubWindow


def _get_road_by_current_mouse_pos():
    idx = GraphicManager.I.MainTexture.get_road_or_node_idx_by_mouse_pos(g.mMousePosInImage, select_roads=True)
    if idx is None: return None
    try:
        return Road.get_road_by_index(idx)
    except Exception as e:
        print(e)
        return None


def _get_node_by_current_mouse_pos():
    idx = GraphicManager.I.MainTexture.get_road_or_node_idx_by_mouse_pos(g.mMousePosInImage, select_roads=False)
    if idx is None:
        return None
    try:
        return Road.get_node_by_index(idx)
    except Exception as e:
        print(e)
        return None


def _start_drag_selection():
    if g.mSelectRoadsMode:
        _start_drag_selection_road()
    else:
        _start_drag_selection_node()


def _start_drag_selection_road():
    global mSelectedRoadsBeforeDrag
    mSelectedRoadsBeforeDrag = g.mSelectedRoads.copy()
    GraphicManager.I.MainTexture.start_drag_selection(g.mMousePosInImage, select_roads=True)


def _start_drag_selection_node():
    global mSelectedNodesBeforeDrag
    mSelectedNodesBeforeDrag = g.mSelectedNodes.copy()
    GraphicManager.I.MainTexture.start_drag_selection(g.mMousePosInImage, select_roads=False)


def _get_roads_or_nodes_by_drag_selection():
    if g.mSelectRoadsMode:
        _get_roads_by_drag_selection()
    else:
        _get_nodes_by_drag_selection()


def _get_roads_by_drag_selection():
    idx_list = GraphicManager.I.MainTexture.update_drag_selection(g.mMousePosInImage)
    if idx_list is None:
        return None
    try:
        roads = Road.get_roads_by_indexes(idx_list)
        return roads
    except Exception as e:
        traceback.print_stack()
        print(e)
        return None


def _get_nodes_by_drag_selection():
    idx_list = GraphicManager.I.MainTexture.update_drag_selection(g.mMousePosInImage)
    if idx_list is None:
        return None
    try:
        nodes = Road.get_nodes_by_indexes(idx_list)
        return nodes
    except Exception as e:
        traceback.print_stack()
        print(e)
        return None


def _end_drag_selection():
    global mSelectedRoadsBeforeDrag
    mSelectedRoadsBeforeDrag = None
    GraphicManager.I.MainTexture.end_drag_selection()


def _select_road_or_node_by_current_mouse_pos(add_mode=False):
    if g.mSelectRoadsMode:
        _select_road_by_current_mouse_pos(add_mode)
    else:
        _select_node_by_current_mouse_pos(add_mode)


def _select_road_by_current_mouse_pos(add_mode=False):
    road = _get_road_by_current_mouse_pos()
    if road is None:
        if not add_mode:
            clear_selected_roads_or_nodes_and_update_graphic()
        return
    uid = road['uid']
    if not add_mode:
        g.mSelectedRoads = {}
    g.mSelectedRoads[uid] = road
    GraphicManager.I.MainTexture.clear_highlight_data()


def _select_node_by_current_mouse_pos(add_mode=False):
    node = _get_node_by_current_mouse_pos()
    if node is None:
        if not add_mode:
            clear_selected_roads_or_nodes_and_update_graphic()
        return
    uid = node['uid']
    if not add_mode:
        g.mSelectedNodes = {}
    g.mSelectedNodes[uid] = node
    GraphicManager.I.MainTexture.clear_highlight_data()


def _select_or_deselect_road_or_node_by_current_mouse_pos():
    if g.mSelectRoadsMode:
        _select_or_deselect_road_by_current_mouse_pos()
    else:
        _select_or_deselect_node_by_current_mouse_pos()


def _select_or_deselect_road_by_current_mouse_pos():
    road = _get_road_by_current_mouse_pos()
    if road is None:
        return
    uid = road['uid']
    if uid in g.mSelectedRoads.keys():
        g.mSelectedRoads.pop(uid)
    else:
        g.mSelectedRoads[uid] = road
    GraphicManager.I.MainTexture.clear_highlight_data()


def _select_or_deselect_node_by_current_mouse_pos():
    node = _get_node_by_current_mouse_pos()
    if node is None:
        return
    uid = node['uid']
    if uid in g.mSelectedNodes.keys():
        g.mSelectedNodes.pop(uid)
    else:
        g.mSelectedNodes[uid] = node
    GraphicManager.I.MainTexture.clear_highlight_data()


def _select_roads_or_nodes_by_drag_selection(add_mode=False):
    if g.mSelectRoadsMode:
        _select_roads_by_drag_selection(add_mode)
    else:
        _select_nodes_by_drag_selection(add_mode)


def _select_roads_by_drag_selection(add_mode=False):
    roads = _get_roads_by_drag_selection()
    if roads is None:
        return
    if not add_mode:
        g.mSelectedRoads = {}
    for uid, road in roads.iterrows():
        g.mSelectedRoads[uid] = road
    GraphicManager.I.MainTexture.clear_highlight_data()


def _select_nodes_by_drag_selection(add_mode=False):
    nodes = _get_nodes_by_drag_selection()
    if nodes is None:
        return
    if not add_mode:
        g.mSelectedNodes = {}
    for uid, node in nodes.iterrows():
        g.mSelectedNodes[uid] = node
    GraphicManager.I.MainTexture.clear_highlight_data()


def _deselect_roads_or_nodes_by_drag_selection():
    if g.mSelectRoadsMode:
        _deselect_roads_by_drag_selection()
    else:
        _deselect_nodes_by_drag_selection()


def _deselect_roads_by_drag_selection():
    roads = _get_roads_by_drag_selection()
    if roads is None:
        return
    g.mSelectedRoads = mSelectedRoadsBeforeDrag.copy()
    for uid, road in roads.iterrows():
        if uid in g.mSelectedRoads:
            g.mSelectedRoads.pop(uid)
    GraphicManager.I.MainTexture.clear_highlight_data()


def _deselect_nodes_by_drag_selection():
    nodes = _get_nodes_by_drag_selection()
    if nodes is None:
        return
    g.mSelectedNodes = mSelectedNodesBeforeDrag.copy()
    for uid, node in nodes.iterrows():
        if uid in g.mSelectedNodes:
            g.mSelectedNodes.pop(uid)
    GraphicManager.I.MainTexture.clear_highlight_data()


def clear_selected_roads_or_nodes_and_update_graphic():
    if g.mSelectRoadsMode:
        _clear_selected_roads_and_update_graphic()
    else:
        _clear_selected_nodes_and_update_graphic()


def _clear_selected_roads_and_update_graphic():
    if len(g.mSelectedRoads) > 0:
        GraphicManager.I.MainTexture.clear_highlight_data()
        g.mSelectedRoads = {}


def _clear_selected_nodes_and_update_graphic():
    if len(g.mSelectedNodes) > 0:
        GraphicManager.I.MainTexture.clear_highlight_data()
        g.mSelectedNodes = {}


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
                GraphicManager.I.MainTexture.clear_highlight_data()
        except Exception as e:
            print(str(e))
