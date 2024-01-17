import os
import pickle

import imgui
import pygame
from graphic_module import GraphicManager
from geo import Road, Building, Region
from gui import global_var as g
from gui import components as imgui_c
from gui import common
from utils import io_utils

mGraphicCacheInfo = {}
mGDFInfo = {}


print('info subwindow loaded')
def show():

    if g.mInfoWindowOpened:
        if g.mFirstLoop:
            window_width = 400
            windows_height = 400
            screen_width, screen_height = pygame.display.get_window_size()
            imgui.set_next_window_position(screen_width - window_width, 32)
            imgui.set_next_window_size(window_width, windows_height)
        expanded, g.mInfoWindowOpened = imgui.begin('信息窗口', True)
        g.mHoveringInfoSubWindow = imgui_c.is_hovering_window()
        if g.mFrameTime == 0:
            g.mFrameTime += 1e-4
        imgui.text(f'fps {(1.0 / g.mFrameTime):.1f}')
        imgui.separator()
        imgui.text('gdf信息:')
        update_mGDFInfo()
        imgui_c.dict_viewer_component(mGDFInfo, 'dgf info', 'GDF Type', 'count', lambda value: str(value))

        imgui.text(f'selected roads {len(g.mSelectedRoads)}')
        imgui.text('')
        imgui.text('图像缓冲区:')
        mGraphicCacheInfo[
            'cached highlighted img'] = GraphicManager.instance.main_texture.cached_highlighted_road_data is not None
        mGraphicCacheInfo['cached road img'] = GraphicManager.instance.main_texture.cached_road_data is not None
        mGraphicCacheInfo['cached road idx img'] = GraphicManager.instance.main_texture.cached_road_idx is not None
        imgui_c.dict_viewer_component(mGraphicCacheInfo, 'graphic cache info', 'cache type', 'has data',
                                    lambda value: str(value))

        imgui.text(f'inner image mpose {g.mMousePosInImage}')
        imgui.end()


def update_mGDFInfo():
    global mGDFInfo
    mGDFInfo['Roads'] = len(Road.get_all_roads())
    mGDFInfo['Buildings'] = len(Building.get_all_buildings())
    mGDFInfo['Regions'] = len(Region.get_all_regions())
