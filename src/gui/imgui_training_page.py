import imgui

print('training page loaded')


def show():
    imgui.push_id('agent_op')
    if imgui.tree_node('agent op'):
        imgui.tree_pop()
    imgui.pop_id()
