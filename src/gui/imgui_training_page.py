import os
import pickle
import time

import imgui
import numpy as np
import pandas as pd

from graphic_module import GraphicManager
from gui import global_var as g
from gui import common
from geo import Road
from utils import RoadLevel, RoadState
from utils import io_utils, graphic_uitls

print('training page loaded')

mSelectStartPointMode = False
mRoadInterpolateValue = 0.5
mNewRoads: dict[int, pd.Series] = {}

mRoadAnimationData = {}

mPlayRoadAnimation = False
mNextStepTime = 0
mRoadAnimationStep = 0


def show():
    global mRoadInterpolateValue, mNewRoads, mRoadAnimationData, mNextStepTime, \
        mPlayRoadAnimation, mRoadAnimationStep, mSelectStartPointMode
    imgui.push_id('agent_op')

    if imgui.tree_node('演示工具'):
        imgui.tree_pop()
    if imgui.tree_node('创建演示文件'):

        if imgui.button('cache'):
            try:
                Road.cache()
            except Exception as e:
                print(str(e))
        imgui.same_line()
        if imgui.button('restore'):
            try:
                Road.restore()
                mNewRoads = {}
            except Exception as e:
                print(str(e))

        if imgui.button('delete branch'):
            roads = Road.get_roads_by_attr_and_value('level', RoadLevel.BRANCH)
            for uid, road in roads.iterrows():
                Road.delete_road(road)
        imgui.same_line()
        if imgui.button('delete alley'):
            roads = Road.get_roads_by_attr_and_value('level', RoadLevel.ALLEY)
            for uid, road in roads.iterrows():
                Road.delete_road(road)
        # 绘制图形
        imgui.separator()
        expanded, visible = imgui.collapsing_header('道路新建与编辑工具', flags = imgui.TREE_NODE_DEFAULT_OPEN)
        if expanded:

            if mSelectStartPointMode:
                try:
                    imgui.text('您正在选择新建道路的起点')
                    _, mRoadInterpolateValue = imgui.slider_float('位置', mRoadInterpolateValue, 0, 1)
                    geo = g.mCurrentEditingRoad['geometry']
                    cut_point = geo.interpolate(mRoadInterpolateValue, True)
                    cut_point_tuple = tuple(cut_point.coords)[0]
                    screen_point_local = graphic_uitls.world_space_to_image_space(cut_point_tuple[0],
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
                if imgui.button('完成', 300 * g.GLOBAL_SCALE, 24 * g.GLOBAL_SCALE):
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
        for i in mNewRoads.keys():
            road = mNewRoads[i]
            imgui.text(f'{i} {road["uid"]}')

        imgui.separator()
        if imgui.button('保存new points'):
            # 这里不能用原始的road对象，因为road增加点后没有更新，应该重新根据uid查找一遍
            data = [list(Road.get_road_by_uid(road["uid"])['geometry'].coords) for road in mNewRoads.values()]

            file_path = io_utils.save_file_window(defaultextension='.ptseq',
                                                  filetypes=[('Point Sequence', '.ptseq')])
            if file_path is None or file_path == '':
                return

            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'wb') as file:
                pickle.dump(data, file)
            print(f'Point Sequence saved to {file_path}')
        imgui.same_line()
        if imgui.button('加载序列'):
            file_path = io_utils.open_file_window(filetypes=[('Point Sequence', '.ptseq')])
            print(f'loading ptseq from {file_path}')
            if file_path is None or file_path == '':
                return
            with open(file_path, 'rb') as file:
                data: list = pickle.load(file)
                print(f'found {len(data)} roads in file')
                mRoadAnimationData = {i: pt_seq for i, pt_seq in enumerate(data)}
                for road in mNewRoads.values():
                    Road.delete_road(Road.get_road_by_uid(road['uid']))
                mNewRoads = {}
                mNextStepTime = 0
                mPlayRoadAnimation = False
                mRoadAnimationStep = 0
        if len(mRoadAnimationData) > 0:
            if imgui.button('play'):
                mPlayRoadAnimation = True
        road_animation()
        imgui.tree_pop()
    imgui.pop_id()


def road_animation():
    global mRoadAnimationData, mPlayRoadAnimation, mRoadAnimationStep, mNextStepTime
    if not mPlayRoadAnimation:
        return
    if time.time() < mNextStepTime:
        return
    try:
        if len(mRoadAnimationData.keys()) > 0:
            print(f'step = {mRoadAnimationStep}')
            for i in mRoadAnimationData.keys():
                pt_seq = mRoadAnimationData[i]
                if mRoadAnimationStep >= len(pt_seq):
                    mRoadAnimationData.pop(i)
                    print(f'{i} 结束')
                    continue
                pt = pt_seq[mRoadAnimationStep]
                pt = np.array([[pt[0], pt[1]]])
                if mRoadAnimationStep == 0:
                    uid = Road.add_road_by_coords(pt, RoadLevel.BRANCH, RoadState.OPTIMIZING)
                    road = Road.get_road_by_uid(uid)
                    mNewRoads[i] = road
                else:
                    mNewRoads[i] = Road.add_point_to_road(mNewRoads[i], pt)
            mRoadAnimationStep += 1
            mNextStepTime = time.time() + 0.5
            GraphicManager.instance.main_texture.clear_road_data_deep()
        else:
            mRoadAnimationData = {}
            mPlayRoadAnimation = False
            mNextStepTime = 0
            mRoadAnimationStep = 0

    except Exception as e:
        print(str(e))
