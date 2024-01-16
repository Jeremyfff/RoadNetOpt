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
from utils import  io_utils
print('training page loaded')

mRoadInterpolateValue = 0.5
mNewRoads:dict[int, pd.Series] = {}

mRoadAnimationData = {}
mPlayRoadAnmation = False
mNextStepTime = 0
mRoadAnimationStep = 0
def show():
    global mRoadInterpolateValue, mNewRoads, mRoadAnimationData, mNextStepTime, \
        mPlayRoadAnmation,mRoadAnimationStep
    imgui.push_id('agent_op')

    if imgui.tree_node('演示工具'):

        imgui.tree_pop()
    if imgui.tree_node('创建演示文件'):
        _, mRoadInterpolateValue = imgui.slider_float('t', mRoadInterpolateValue, 0, 1)
        if imgui.button('cache'):
            try:
                Road.cache()
            except Exception as e:
                print(str(e))
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
        if imgui.button('delete alley'):
            roads = Road.get_roads_by_attr_and_value('level', RoadLevel.ALLEY)
            for uid, road in roads.iterrows():
                Road.delete_road(road)
        if imgui.button('add new road by selection'):
            try:
                road = list(g.mSelectedRoads.values())[0]
                cut_point = Road.split_road(road, mRoadInterpolateValue, True)

                new_road_uid = Road.add_road_by_coords(cut_point, RoadLevel.BRANCH, RoadState.OPTIMIZING)
                new_road = Road.get_road_by_uid(new_road_uid)
                mNewRoads[len(mNewRoads.keys())] = new_road
                g.mCurrentEditingRoad = new_road
                g.mAddNodeMode = True
                common.clear_selected_roads_and_update_graphic()
            except Exception as e:
                print(str(e))
        if imgui.button('add node to selected road'):
            try:
                road = list(g.mSelectedRoads.values())[0]
                g.mAddNodeMode = True
                g.mCurrentEditingRoad = road
                common.clear_selected_roads_and_update_graphic()
            except Exception as e:
                print(str(e))
        if g.mAddNodeMode:
            if imgui.button('end add mode'):
                g.mAddNodeMode = False
        for i in mNewRoads.keys():
            road = mNewRoads[i]
            imgui.text(f'{i} {road["uid"]}')
        if imgui.button('save new roads'):
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
        if imgui.button('load point sequence'):
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
                mPlayRoadAnmation = True
                mRoadAnimationStep = 0
        road_animation()
        imgui.tree_pop()
    imgui.pop_id()


def road_animation():
    global mRoadAnimationData, mPlayRoadAnmation, mRoadAnimationStep, mNextStepTime
    if not mPlayRoadAnmation:
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
            mPlayRoadAnmation = False
            mNextStepTime = 0
            mRoadAnimationStep = 0

    except Exception as e:
        print(str(e))