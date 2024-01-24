from typing import *
import imgui

from gui.icon_module import IconManager
from style_module import StyleManager
from graphic_module import GraphicManager

from gui import global_var as g
from gui import components as imgui_c
from gui import common

mCurrentRoadDisplayOption = 0
mCurrentBuildingDisplayOption = 0
mCurrentRegionDisplayOption = 0

mPinSelectEditor = False
mPinSelectEditorPos: Union[tuple, None] = None
print('main_texture_toolbox subwindow loaded')


def show():
    global mCurrentRoadDisplayOption, mCurrentBuildingDisplayOption, \
        mCurrentRegionDisplayOption, mPinSelectEditor, mPinSelectEditorPos
    tool_set_button_num = 3  # 在这里更改按钮个数

    imgui.set_next_window_position(*g.mImageWindowInnerPos)
    imgui.set_next_window_size(g.DEFAULT_IMAGE_BUTTON_WIDTH + 22,
                               tool_set_button_num * (g.DEFAULT_IMAGE_BUTTON_HEIGHT + 22))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE
    expanded, _ = imgui.begin('main texture subwindow', False, flags)
    g.mHoveringMainTextureSubWindow = imgui_c.is_hovering_window()

    # 显示样式设置
    if imgui.image_button(IconManager.icons['paint-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_style_editor')
    imgui_c.tooltip('显示样式设置')
    if imgui.begin_popup('display_style_editor'):
        g.mHoveringMainTextureSubWindow = True
        StyleManager.instance.display_style.show_imgui_style_editor(
            road_style_change_callback=GraphicManager.instance.main_texture.clear_road_data,
            building_style_change_callback=GraphicManager.instance.main_texture.clear_building_data,
            region_style_change_callback=GraphicManager.instance.main_texture.clear_region_data,
        )
        imgui.end_popup()

    # 显示图层设置
    if imgui.image_button(IconManager.icons['stack-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_layer_editor')
    imgui_c.tooltip('显示图层设置')
    if imgui.begin_popup('display_layer_editor'):
        g.mHoveringMainTextureSubWindow = True
        GraphicManager.instance.main_texture.show_imgui_display_editor()
        imgui.end_popup()

    # 选择工具
    if imgui.image_button(IconManager.icons['cursor-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('select_editor')
    imgui_c.tooltip('显示选择详情')
    if not mPinSelectEditor and imgui.begin_popup('select_editor'):
        g.mHoveringMainTextureSubWindow = True
        imgui_select_editor_content()
        imgui.end_popup()
    elif mPinSelectEditor:
        if mPinSelectEditorPos is not None:
            imgui.set_next_window_position(mPinSelectEditorPos[0], mPinSelectEditorPos[1])
            mPinSelectEditorPos = None
        expanded, mPinSelectEditor = imgui.begin('select_editor_subwindow', True, imgui.WINDOW_NO_TITLE_BAR)
        imgui_select_editor_content()
        imgui.end()
    imgui.end()


def imgui_select_editor_content():
    global mPinSelectEditor, mPinSelectEditorPos

    icon_name = 'pushpin-2-fill' if mPinSelectEditor else 'pushpin-2-line'
    if imgui.image_button(IconManager.icons[icon_name], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        mPinSelectEditor = not mPinSelectEditor
        if mPinSelectEditor:
            mPinSelectEditorPos = imgui.get_window_position()
    imgui_c.tooltip('取消Pin' if mPinSelectEditor else 'Pin')
    imgui.text(f'selected roads {len(g.mSelectedRoads)}')
    if imgui.button('取消所有选择'):
        common._clear_selected_roads_and_update_graphic()
    if imgui.button('save selected roads'):
        common.save_selected_roads()
    imgui.same_line()
    if imgui.button('load selection'):
        common.load_selected_road_from_file()
    imgui_c.dict_viewer_component(g.mSelectedRoads, 'seleted roads', 'uid', 'hash',
                                  lambda road: str(road['geohash']))
