import imgui
import pygame
from PIL import Image
from graphic_module import GraphicManager
from geo import Road
from utils import io_utils
from gui import global_var as g
from gui import components as imgui_c

from gui import imgui_main_texture_toolbox_subwindow

mImageWindowSize = (0, 0)
mImageWindowPos = (0, 0)
mImageWindowInnerSize = (0, 0)
mImageWindowInnerPos = (0, 0)
mImageWindowMousePos = (0, 0)



mTextureInfo = {}

print('image window loaded')
def show():
    global mImageWindowSize, mImageWindowPos, mImageWindowInnerSize, \
        mImageWindowInnerPos, mImageWindowMousePos
    screen_width, screen_height = pygame.display.get_window_size()
    flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS
    imgui.set_next_window_size(screen_width - g.LEFT_WINDOW_WIDTH, screen_height - g.BOTTOM_WINDOW_HEIGHT)
    imgui.set_next_window_position(g.LEFT_WINDOW_WIDTH, 0)
    imgui.begin("image window", False, flags=flags)
    mImageWindowPos = (int(imgui.get_window_position()[0]), int(imgui.get_window_position()[1]))
    mImageWindowSize = (int(imgui.get_window_size()[0]), int(imgui.get_window_size()[1]))
    mImageWindowInnerSize = (int(mImageWindowSize[0] - 16), int(mImageWindowSize[1] - g.FONT_SIZE - 18))
    g.mImageSize = (int(mImageWindowInnerSize[0] / g.mTextureScale), int(mImageWindowInnerSize[1] / g.mTextureScale))
    mImageWindowInnerPos = (int(mImageWindowPos[0] + 8), int(mImageWindowPos[1] + g.FONT_SIZE + 18))
    vec1 = (int(imgui.get_mouse_position()[0]), int(imgui.get_mouse_position()[1]))
    vec2 = mImageWindowInnerPos
    mImageWindowMousePos = (vec1[0] - vec2[0], vec1[1] - vec2[1])
    g.mMousePosInImage = (int(mImageWindowMousePos[0] / g.mTextureScale), int(mImageWindowMousePos[1] / g.mTextureScale))
    g.mHoveringImageWindow = imgui_c.is_hovering_window()
    textures_to_delete = set()
    flags = imgui.TAB_BAR_AUTO_SELECT_NEW_TABS | imgui.TAB_BAR_TAB_LIST_POPUP_BUTTON
    with imgui.begin_tab_bar('image_tab_bar', flags=flags):
        for texture in GraphicManager.instance.textures.values():
            if not texture.exposed:
                continue
            selected, opened = imgui.begin_tab_item(texture.name, imgui.TAB_ITEM_TRAILING)
            if selected:
                # IconManager.imgui_icon('fill', width=texture.width*g.mTextureScale, height=texture.height*g.mTextureScale)
                imgui.image(texture.texture_id, texture.width * g.mTextureScale, texture.height * g.mTextureScale)
                if texture.name == 'main':
                    imgui_main_texture_toolbox_subwindow.show(mImageWindowInnerPos)
                mTextureInfo['last updated'] = str(texture.last_update_time)
                mTextureInfo['texture size'] = f"{texture.width} , {texture.height}"
                mTextureInfo['x_lim'] = str(texture.x_lim)
                mTextureInfo['y_lim'] = str(texture.y_lim)
                imgui_c.dict_viewer_component(mTextureInfo, 'texture info', 'key', 'value', None, 800)
                if texture.cached_data is not None:
                    if imgui.button('save'):
                        image = Image.fromarray(texture.cached_data.astype('uint8'))  # 将图像数据缩放到 0-255 范围并转换为 uint8 类型
                        try:
                            image.save(
                                io_utils.save_file_window(defaultextension='.png', filetypes=[('Image File', '.png')]))
                        except:
                            pass
                imgui.end_tab_item()
            if not opened:
                textures_to_delete.add(texture.name)
    imgui.end()

    for name in textures_to_delete:
        GraphicManager.instance.del_texture(name)

