import os
import pickle
import typing
import imgui
import numpy as np
import pandas as pd

from graphic_module import GraphicManager
from gui import global_var as g
from gui import common
from geo import Road, Building, Region
from utils import RoadLevel, RoadState
from utils import io_utils, graphic_uitls
from gui.animation_module import Animation
from DDPG import env2 as env

print('training page loaded')

mSelectStartPointMode = False
mRoadInterpolateValue = 0.5
mNewRoads: dict[int, pd.Series] = {}

mRoadPtSeqData: list = []
mRoadAnimationData: dict = {}
mRoadGrowAnimation: Animation = Animation.blank()

mRoadNet: typing.Union[env.RoadNet, None] = None
mRoadNetDone: typing.Union[np.ndarray, None] = None
mRoadNetEpisodeReturn: float = 0
mRoadNetState = None
mRoadNetAnimation: Animation = Animation.blank()
mRoadNetAnimationTimeGap = 0.5


def show():
    global mRoadInterpolateValue, mNewRoads, mRoadPtSeqData, mRoadAnimationData, mRoadGrowAnimation, \
        mSelectStartPointMode, \
        mRoadNet, mRoadNetDone, mRoadNetEpisodeReturn, mRoadNetAnimation, mRoadNetAnimationTimeGap
    imgui.push_id('agent_op')

    if imgui.tree_node('快捷工具'):
        if imgui.button('cache'):
            Road.cache()
        imgui.same_line()
        if imgui.button('restore'):
            Road.restore()
            mNewRoads = {}
        if imgui.button('delete branch'):
            roads = Road.get_roads_by_attr_and_value('level', RoadLevel.BRANCH)
            for uid, road in roads.iterrows():
                Road.delete_road(road)
        imgui.same_line()
        if imgui.button('delete alley'):
            roads = Road.get_roads_by_attr_and_value('level', RoadLevel.ALLEY)
            for uid, road in roads.iterrows():
                Road.delete_road(road)
        imgui.tree_pop()

    if imgui.tree_node('训练工具', flags=imgui.TREE_NODE_DEFAULT_OPEN):
        _, mRoadNetAnimationTimeGap = imgui.slider_float('animation time gap', mRoadNetAnimationTimeGap, 0, 1)
        if imgui.button('Load Data'):
            _ = io_utils.load_data('../data/VirtualEnv/try2.bin')
            Building.data_to_buildings(_)
            Region.data_to_regions(_)
            Road.data_to_roads(_)

        if imgui.button('Create RoadNet'):
            mRoadNet = env.RoadNet()
            mRoadNetAnimation = Animation(body_func=road_net_play_func,
                                          reset_func=road_net_reset_func,
                                          time_gap=mRoadNetAnimationTimeGap)
            mRoadNetAnimation.reset()

        if imgui.button('Play Animation'):
            mRoadNetAnimation.start()
        if imgui.button('Reset Animation'):
            mRoadNetAnimation.reset()
        mRoadNetAnimation.show()

        imgui.tree_pop()

    if imgui.tree_node('创建演示文件'):
        # 绘制图形
        imgui.separator()
        expanded, visible = imgui.collapsing_header('道路新建与编辑工具', flags=imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:

            if mSelectStartPointMode:
                try:
                    imgui.text('您正在选择新建道路的起点')
                    _, mRoadInterpolateValue = imgui.slider_float('位置', mRoadInterpolateValue, 0, 1)
                    geo = g.mCurrentEditingRoad['geometry']
                    cut_point = geo.interpolate(mRoadInterpolateValue, True)
                    cut_point_tuple = tuple(cut_point.coords)[0]
                    screen_point_local = \
                        graphic_uitls.world_space_to_image_space(cut_point_tuple[0],
                                                                 cut_point_tuple[1],
                                                                 GraphicManager.instance.main_texture.x_lim,
                                                                 GraphicManager.instance.main_texture.y_lim,
                                                                 g.mImageWindowInnerSize[0],
                                                                 g.mImageWindowInnerSize[1])
                    screen_point = (screen_point_local[0] + g.mImageWindowInnerPos[0],
                                    screen_point_local[1] + g.mImageWindowInnerPos[1])

                    draw_list = imgui.get_overlay_draw_list()
                    draw_list.add_circle_filled(screen_point[0], screen_point[1], 5,
                                                imgui.get_color_u32_rgba(1, 1, 0, 1))

                    if imgui.button('确认起点', 300 * g.GLOBAL_SCALE, 24 * g.GLOBAL_SCALE):
                        cut_point_array = np.array([[cut_point_tuple[0], cut_point_tuple[1]]])
                        new_road_uid = Road.add_road_by_coords(cut_point_array, RoadLevel.BRANCH, RoadState.OPTIMIZING)
                        new_road = Road.get_road_by_uid(new_road_uid)
                        mNewRoads[len(mNewRoads.keys())] = new_road
                        g.mCurrentEditingRoad = new_road
                        g.mAddNodeMode = True
                        mSelectStartPointMode = False
                        common.clear_selected_roads_and_update_graphic()
                except Exception as e:
                    print(e)

            if g.mAddNodeMode:
                imgui.text('请鼠标左键单击以添加点')
                if imgui.button('完成(Enter)', 300 * g.GLOBAL_SCALE, 24 * g.GLOBAL_SCALE):
                    g.mAddNodeMode = False

            if not mSelectStartPointMode and not g.mAddNodeMode:
                if imgui.button('在已选择的道路上新增道路'):
                    if len(g.mSelectedRoads.values()) > 0:
                        mSelectStartPointMode = True
                        g.mCurrentEditingRoad = list(g.mSelectedRoads.values())[0]

                if imgui.button('添加点至选中道路'):
                    try:
                        road = list(g.mSelectedRoads.values())[0]
                        g.mAddNodeMode = True
                        g.mCurrentEditingRoad = road
                        common.clear_selected_roads_and_update_graphic()
                    except Exception as e:
                        print(str(e))

        imgui.separator()
        imgui.text('保存与加载工具: ')
        if imgui.button('保存new points'):
            # 这里不能用原始的road对象，因为road增加点后没有更新，应该重新根据uid查找一遍
            mRoadPtSeqData = [list(Road.get_road_by_uid(road["uid"])['geometry'].coords) for road in
                              mNewRoads.values()]

            file_path = io_utils.save_file_window(defaultextension='.ptseq',
                                                  filetypes=[('Point Sequence', '.ptseq')])
            if file_path is None or file_path == '':
                return

            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'wb') as file:
                pickle.dump(mRoadPtSeqData, file)
            print(f'Point Sequence saved to {file_path}')
        imgui.same_line()
        if imgui.button('加载序列'):
            file_path = io_utils.open_file_window(filetypes=[('Point Sequence', '.ptseq')])
            print(f'loading ptseq from {file_path}')
            if file_path is None or file_path == '':
                return
            with open(file_path, 'rb') as file:
                mRoadPtSeqData = pickle.load(file)
                print(f'found {len(mRoadPtSeqData)} roads in file')
                mRoadGrowAnimation = Animation(body_func=road_grow_animation_body_func,
                                               reset_func=road_grow_animation_reset_func,
                                               time_gap=0.5)
                mRoadGrowAnimation.reset()

        if len(mRoadAnimationData) > 0:
            if imgui.button('play'):
                mRoadGrowAnimation.start()
            if imgui.button('reset'):
                mRoadGrowAnimation.reset()
        mRoadGrowAnimation.show()

        imgui.separator()
        imgui.text('新创建的道路: ')
        for i in mNewRoads.keys():
            road = mNewRoads[i]
            imgui.text(f'{i} {road["uid"]}')

        imgui.tree_pop()

    imgui.pop_id()


def road_grow_animation_reset_func():
    global mRoadAnimationData, mNewRoads
    mRoadAnimationData = {i: pt_seq for i, pt_seq in enumerate(mRoadPtSeqData)}

    for road in mNewRoads.values():
        Road.delete_road(Road.get_road_by_uid(road['uid']))
    mNewRoads = {}
    GraphicManager.instance.main_texture.clear_road_data_deep()


def road_grow_animation_body_func(step: int) -> bool:
    global mRoadAnimationData
    try:
        count = 0
        for i in mRoadAnimationData.keys():
            pt_seq = mRoadAnimationData[i]
            if step >= len(pt_seq):
                continue
            pt = pt_seq[step]
            pt = np.array([[pt[0], pt[1]]])
            if step == 0:
                uid = Road.add_road_by_coords(pt, RoadLevel.BRANCH, RoadState.OPTIMIZING)
                road = Road.get_road_by_uid(uid)
                mNewRoads[i] = road
            else:
                mNewRoads[i] = Road.add_point_to_road(mNewRoads[i], pt)
            count += 1
        GraphicManager.instance.main_texture.clear_road_data_deep()
        if count == 0:
            return True
        return False

    except Exception as e:
        print(e)
        return True


def road_net_reset_func():
    global mRoadNet, mRoadNetDone, mRoadNetEpisodeReturn
    mRoadNet.reset()
    mRoadNetDone = np.zeros((mRoadNet.nb_new_roads, 1))
    mRoadNetEpisodeReturn = 0
    GraphicManager.instance.bilt_to('RoadNet', mRoadNet.return_image_observation())
    print('road net reset')


def road_net_play_func(step: int) -> bool:
    global mRoadNet, mRoadNetDone, mRoadNetEpisodeReturn, mRoadNetState
    try:
        _ = step
        action_list = []
        for i in range(mRoadNet.nb_new_roads):
            a = np.random.uniform(low=-1, high=1, size=(2,))
            b = mRoadNet.action_space_bound
            c = mRoadNet.action_space_boundMove
            a_a = a * b + c
            if mRoadNetDone[i]:
                a_a = np.zeros((1, 2))
            action_list.append(a_a) 
        action = np.array(action_list).reshape(-1, 2)  # (3, 2)
        next_state, rewards, done, Done = mRoadNet.step(action)
        mRoadNetState = next_state
        mRoadNetEpisodeReturn += rewards
        GraphicManager.instance.bilt_to('RoadNet', mRoadNet.return_image_observation())
        return Done

    except IndexError:
        return True
