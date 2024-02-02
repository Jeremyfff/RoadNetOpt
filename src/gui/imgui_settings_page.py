import importlib
import sys

import imgui
from graphic_module import GraphicManager
from gui import components as imgui_c
from gui import global_var as g
from gui import imgui_style

print('settings page loaded')

mStyleList = ['dark', 'light']
mShowingStyleEditor = False


def show():
    global mShowingStyleEditor
    expanded, visible = imgui.collapsing_header('外观设置')
    if expanded:
        changed, current = imgui.combo('色彩主题', 0 if g.DARK_MODE else 1, mStyleList)
        if changed:
            imgui_style.push_style(True if current == 0 else False)
        if imgui.button('Show Imgui Style Editor'):
            mShowingStyleEditor = True
        if mShowingStyleEditor:
            expanded, mShowingStyleEditor = imgui.begin('Style Editor', True)
            imgui.show_style_editor()
            imgui.end()
        changed, value = imgui.checkbox('启用窗口模糊', g.ENABLE_WINDOW_BLUR)
        if changed:
            g.ENABLE_WINDOW_BLUR = value

        imgui.text('以下选项下次启动生效')
        _, g.GLOBAL_SCALE = imgui.input_float('全局缩放', g.GLOBAL_SCALE)
        _, g._INIT_WINDOW_WIDTH = imgui.input_int('启动窗口宽度', g._INIT_WINDOW_WIDTH)
        _, g._INIT_WINDOW_HEIGHT = imgui.input_int('启动窗口高度', g._INIT_WINDOW_HEIGHT)
        _, g._FONT_SIZE = imgui.input_int('字体大小', g._FONT_SIZE)
        _, g._LEFT_WINDOW_WIDTH = imgui.input_int('左边窗口宽度', g._LEFT_WINDOW_WIDTH)
        _, g._BOTTOM_WINDOW_HEIGHT = imgui.input_int('底部状态栏宽度', g._BOTTOM_WINDOW_HEIGHT)
        _, g.VSYNC = imgui.checkbox('垂直同步', g.VSYNC)

    imgui.separator()
    expanded, visible = imgui.collapsing_header('高级设置')
    if expanded:
        imgui.text('graphic textures')
        imgui.listbox('', 0, [texture.name for texture in GraphicManager.I.textures.values()])
        imgui_c.popup_modal_input_ok_cancel_component('_add_texture', 'add texture', 'name?',
                                                      'please type in texture name',
                                                      lambda name: GraphicManager.I.get_or_create_simple_texture(name))

    imgui.separator()


    if imgui.button('EXIT', width=imgui.get_content_region_available_width(), height=24 * g.GLOBAL_SCALE):
        g.mWindowEvent.wnd.close()
