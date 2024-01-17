import imgui
import sys

from gui import global_var as g
from gui import components as imgui_c

print('home page loaded')
def show():
    imgui.push_id('home_page')
    imgui.text("Welcome to road net opt")
    imgui.text_wrapped("交互式街区路网织补工具")
    imgui.text('version:2024.1.13')
    imgui.text('工具作者：冯以恒， 武文忻， 邱淑冰')
    imgui.text('使用帮助：')
    imgui.text('请点击geo标签栏')

    imgui.pop_id()
