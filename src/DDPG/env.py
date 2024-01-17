import os.path
import random
import math
import cv2
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from geo import Road, Building, Region, Object
from utils.graphic_uitls import plot_as_array
from utils import point_utils, image_utils, road_utils, io_utils
from utils import RoadState, RoadLevel
from optimize_module import RoadOptimizer
from fields import BuildingField, AttractionField, DirectionField, MomentumField, RandomField
import examples as ex
import geopandas as gpd
import shapely.geometry as geo

data = io_utils.load_data(r"try2.bin")
Building.data_to_buildings(data)
Region.data_to_regions(data)
Road.data_to_roads(data)
class RoadNet:
    nb_new_roads = 3
    distance = 80
    choice = False
    get_image =False
    if_render = False
    # 智能体能活动的画布区域坐标x 在（-20,480）, 坐标y在（-50,420）
    road_net_x_region = [-40*0.7, 400*0.7]
    road_net_y_region = [-50*0.7, 400*0.7]

    action_space_bound = np.array([(math.pi, 30)])  # [((-π~π), (-20~20))]
    action_space_boundMove = np.array([(0, 30)])  # [((-π~π), (0~60))]
    observation_space_shape = (128, 128, 3)  # 图像格式
    # uid = '74b974e6-0781-4030-9ad5-184925cc79d1'
    # index = len(current_road_net)
    # i = np.random.randint(0, index)
    # print(i)
    # print(road_start)
    def __init__(self):
        current_road_net = Road.get_all_roads()
        cond = current_road_net
        self.road_start = cond['geometry'].tolist()
        self.road_start_len = len(self.road_start)
    def check_line_and_out_random_point(self, line, distance):
        """判断哪些路可以设置新的路口， 返回bool索引表"""
        if line.length > 2*distance:
            new_points = [line.interpolate(distance), line.interpolate(line.length-distance)]
            new_line = geo.LineString(new_points)
            point = new_line.interpolate(random.uniform(0, new_line.length))
            return np.array([(point.x, point.y)])
        else:
            return np.array([(np.nan, np.nan)])

    def reset(self):
        """初始化新的道路，分随机初始化、选定道路初始化"""
        self.episode_step = 0
        if not self.choice:
            point = [self.check_line_and_out_random_point(l, self.distance) for l in self.road_start]
            points_array = np.concatenate(point, axis=0)
            points_bool = ~np.isnan(points_array)
            start_points_for_choice = np.reshape(points_array[points_bool], (-1, 2))
            if self.nb_new_roads < start_points_for_choice.shape[0]:
                self.last_points = start_points_for_choice[np.random.choice(start_points_for_choice.shape[0],
                                                                  size=self.nb_new_roads,
                                                                  replace=False), :]
            else:
                self.last_points  = start_points_for_choice
            for i in range(0, self.last_points.shape[0]):
                Road.add_road_by_coords(coords=self.last_points [i].reshape((1,2)), level=RoadLevel.BRANCH,
                                                          state=RoadState.OPTIMIZING)
        else:
            pass
    
    def return_image_observation(self):
        """返回状态，为 图像 格式"""
        roads = Road.get_all_roads()
        buildings = Building.get_all_buildings()
        regions = Region.get_all_regions()

        list_all = [roads, buildings, regions]
        image_data, ax = plot_as_array(list_all, 512, 512,
                      y_lim=(-100*1.2,400*1.2), x_lim=(-100,450*1.2),
                      transparent=True, antialiased=False)
        # print(image_data.shape)
        return image_data.numpy()

    def render(self):
        # pil_image = Image.fromarray(self.return_image_observation())
        # 显示图像
        cv2.imshow('RoadNetOpt', self.return_image_observation())
        cv2.waitKey(1)

    def step(self, action):
        """返回new_observation, rewards, done, Done"""
        points = self.last_points
        self.episode_step += 1
        # print(points)
        i = action
        x_move = np.reshape(np.cos(i[:, 0]) * i[:, 1], (-1, 1))
        y_move = np.reshape(np.sin(i[:, 0]) * i[:, 1], (-1, 1))
        move = np.concatenate((x_move, y_move), axis=1)
        self.last_points = points + move
        # 给每条路添加新的 最末点， 以此使路网生长
        for i in range(0, self.nb_new_roads):
            agent_road = Road.get_all_roads().iloc[i-3]
            my_road = Road.add_point_to_road(agent_road, point=self.last_points[i].reshape((1, 2)))
        # 返回下一时刻状态
        new_observation = self.return_image_observation()
        # 根据下一时刻状态，判断该动作下获得的奖励
        reward = self.reward()
        # 判断路网生长是否结束
        done = self.done()
        Done = self.Done(done)


        if self.if_render:
            self.render()

        return new_observation, reward, done, Done

    def reward(self):
        # print(self.last_points)
        # return np.zeros((self.nb_new_roads,1))

        # roads = Road.get_all_roads()
        buildings = Building.get_all_buildings()
        regions = Region.get_all_regions()
        min_x, max_x = -100,450*1.2
        min_y, max_y = -100*1.2,400*1.2
        min, max = 0, 512
        # list_road = [roads]
        # road_img, ax = plot_as_array(list_road, 512, 512,
        #               y_lim=(-100*1.2,400*1.2), x_lim=(-100,450*1.2),
        #               transparent=True, antialiased=False)     
        list_buire = [buildings, regions]
        buire_img, ax = plot_as_array(list_buire, max, max,
                      y_lim=(min_y, max_y), x_lim=(min_x, max_x),
                      transparent=True, antialiased=False)
        
        scaled_points_x = np.interp(self.last_points[:, 0], (min_x, max_x), (min, max))
        scaled_points_y = np.interp(self.last_points[:, 1], (min_y, max_y), (min, max))
        points = np.column_stack((scaled_points_x, scaled_points_y))
        from DDPG.reward_agent import RewardAgent
        rewardagent = RewardAgent(points,buire_img.numpy()[:, :, :3])
        return rewardagent.agent_reward()

    def done(self):
        """
        判断每一个新状态下每个小智能体的游戏是否结束,
        暂定为和再次和其他路相交（不包含智能体创造的新路）、超过一定区域（否则图像状态的缩放会改变）
        返回值为numpy.ndarray, shape=[nb_new_roads,1]
        """
        current_road_net = Road.get_all_roads()
        cond = current_road_net
        ori_len = self.road_start_len
        self.road_end = cond['geometry'].tolist()
        tolerance = 0.8
        list_done = []
        for i in range(0, self.nb_new_roads):
            agent_road = self.road_end[ori_len+i].buffer(tolerance)
            num = 0
            for j in range(0,ori_len):
                ori_road = self.road_end[j].buffer(tolerance)
                intersection = agent_road.intersection(ori_road)
                # print(type(intersection))
                if intersection.geom_type == 'Polygon' and not intersection.is_empty:
                    num += 1
                elif intersection.geom_type == 'MultiPolygon':
                    num += len(intersection.geoms)
            # print(num)
            if num > 1:
                list_done.append(1)
            else:
                list_done.append(0)
            # print(list_ints)

        # 定义两个区间的边界
        bins1 = self.road_net_x_region # 第一个数的区间
        bins2 = self.road_net_y_region  # 第二个数的区间

        # 判断每个数是否在对应的区间内，返回一个0或1的数组
        # 0表示不在区间内，1表示在区间内
        res1 = np.digitize(self.last_points[:, 0], bins1)  # 判断第一列
        res2 = np.digitize(self.last_points[:, 1], bins2)  # 判断第二列

        # 判断每一行是否都为1，即都在区间内，返回一个布尔数组
        done_region = ~np.all(np.stack([res1, res2], axis=1), axis=1).reshape(-1, 1)
        done_intersection = np.array(list_done).reshape(-1, 1)
        agent_done = np.logical_or(done_region, done_intersection)
        return agent_done

    def Done(self, done):
        if np.all(done) or self.episode_step > 200:
            return True
        else:
            return False


import time
A = RoadNet()
print(A.road_start)
start =time.perf_counter()
state = A.reset()
A.render()
done = np.zeros((A.nb_new_roads,1))
episode_return = 0
for e in range(10):
    # a = np.array([(0.3, -0.5), (0.4, 0.2), (0.2, 0)])
    action_list = []
    for i in range(A.nb_new_roads):
        a = np.random.uniform(low=-1, high=1, size=(2,))
        b = A.action_space_bound
        c = A.action_space_boundMove
        a_a = a * b + c
        if done[i]:
            a_a = np.zeros((1,2))
        action_list.append(a_a)
    action = np.array(action_list).reshape(-1, 2)  #(3, 2)
    next_state, rewards, done, Done = A.step(action)
    state = next_state
    episode_return += rewards
    print('aaaaaaaaaaaaaaaa')
    # print(action)
    # print(done)
    A.render()
    print(Done)
    if Done:
        break
    print(f'现在是第 {A.episode_step} 轮')
end = time.perf_counter()

# print(A.road_start_len)
print('Running time: %s Seconds'%(end-start))

