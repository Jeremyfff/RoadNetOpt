import os.path
from typing import Optional
import imgui
import osmnx as ox
from pympler.asizeof import asizeof
from graphic_module import GraphicManager
from geo import Road, Building, Region
from utils import io_utils, RoadCluster, BuildingCluster, RegionCluster
from gui.icon_module import IconManager, Spinner
from gui import components as imgui_c
from gui import global_var as g

mRoadGDFCluster = RoadCluster()
mBuildingGDFCluster = BuildingCluster()
mRegionGDFCluster = RegionCluster()

print('geo page loaded')


def show():
    imgui.push_id('geo_page')

    if imgui.tree_node('[1] 加载数据', imgui.TREE_NODE_DEFAULT_OPEN):
        imgui_tree_node_load_data_content()
        imgui.tree_pop()

    if imgui.tree_node('[2] GDF操作工具', imgui.TREE_NODE_DEFAULT_OPEN):
        imgui_tree_node_gdf_ops_content()
        imgui.tree_pop()

    imgui.pop_id()


def imgui_tree_node_load_data_content():
    with imgui.begin_tab_bar('gdf loader'):
        if imgui.begin_tab_item('[1.1] data->GDFs').selected:
            imgui_tab_item_data_to_gdfs_content()
            imgui.end_tab_item()
        if imgui.begin_tab_item('[1.2] OSM->GDFs').selected:
            imgui_tab_item_osm_to_gdfs_content()
            imgui.end_tab_item()


mDataPath = g.DEFAULT_DATA_PATH
mCachedData: Optional[dict] = None
mCachedDataSize: float = 0  # MiB
EMPTY_DATA = {'version': 'N/A', 'roads': 'N/A', 'buildings': 'N/A', 'regions': 'N/A', 'height': 'N/A'}


def _load_data():
    global mCachedData, mCachedDataSize
    mCachedData = io_utils.load_data(mDataPath)
    mCachedDataSize = asizeof(mCachedData) / 1048576  # 1048576 = 1024 * 1024


def imgui_tab_item_data_to_gdfs_content():
    global mDataPath, mCachedData, mCachedDataSize
    imgui.push_id('data_path')
    if not mCachedData:
        imgui.text_colored('请选择并加载数据', 1, 0.4, 0.4, 1)
    else:
        imgui.text('数据已加载')
    changed, mDataPath = imgui.input_text('', mDataPath)
    imgui_c.tooltip(os.path.abspath(mDataPath))
    imgui.pop_id()
    imgui.same_line()
    if imgui.button('...', width=45 * g.GLOBAL_SCALE):
        mDataPath = io_utils.open_file_window()
        g.DEFAULT_DATA_PATH = mDataPath
    imgui_c.tooltip('打开文件浏览器')
    if imgui.button('LOAD DATA', width=300 * g.GLOBAL_SCALE + 16, height=32 * g.GLOBAL_SCALE):
        Spinner.start('load_data', target=_load_data, args=())
    Spinner.spinner('load_data')
    imgui_c.tooltip('将二进制data加载到内存中')
    if imgui.button('Pop Data'):
        mCachedData = {}
        mCachedDataSize = 0
    imgui_c.tooltip('数据转化为GDF后便可以释放了')
    imgui.same_line()
    imgui.text(f'占用内存: {mCachedDataSize:.2f}MB')
    imgui.separator()
    imgui.text('Data数据概览:')
    data_to_display = mCachedData if mCachedData else EMPTY_DATA
    imgui_c.dict_viewer_component(data_to_display, 'Data', 'keys', 'info',
                                  lambda value: f'count={str(len(value))}'
                                  if isinstance(value, list)
                                  else str(value))
    imgui.separator()
    imgui.text('基于data生成GDFs:')
    if not mCachedData:
        imgui.push_style_color(imgui.COLOR_TEXT, 1, 0.4, 0.4, 1)
        imgui.text('没有data!')
        imgui.pop_style_color()
    if imgui.button('->Roads', 100 * g.GLOBAL_SCALE):
        Spinner.start('data_to_road', target=Road.data_to_roads, args=(mCachedData,))
    Spinner.spinner('data_to_road')
    imgui.same_line()
    if imgui.button('->Buildings', 100 * g.GLOBAL_SCALE):
        Spinner.start('data_to_building', target=Building.data_to_buildings, args=(mCachedData,))
    Spinner.spinner('data_to_building')
    imgui.same_line()
    if imgui.button('->Regions', 100 * g.GLOBAL_SCALE):
        Spinner.start('data_to_region', target=Region.data_to_regions, args=(mCachedData,))
    Spinner.spinner('data_to_region')
    if imgui.button('->All', 300 * g.GLOBAL_SCALE + 16, 32 * g.GLOBAL_SCALE):
        Spinner.start('data_to_all', target=lambda _: (
            Road.data_to_roads(mCachedData),
            Building.data_to_buildings(mCachedData),
            Region.data_to_regions(mCachedData),
            GraphicManager.I.MainTexture.clear_cache()
        ), args=(0,))
    Spinner.spinner('data_to_all')

    imgui.text('')


mOSMNorth = 37.79
mOSMSouth = 37.78
mOSMEast = -122.41
mOSMWest = -122.43
mOSMGraph = None
mOSMNetworkTypes = ["all_private", "all", "bike", "drive", "drive_service", "walk"]
mOSMCurrentNetworkTypeIdx = 3


def imgui_tab_item_osm_to_gdfs_content():
    global mOSMNorth, mOSMSouth, mOSMEast, mOSMWest, mOSMGraph, mOSMCurrentNetworkTypeIdx
    imgui.text('使用osmnx下载数据:')
    _, (mOSMNorth, mOSMSouth, mOSMEast, mOSMWest) = imgui.input_float4('NSEW', mOSMNorth, mOSMSouth, mOSMEast,
                                                                       mOSMWest)
    _, mOSMCurrentNetworkTypeIdx = imgui.combo('Network Type', mOSMCurrentNetworkTypeIdx, mOSMNetworkTypes)
    if imgui.button('Download', 260 * g.GLOBAL_SCALE, 32 * g.GLOBAL_SCALE):
        Spinner.start('download_osm', target=
        lambda _: (
            Road.from_graph(ox.graph_from_bbox(mOSMNorth, mOSMSouth, mOSMEast, mOSMWest,
                                               network_type=mOSMNetworkTypes[mOSMCurrentNetworkTypeIdx])),
            GraphicManager.I.MainTexture.clear_x_y_lim()
        ), args=(0,))
    Spinner.spinner('download_osm')


def imgui_tree_node_gdf_ops_content():
    with imgui.begin_tab_bar('geo_op_tab_bar'):
        if imgui.begin_tab_item('Road').selected:
            imgui_tab_item_road_ops_content()
            imgui.end_tab_item()
        if imgui.begin_tab_item('Building').selected:
            imgui_tab_item_building_ops_content()
            imgui.end_tab_item()
        if imgui.begin_tab_item('Region').selected:
            imgui_tab_item_region_ops_content()
            imgui.end_tab_item()
    imgui.text('')


mShowingCloseNodes = False  # 是否正在显示相近的nodes信息
mShowingIntersectionRoads = False  # 是否正在显示相交路网信息
mShowingInvalidRoads = False  # 是否正在显示非法道路
mCachedIntersectionData_uid = None
mCachedIntersectionData_point = None
mCurrentViewingIntersectionData = 0  # 正在浏览第几个交点
mCachedInvalidRoadUids = []
mAnyChangeOnRoad = False  # 当使用工具修改时，该项会被置为True，以提醒刷新相关信息


def imgui_tab_item_road_ops_content():
    global mShowingCloseNodes, mShowingIntersectionRoads, mShowingInvalidRoads
    global mCurrentViewingIntersectionData, mCachedIntersectionData_point, mCachedIntersectionData_uid
    global mCachedInvalidRoadUids
    global mAnyChangeOnRoad
    imgui.text('路网清理工具')
    if imgui.button('自动清理路网', width=300 * g.GLOBAL_SCALE + 16, height=32 * g.GLOBAL_SCALE):
        Road.auto_fix()

    # 相近nodes的显示
    clicked, mShowingCloseNodes = imgui.checkbox('显示相近节点', mShowingCloseNodes)
    clicked |= mAnyChangeOnRoad
    if clicked and mShowingCloseNodes:
        GraphicManager.I.MainTexture.clear_close_node_debug_circles()
        groups = Road.get_close_nodes()
        for _, nodes in groups.items():
            GraphicManager.I.MainTexture.add_close_node_debug_circle(
                *Road.get_nodes_avg_coord(nodes), screen_radius=25, color=(1, 1, 0, 1),
                content='\n'.join([f"coord: {node['coord']}" for _, node in nodes.iterrows()])
            )
    elif clicked and not mShowingCloseNodes:
        GraphicManager.I.MainTexture.clear_close_node_debug_circles()
    # 相交路网的显示
    _idx_changed = False
    clicked, mShowingIntersectionRoads = imgui.checkbox('显示相交路网', mShowingIntersectionRoads)
    clicked |= mAnyChangeOnRoad
    if clicked and mShowingIntersectionRoads:
        GraphicManager.I.MainTexture.clear_intersection_debug_circles()
        mCachedIntersectionData_uid, mCachedIntersectionData_point = \
            Road.detect_intersection(Road.get_all_roads(), Road.get_all_roads())
        _idx_changed = True
    elif clicked and not mShowingIntersectionRoads:
        mCachedIntersectionData_uid = None
        mCachedIntersectionData_point = None
        mCurrentViewingIntersectionData = 0
        g.mSelectedRoads = {}
        GraphicManager.I.MainTexture.clear_intersection_debug_circles()
        GraphicManager.I.MainTexture.clear_highlight_data()
    if mShowingIntersectionRoads and mCachedIntersectionData_uid and mCachedIntersectionData_point:
        imgui.same_line()
        imgui.text(f'{mCurrentViewingIntersectionData}/{len(mCachedIntersectionData_uid)}')
        imgui.same_line()
        if imgui.arrow_button('previous', imgui.DIRECTION_LEFT):
            mCurrentViewingIntersectionData = max(0, mCurrentViewingIntersectionData - 1)
            _idx_changed = True
        imgui.same_line()
        if imgui.arrow_button('next', imgui.DIRECTION_RIGHT):
            mCurrentViewingIntersectionData = min(len(mCachedIntersectionData_uid) - 1,
                                                  mCurrentViewingIntersectionData + 1)
            _idx_changed = True

        if _idx_changed:
            GraphicManager.I.MainTexture.clear_intersection_debug_circles()
            point = mCachedIntersectionData_point[mCurrentViewingIntersectionData]
            uid1 = mCachedIntersectionData_uid[mCurrentViewingIntersectionData][0]
            uid2 = mCachedIntersectionData_uid[mCurrentViewingIntersectionData][1]
            road1 = Road.get_road_by_uid(uid1)
            road2 = Road.get_road_by_uid(uid2)
            g.mSelectedRoads = {road1['uid']: road1, road2['uid']: road2}
            GraphicManager.I.MainTexture.clear_highlight_data()
            GraphicManager.I.MainTexture.add_intersection_debug_circle(
                mCachedIntersectionData_point[mCurrentViewingIntersectionData][0],
                mCachedIntersectionData_point[mCurrentViewingIntersectionData][1],
                8, (1, 1, 1, 1),
                f"{point}\n{uid1}\n{uid2}"
            )
    # 非法路网的显示
    clicked, mShowingInvalidRoads = imgui.checkbox('显示非法路网', mShowingInvalidRoads)
    clicked |= mAnyChangeOnRoad
    if clicked and mShowingInvalidRoads:
        invalid_road_uids = Road.examine_invalid_roads()
        g.mSelectedRoads = {uid: Road.get_road_by_uid(uid) for uid in invalid_road_uids}
        GraphicManager.I.MainTexture.clear_highlight_data()
        mCachedInvalidRoadUids = invalid_road_uids
    if clicked and not mShowingInvalidRoads:
        mShowingInvalidRoads = False
        mCachedInvalidRoadUids = []
        g.mSelectedRoads = {}
        GraphicManager.I.MainTexture.clear_highlight_data()

    mAnyChangeOnRoad = False  # set back to false
    # 各类工具按钮
    if imgui.button('分割相交路网', width=150 * g.GLOBAL_SCALE + 4):
        inter_uid, inter_point = Road.detect_intersection(Road.get_all_roads(), Road.get_all_roads())
        Road.split_roads_by_intersection_data(inter_uid, inter_point)
        mAnyChangeOnRoad |= True
    imgui.same_line()
    if imgui.button('合并相近节点', width=150 * g.GLOBAL_SCALE + 4):
        groups = Road.get_close_nodes()
        for _, nodes in groups.items():
            Road.merge_nodes(nodes)
        Road.clear_unused_nodes()
        mAnyChangeOnRoad |= True
    if imgui.button('简化道路节点', width=150 * g.GLOBAL_SCALE + 4):
        Road.simplify_roads()
        mAnyChangeOnRoad |= True
    imgui.same_line()
    if imgui.button('删除非法道路', width=150 * g.GLOBAL_SCALE + 4):
        invalid_road_uids = Road.examine_invalid_roads()
        Road.delete_roads_by_uids_list(invalid_road_uids)
        mAnyChangeOnRoad |= True
    # 工具按钮结束

    imgui.text('选择工具')
    imgui.text('current selected: 0')
    mRoadGDFCluster.show_imgui_cluster_editor_button()
    imgui.text('详细操作')
    if imgui.tree_node('创建删除'):
        imgui.tree_pop()
    if imgui.tree_node('获取查找'):
        imgui.tree_pop()
    if imgui.tree_node('编辑修改'):
        imgui.button('add point to road')
        imgui.button('add points to road')
        imgui.button('split road')
        imgui.button('merge road')

        imgui.tree_pop()
    if imgui.tree_node('绘图相关'):
        imgui.tree_pop()
    if imgui.tree_node('类型转换'):
        imgui.tree_pop()
    if imgui.tree_node('其他工具'):
        imgui.tree_pop()


def imgui_tab_item_building_ops_content():
    imgui.text('1. 选择工具')
    imgui.text('current selected: 0')
    mBuildingGDFCluster.show_imgui_cluster_editor_button()
    imgui.text('2. 详细操作')
    if imgui.tree_node('创建删除'):
        imgui.tree_pop()
    if imgui.tree_node('获取查找'):
        imgui.tree_pop()
    if imgui.tree_node('编辑修改'):
        imgui.tree_pop()
    if imgui.tree_node('绘图相关'):
        imgui.tree_pop()
    if imgui.tree_node('类型转换'):
        imgui.tree_pop()
    if imgui.tree_node('其他工具'):
        imgui.tree_pop()


def imgui_tab_item_region_ops_content():
    imgui.text('1. 选择工具')
    imgui.text('current selected: 0')
    mRegionGDFCluster.show_imgui_cluster_editor_button()
    imgui.text('2. 详细操作')
    if imgui.tree_node('创建删除'):
        imgui.tree_pop()
    if imgui.tree_node('获取查找'):
        imgui.tree_pop()
    if imgui.tree_node('编辑修改'):
        imgui.tree_pop()
    if imgui.tree_node('绘图相关'):
        imgui.tree_pop()
    if imgui.tree_node('类型转换'):
        imgui.tree_pop()
    if imgui.tree_node('其他工具'):
        imgui.tree_pop()
