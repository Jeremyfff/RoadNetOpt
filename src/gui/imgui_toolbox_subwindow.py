from typing import *
import imgui
import numpy as np
from PIL import Image

from gui.icon_module import IconManager
from style_module import StyleManager
from graphic_module import GraphicManager

from gui import global_var as g
from gui import components as imgui_c
from gui import common
from utils import io_utils

print('main_texture_toolbox subwindow loaded')

mTextureInfo = {}
mTmpImgWidth = 0
mTmpImgHeight = 0

mPinSelectEditor = False
mPinSelectEditorPos: Union[tuple, None] = None


def show(graphic_texture):
    if g.mShowingMainTextureWindow:
        tool_set_button_num = 5  # 在这里更改按钮个数
    else:
        tool_set_button_num = 1  # 在这里更改按钮个数

    imgui.set_next_window_position(*g.mImageWindowInnerPos)
    imgui.set_next_window_size(g.DEFAULT_IMAGE_BUTTON_WIDTH + 24,
                               tool_set_button_num * (g.DEFAULT_IMAGE_BUTTON_HEIGHT + 16) + 8)
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE
    expanded, _ = imgui.begin('main texture subwindow', False, flags)
    g.mHoveringMainTextureSubWindow = imgui_c.is_hovering_window()

    # 显示图层设置
    if g.mShowingMainTextureWindow:
        show_display_layer_editor()

    # 显示样式设置
    if g.mShowingMainTextureWindow:
        show_display_style_editor()

    # 选择工具
    if g.mShowingMainTextureWindow:
        show_select_editor()

    # 图像信息
    show_graphic_info(graphic_texture)

    # 图形设置
    if g.mShowingMainTextureWindow:
        show_graphic_settings()

    imgui.end()


def show_display_layer_editor():
    if imgui.image_button(IconManager.icons['stack-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_layer_editor')
    imgui_c.tooltip('显示图层设置')
    if imgui.begin_popup('display_layer_editor'):
        g.mHoveringMainTextureSubWindow = True
        GraphicManager.I.MainTexture.show_imgui_display_editor()
        imgui.end_popup()


def show_display_style_editor():
    if imgui.image_button(IconManager.icons['paint-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_style_editor')
    imgui_c.tooltip('显示样式设置')
    if imgui.begin_popup('display_style_editor'):
        g.mHoveringMainTextureSubWindow = True
        StyleManager.instance.display_style.show_imgui_style_editor(
            road_style_change_callback=GraphicManager.I.MainTexture.clear_road_data,
            building_style_change_callback=GraphicManager.I.MainTexture.clear_building_data,
            region_style_change_callback=GraphicManager.I.MainTexture.clear_region_data,
            node_style_change_callback=GraphicManager.I.MainTexture.clear_node_data,
            highlight_style_change_callback=GraphicManager.I.MainTexture.clear_highlight_data
        )
        imgui.end_popup()


def show_select_editor():
    global mPinSelectEditor, mPinSelectEditorPos
    if imgui.image_button(IconManager.icons['cursor-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('select_editor')
    imgui_c.tooltip('显示选择详情')
    if not mPinSelectEditor and imgui.begin_popup('select_editor'):
        g.mHoveringMainTextureSubWindow = True
        _imgui_select_editor_content()
        imgui.end_popup()
    elif mPinSelectEditor:
        if mPinSelectEditorPos is not None:
            imgui.set_next_window_position(mPinSelectEditorPos[0], mPinSelectEditorPos[1])
            mPinSelectEditorPos = None
        expanded, mPinSelectEditor = imgui.begin('select_editor_subwindow', True, imgui.WINDOW_NO_TITLE_BAR)
        _imgui_select_editor_content()
        imgui.end()


def show_graphic_info(graphic_texture):
    """显示图像信息"""
    global mTextureInfo
    if imgui.image_button(IconManager.icons['information-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('graphic_texture_info')
    imgui_c.tooltip('图像信息')
    if imgui.begin_popup('graphic_texture_info'):
        mTextureInfo['name'] = graphic_texture.name
        mTextureInfo['Type'] = str(type(graphic_texture)).split(".")[-1].split("'")[0]
        mTextureInfo['texture size'] = f"{graphic_texture.width} , {graphic_texture.height}"

        mTextureInfo['x_min'] = f"{graphic_texture.x_lim[0]:.3f}" if graphic_texture.x_lim is not None else "N/A"
        mTextureInfo['x_max'] = f"{graphic_texture.x_lim[1]:.3f}" if graphic_texture.x_lim is not None else "N/A"
        mTextureInfo['y_min'] = f"{graphic_texture.y_lim[0]:.3f}" if graphic_texture.y_lim is not None else "N/A"
        mTextureInfo['y_max'] = f"{graphic_texture.y_lim[1]:.3f}" if graphic_texture.y_lim is not None else "N/A"

        imgui_c.dict_viewer_component(mTextureInfo, 'Texture Info', '项目', '值', flags=imgui.TABLE_ROW_BACKGROUND)
        imgui.separator()
        if imgui.button('保存当前帧至本地', width=imgui.get_content_region_available_width()):
            buffer = graphic_texture.texture.read()
            img_arr = np.frombuffer(buffer, dtype=np.uint8).reshape(
                (graphic_texture.height, graphic_texture.width, graphic_texture.channel))
            image = Image.fromarray(img_arr)
            path = io_utils.save_file_window(defaultextension='.png', filetypes=[('Image File', '.png')])
            if path != "" and path is not None:
                image.save(path)

        imgui.end_popup()


def show_graphic_settings():
    """图形设置"""
    if imgui.image_button(IconManager.icons['settings-4-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('main_texture_settings')
    imgui_c.tooltip('图形设置')
    if imgui.begin_popup('main_texture_settings'):
        g.mHoveringMainTextureSubWindow = True
        GraphicManager.I.MainTexture.show_imgui_main_texture_settings()
        imgui.end_popup()


def _imgui_select_editor_content():
    global mPinSelectEditor, mPinSelectEditorPos

    icon_name = 'pushpin-2-fill' if mPinSelectEditor else 'pushpin-2-line'
    if imgui.image_button(IconManager.icons[icon_name], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        mPinSelectEditor = not mPinSelectEditor
        if mPinSelectEditor:
            mPinSelectEditorPos = imgui.get_window_position()
    imgui_c.tooltip('取消Pin' if mPinSelectEditor else 'Pin')
    clicked, state = imgui.checkbox('选择道路', g.mSelectRoadsMode)
    if clicked:
        g.mSelectRoadsMode = state
        common.clear_selected_roads_or_nodes_and_update_graphic()
    clicked, state = imgui.checkbox('选择节点', not g.mSelectRoadsMode)
    if clicked:
        g.mSelectRoadsMode = not state
        common.clear_selected_roads_or_nodes_and_update_graphic()
    imgui.text(f'selected roads {len(g.mSelectedRoads)}')
    if imgui.button('取消所有选择'):
        common.clear_selected_roads_or_nodes_and_update_graphic()
    if imgui.button('save selected roads'):
        common.save_selected_roads()
    imgui.same_line()
    if imgui.button('load selection'):
        common.load_selected_road_from_file()
    imgui_c.dict_viewer_component(g.mSelectedRoads, 'seleted roads', 'uid', 'hash',
                                  lambda road: str(road['geohash']))
