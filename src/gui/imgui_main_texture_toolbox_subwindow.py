import imgui

from gui.icon_module import IconManager
from style_module import StyleManager
from graphic_module import GraphicManager

from gui import global_var as g
from gui import components as imgui_c

mCurrentRoadDisplayOption = 0
mCurrentBuildingDisplayOption = 0
mCurrentRegionDisplayOption = 0

print('main_texture_toolbox subwindow loaded')
def show(pos):
    global mCurrentRoadDisplayOption, mCurrentBuildingDisplayOption, \
        mCurrentRegionDisplayOption
    tool_set_button_num = 2

    imgui.set_next_window_position(*pos)
    imgui.set_next_window_size(g.DEFAULT_IMAGE_BUTTON_WIDTH + 22,
                               tool_set_button_num * (g.DEFAULT_IMAGE_BUTTON_HEIGHT + 22))
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE
    expanded, _ = imgui.begin('main texture subwindow', False, flags)
    g.mHoveringMainTextureSubWindow = imgui_c.is_hovering_window()
    if imgui.image_button(IconManager.instance.icons['paint-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_style_editor')
    if imgui.is_item_hovered():
        imgui.set_tooltip('显示样式设置')
    if imgui.begin_popup('display_style_editor'):
        g.mHoveringMainTextureSubWindow = True
        StyleManager.instance.display_style.show_imgui_style_editor(
            road_style_change_callback=GraphicManager.instance.main_texture.clear_road_data,
            building_style_change_callback=GraphicManager.instance.main_texture.clear_building_data,
            region_style_change_callback=GraphicManager.instance.main_texture.clear_region_data,
        )
        imgui.end_popup()
    if imgui.image_button(IconManager.instance.icons['stack-fill'], g.DEFAULT_IMAGE_BUTTON_WIDTH,
                          g.DEFAULT_IMAGE_BUTTON_HEIGHT):
        imgui.open_popup('display_layer_editor')
    if imgui.is_item_hovered():
        imgui.set_tooltip('显示图层设置')
    if imgui.begin_popup('display_layer_editor'):
        g.mHoveringMainTextureSubWindow = True
        GraphicManager.instance.main_texture.show_imgui_display_editor()
        imgui.end_popup()
    imgui.end()
