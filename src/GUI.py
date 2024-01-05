import time
import imgui
import pygame
from imgui.integrations.pygame import PygameRenderer
import OpenGL.GL as gl

import sys
import numpy as np
from graphic_module import GraphicManager
from utils import io_utils
from utils import RoadLevel, RoadState
import ctypes

# ctypes.windll.user32.SetProcessDPIAware()  # 禁用dpi缩放

"""
* Powered by DearImGui
* Online Manual - https://pthom.github.io/imgui_manual_online/manual/imgui_manual.html
"""

mDxfPath = r'D:/M.Arch/2024Spr/RoadNetworkOptimization/RoadNetOpt/data/和县/simplified_data.dxf'
mLoadDxfNextFrame = False
mDxfDoc = None
mDxfLayers = None


def imgui_image_window():
    imgui.set_next_window_size(*pygame.display.get_window_size())
    imgui.set_next_window_position(0, 0)
    imgui.begin("image display",
                flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOUSE_INPUTS)
    imgui.image(graphic_manager.texture_id, graphic_manager.width, graphic_manager.height)
    imgui.end()


def imgui_main_window():
    global lst_time
    imgui.set_next_window_size(300, 600)
    expanded, opened = imgui.begin("路网优化开发工具", True)
    imgui.push_id('main_window')
    if expanded:

        frame_time = (time.time() - lst_time)
        lst_time = time.time()
        if frame_time == 0:
            frame_time += 1e-5
        imgui.text(f'fps {(1.0 / frame_time):.1f}')

        imgui_file_op_tree()
        imgui_geo_op_tree()
        imgui_agent_op_tree()
    imgui.pop_id()
    imgui.end()


def imgui_file_op_tree():
    global mDxfPath, mDxfDoc, mLoadDxfNextFrame, mDxfLayers
    imgui.push_id('文件操作')
    if imgui.tree_node('file op'):
        imgui.text('DXF path')
        imgui.push_id('dxf_path')
        changed, mDxfPath = imgui.input_text('', mDxfPath)
        imgui.pop_id()
        imgui.same_line()
        if imgui.button('...'):
            mDxfPath = io_utils.open_file_window()
        if mLoadDxfNextFrame:
            mDxfDoc = io_utils.load_dxf(mDxfPath)
            mDxfLayers = io_utils.get_dxf_layers(mDxfDoc)
            mLoadDxfNextFrame = False
        if imgui.button('Load dxf'):
            imgui.text('loading...')
            mLoadDxfNextFrame = True
        if mDxfDoc is not None:
            imgui.text("dxf loaded")
            imgui.text('road layers')
            target_dict = io_utils.road_layer_mapper
            changed = False
            for key in target_dict.keys():
                # 此段代码有问题
                if changed:
                    break
                imgui.push_id(f'road_layers_{key}')
                level = io_utils.road_layer_mapper[key]
                state = io_utils.road_state_mapper[key]
                changed = imgui_layer_selector_component(label=str(key),
                                               items=mDxfLayers - target_dict.keys(),
                                               callback=lambda new_key:change_dict_key(target_dict, key, new_key))
                if not changed:
                    imgui.same_line()
                    changed = imgui_layer_selector_component(label=str(level),
                                                   items=set(RoadLevel.__members__) - {level},
                                                   callback=lambda new_level:change_dict_value(io_utils.road_layer_mapper, key, new_level))

                imgui.pop_id()
        imgui.tree_pop()
    imgui.pop_id()

def change_dict_key(dict:dict, org_key, new_key):
    print(dict.keys())
    print(org_key in dict)
    org_value = dict[org_key]
    dict.pop(org_key)
    dict[new_key] = org_value

def change_dict_value(dict:dict, key, value):
    dict[key] = value
def imgui_geo_op_tree():
    imgui.push_id('geo_op')
    if imgui.tree_node('geo op'):
        imgui.tree_pop()
    imgui.pop_id()


def imgui_agent_op_tree():
    imgui.push_id('agent_op')
    if imgui.tree_node('agent op'):
        imgui.tree_pop()
    imgui.pop_id()


def imgui_layer_selector_component(label, items, callback):
    if imgui.button(label):
        imgui.open_popup(f'{label} selector')
    if imgui.begin_popup(f'{label} selector'):
        for item in items:
            opened, selected = imgui.selectable(item)
            if selected:
                if callback:
                    callback(item)
                    return True
        imgui.end_popup()
    return False


if __name__ == "__main__":
    pygame.init()
    size = (1920, 1080)
    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption('road net opt window')

    imgui.create_context()
    impl = PygameRenderer()
    io = imgui.get_io()
    io.display_size = size
    font_scaling_factor = 1
    font_size_in_pixels = 16
    chinese_font = io.fonts.add_font_from_file_ttf(
        "../fonts/Unifont.ttf", font_size_in_pixels * font_scaling_factor,
        glyph_ranges=io.fonts.get_glyph_ranges_chinese_full()
    )
    io.font_global_scale /= font_scaling_factor
    impl.refresh_font_texture()

    graphic_manager = GraphicManager()

    lst_time = time.time()
    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            impl.process_event(event)
        impl.process_inputs()
        # update graphic
        time.sleep(0.004)
        # graphic_manager.update()

        # draw imgui windows
        imgui.new_frame()
        with imgui.font(chinese_font):
            imgui_image_window()
            imgui_main_window()

        # render and display
        gl.glClearColor(1, 1, 1, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        pygame.display.flip()
