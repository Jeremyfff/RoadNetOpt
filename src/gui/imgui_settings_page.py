import sys

import imgui
from graphic_module import GraphicManager
from gui import components as imgui_c
from gui import global_var as g

print('settings page loaded')
def show():
    imgui.show_style_selector('style selector')
    if imgui.tree_node('graphic settings'):
        imgui.text('graphic textures')
        imgui.listbox('', 0, [texture.name for texture in GraphicManager.instance.textures.values()])
        imgui_c.popup_modal_input_ok_cancel_component('_add_texture', 'add texture', 'name?',
                                                      'please type in texture name',
                                                      lambda name: GraphicManager.instance.get_or_create_texture(name))
        imgui.tree_pop()
    if imgui.tree_node('style settings'):
        imgui.show_style_editor()
        imgui.tree_pop()
    if imgui.button('show user guide'):
        imgui.show_user_guide()
    if imgui.button('show demo window'):
        imgui.show_demo_window()
    if imgui.button('show about window'):
        imgui.show_about_window()

    if imgui.button('exit', width=200*g.GLOBAL_SCALE, height=24*g.GLOBAL_SCALE):
        sys.exit(0)
    _, g.mTextureScale = imgui.slider_float('target texture scale', g.mTextureScale, 0.5, 10)
