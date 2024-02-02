import os
import pickle

import imgui
import pygame
from graphic_module import GraphicManager
from geo import Road, Building, Region
from gui import global_var as g
from gui import components as imgui_c
from gui import common
from utils import io_utils, graphic_uitls

mGDFInfo = {}

print('info subwindow loaded')


def show():
    if g.mInfoWindowOpened:

        screen_width, screen_height = g.mWindowSize
        window_width = 400
        windows_height = screen_height - g.IMAGE_WINDOW_INDENT_TOP - g.BOTTOM_WINDOW_HEIGHT
        imgui.set_next_window_position(screen_width - window_width, g.IMAGE_WINDOW_INDENT_TOP)
        imgui.set_next_window_size(window_width, windows_height)
        imgui_c.auto_push_blur_window_bg()  # 如果开启了窗口模糊，则处理相关内容
        # 开启窗口
        expanded, g.mInfoWindowOpened = imgui.begin('信息窗口', True)
        imgui_c.auto_pop_blur_window_bg()  # 如果开启了窗口模糊，则处理相关内容
        if expanded:
            imgui_c.auto_draw_blur_bg(GraphicManager.I.ImguiBlurLayer.texture_id)  # 如果开启了窗口模糊，则处理相关内容
            g.mHoveringInfoSubWindow = imgui_c.is_hovering_window()
            if g.mSmoothedFrameTime == 0:
                g.mSmoothedFrameTime += 1e-4
            imgui.text(f'fps {(1.0 / g.mSmoothedFrameTime):.0f}')
            imgui.separator()
            imgui.text('gdf信息:')
            update_mGDFInfo()
            imgui_c.dict_viewer_component(mGDFInfo, 'dgf info', 'GDF Type', 'count', lambda value: str(value))

            item_count = len(g.mSelectedRoads)
            item_count = 4 if item_count > 4 else item_count
            child_height = (item_count + 1) * (g.FONT_SIZE + 8) * g.GLOBAL_SCALE + 8
            imgui.begin_child('selected roads', 0, child_height, border=True)
            imgui.text(f'selected roads: {len(g.mSelectedRoads)}')
            for uid, road in g.mSelectedRoads.items():
                imgui.text(str(uid))
            imgui.end_child()
            imgui.text('')

            item_count = len(g.mSelectedNodes)
            item_count = 4 if item_count > 4 else item_count
            child_height = (item_count + 1) * (g.FONT_SIZE + 8) * g.GLOBAL_SCALE + 8
            imgui.begin_child('selected nodes', 0, child_height, border=True)
            imgui.text(f'selected nodes: {len(g.mSelectedNodes)}')
            for uid, node in g.mSelectedNodes.items():
                imgui.text(str(uid))
            imgui.end_child()
            imgui.text('')

            imgui.text(f'inner image mpose {g.mMousePosInImage}')
            if GraphicManager.I.MainTexture.x_lim is not None:
                mouse_world_pos = graphic_uitls.image_space_to_world_space(g.mMousePosInImage[0],
                                                                           g.mMousePosInImage[1],
                                                                           GraphicManager.I.MainTexture.x_lim,
                                                                           GraphicManager.I.MainTexture.y_lim,
                                                                           g.mImageSize[0],
                                                                           g.mImageSize[1])
                imgui.text(f'mouse world pos ({mouse_world_pos[0]:.2f}, {mouse_world_pos[1]:.2f})')

            imgui.text(f'Ctrl: {g.mCtrl}')
            imgui.text(f'Shift: {g.mShift}')
            imgui.text(f'Alt: {g.mAlt}')
        imgui.end()


def update_mGDFInfo():
    global mGDFInfo
    mGDFInfo['Roads'] = len(Road.get_all_roads())
    mGDFInfo['Buildings'] = len(Building.get_all_buildings())
    mGDFInfo['Regions'] = len(Region.get_all_regions())
