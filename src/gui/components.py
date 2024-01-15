import imgui

mTmpPopupInputValue = ''


def tooltip(content):
    if imgui.is_item_hovered():
        imgui.set_tooltip(content)


def dict_viewer_component(target_dict: dict, dict_name, key_name, value_name, value_op=None, width: float = 0):
    if imgui.begin_table(dict_name, 2, outer_size_width=width):
        imgui.table_setup_column(key_name)
        imgui.table_setup_column(value_name)
        imgui.table_headers_row()
        for key in target_dict.keys():
            imgui.table_next_row()
            imgui.table_next_column()
            imgui.text(str(key))
            imgui.table_next_column()
            value = target_dict[key]
            if value_op is not None:
                value = value_op(value)
            imgui.text(value)
        imgui.end_table()


def dict_viewer_treenode_component(target_dict, dict_name, key_name, value_name, value_op=None):
    if imgui.tree_node(dict_name, flags=imgui.TREE_NODE_DEFAULT_OPEN):
        dict_viewer_component(target_dict, dict_name, key_name, value_name, value_op)
        imgui.tree_pop()


def popup_modal_input_ok_cancel_component(id, button_label, title, content, ok_callback):
    global mTmpPopupInputValue
    imgui.push_id(f'{id}')
    if imgui.button(button_label):
        imgui.open_popup(title)
    if imgui.begin_popup_modal(title).opened:
        imgui.text(content)
        changed, mTmpPopupInputValue = imgui.input_text('', mTmpPopupInputValue)
        imgui.separator()
        if imgui.button('ok'):
            ok_callback(mTmpPopupInputValue)
            mTmpPopupInputValue = ''
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button('cancel'):
            imgui.close_current_popup()
        imgui.end_popup()
    imgui.pop_id()


def is_hovering_window():
    _min = imgui.get_window_position()
    _size = imgui.get_window_size()
    _max = (_min[0] + _size[0], _min[1] + _size[1])
    return imgui.is_mouse_hovering_rect(_min[0], _min[1], _max[0], _max[1])
