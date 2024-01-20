import imgui
from utils import io_utils
from gui import global_var as g
from gui import components as imgui_c



mDxfPath = r'../data/和县/simplified_data.dxf'
mLoadDxfNextFrame = False
mDxfDoc = None
mDxfLayers = None


print('dxf subwindow loaded')
def show():
    global mDxfPath, mDxfDoc, mLoadDxfNextFrame, mDxfLayers

    if g.mDxfWindowOpened:
        expanded, g.mDxfWindowOpened = imgui.begin('dxf文件转换工具', True)
        g.mHoveringDxfSubWindow = imgui_c.is_hovering_window()
        imgui.text('您需要将dxf文件中的地形 block 炸开')
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
            if imgui.tree_node('layer mappings[readonly]'):
                imgui.text_wrapped('暂不支持动态更改，请前往utils.io_utils.py编辑修改')
                target_dicts = [io_utils.road_layer_mapper,
                                io_utils.road_state_mapper,
                                io_utils.building_movable_mapper,
                                io_utils.building_style_mapper,
                                io_utils.building_quality_mapper,
                                io_utils.region_accessible_mapper,
                                io_utils.region_type_mapper]
                target_dict_names = ['road_level',
                                     'road_state',
                                     'building_movable',
                                     'building_style',
                                     'building_quality',
                                     'region_accessible',
                                     'region_type']
                for dict_idx in range(len(target_dicts)):
                    target_dict = target_dicts[dict_idx]
                    target_dict_name = target_dict_names[dict_idx]
                    imgui_c.dict_viewer_treenode_component(target_dict, target_dict_name, 'dxf_layer', target_dict_name,
                                                         value_op=lambda value: str(value).split('.')[-1])
                imgui.tree_pop()
            if imgui.button('convert to data and save'):
                data = io_utils.dxf_to_data(mDxfDoc)
                io_utils.save_data(data, io_utils.save_file_window(defaultextension='.bin',
                                                                   filetypes=[('Binary Files', '.bin')]))
            if imgui.button('release dxf'):
                mDxfDoc = None
        imgui.end()
