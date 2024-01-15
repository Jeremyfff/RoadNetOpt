import imgui
import pygame
from PIL import Image
from graphic_module import GraphicManager
from geo import Road
from utils import io_utils
from gui import global_var as g
from gui import components as imgui_c


def update_main_graphic():

    if imgui.is_key_pressed(imgui.KEY_ESCAPE):
        if len(g.mSelectedRoads) > 0:
            print('[GUI][update_main_graphic] clear highlight data')
            GraphicManager.instance.main_texture.clear_highlight_data()
            g.mSelectedRoads = {}
    if imgui.is_key_pressed(imgui.KEY_DELETE):
        print('[GUI][update_main_graphic] redraw all')
        GraphicManager.instance.main_texture.clear_cache()

    if imgui.is_mouse_clicked(
            imgui.MOUSE_BUTTON_LEFT) and \
            g.mHoveringImageWindow and \
            not g.mHoveringMainTextureSubWindow and \
            not g.mHoveringInfoSubWindow and \
            not g.mHoveringDxfSubWindow:
        on_road, idx = GraphicManager.instance.main_texture.on_left_mouse_click(g.mMousePosInImage)
        if on_road:
            try:
                road = Road.get_road_by_index(idx)
                uid = road['uid']
                g.mSelectedRoads[uid] = road
            except:
                pass

    GraphicManager.instance.main_texture.update(target_size=g.mImageSize,
                                                selected_roads=g.mSelectedRoads)