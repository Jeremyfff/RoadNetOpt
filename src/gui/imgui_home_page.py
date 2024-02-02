import imgui
import sys

from gui import global_var as g
from gui import global_info as gi
from gui import components as imgui_c

print('home page loaded')
def show():
    imgui.push_id('home_page')
    imgui.indent()
    imgui.text('')
    imgui.text_wrapped(gi.PRODUCT_NAME)
    imgui.text(f'Version:{gi.RELEASE_VERSION} {gi.LAST_MODIFIED}')
    imgui.text(f'工具作者：{", ".join(gi.AUTHOR)}')
    imgui.text('项目地址: ')
    imgui.text_colored('https://github.com/Jeremyfff/RoadNetOpt', 0.19, 0.53, 0.92, 1.0)
    imgui.text('')
    imgui.separator()

    imgui.text('')
    imgui.text('# 快速开始：')
    imgui.text('    1. 点击上方【路网工具】标签栏')
    imgui.text('    2. 选择data文件')
    imgui.text('    3. 点击【LOAD DATA】')
    imgui.text('    4. 点击【-> All】')
    imgui.text('    5. 点击【自动清理路网】')

    imgui.text('')
    imgui.text('# 操作指引：')
    imgui.text('    - 中键平移')
    imgui.text('    - 滚轮缩放')
    imgui.text('    - 左键选择')
    imgui.text('        - Shift 加减选')
    imgui.text('        - Ctrl 加选')
    imgui.text('')
    imgui.text('# 工具栏（视图左上角）：')
    imgui.text('    - 图层设置')
    imgui.text('    - 样式设置')
    imgui.text('    - 选择设置')
    imgui.text('    - 图像信息')
    imgui.text('    - 图形设置')

    imgui.text('')

    imgui.unindent()
    imgui.pop_id()
