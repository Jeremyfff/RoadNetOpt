from typing import Optional, Callable

import imgui

from gui import global_var as g
from gui import components as imgui_c

print('debug subwindow loaded')

debug_content: Optional[Callable] = None


def set_debug_content(func: Callable):
    global debug_content
    debug_content = func


def show():
    if g.mDebugWindowOpened:
        expanded, g.mDebugWindowOpened = imgui.begin('调试窗口', True)
        g.mHoveringDebugSubWindow = imgui_c.is_hovering_window()
        if debug_content is not None:
            debug_content()
        else:
            imgui.text('you have not assigned the debug content')
        imgui.end()
