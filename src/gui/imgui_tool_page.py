import imgui
from gui import global_var as g

print('tool page loaded')


def show():
    if imgui.tree_node('[1] DXF工具'):
        if imgui.button('DXF转换工具', width=200 * g.GLOBAL_SCALE, height=32 * g.GLOBAL_SCALE):
            g.mDxfWindowOpened = True
        if imgui.is_item_hovered():
            imgui.set_tooltip('dxf转换工具能够将dxf文件的内容转换\n为本软件所需的二进制文件交换格式')
        imgui.tree_pop()
