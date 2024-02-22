import random
import math
import cv2
import numpy as np
from geo import Road, Building, Region
from utils.graphic_uitls import plot_as_array
from utils import io_utils
from utils import RoadState, RoadLevel
import shapely.geometry as geo
import collections
import time


class RoadNet:
    simple_agent = False
    if simple_agent:
        nb_new_roads = 1
    else:
        nb_new_roads = 1
    distance = 80
    if_no_choice_roads = False
    choice = False
    get_image = False
    if_render = False
    # 智能体能活动的画布区域坐标x 在（-40,500）, 坐标y在（-50,500）
    road_net_x_region = [-40, 450]
    road_net_y_region = [-50, 450]



    action_space_bound = np.array([(math.pi, 30)])  # [((-π~π), (-20~20))]
    action_space_boundMove = np.array([(0, 30)])  # [((-π~π), (0~60))]
    observation_space_shape = (128, 128, 3)  # 图像格式

    # uid = '74b974e6-0781-4030-9ad5-184925cc79d1'
    # index = len(current_road_net)
    # i = np.random.randint(0, index)
    # print(i)
    # print(road_start)
    def __init__(self, data):
        self.data = data
        self.current_road_net = 0
        self.ori_road_net = 0
        self.ori_start = 0
        self.ori_start_len = 0

    def restore(self):
        Building.data_to_buildings(self.data)
        Region.data_to_regions(self.data)
        Road.data_to_roads(self.data)
        self.current_road_net = Road.get_all_roads()
        self.ori_road_net = self.current_road_net
        self.ori_start = self.ori_road_net['geometry'].tolist()
        self.ori_start_len = len(self.ori_start)

    def check_line_and_out_random_distance(self, line, distance):
        """判断哪些路可以设置新的路口， 返回bool索引表"""
        if line.length > 2 * distance:
            new_distance = random.uniform(distance, line.length - distance)
            return np.array([new_distance])
        else:
            return np.array([np.nan])

    def out_start_points_by_index(self, index, distance_array):
        # print(index)
        road = self.current_road_net.iloc[index]
        # print(road)
        distance = distance_array[index]
        # print(distance)
        point = Road.split_road(road, distance, normalized=False, update_nodes_immediately=True)
        return point

    def reset(self):
        """初始化新的道路，分随机初始化、选定道路初始化"""
        self.episode_step = 0
        self.point_list = collections.deque(maxlen=3)
        self.restore()

        if not self.choice:
            new_distance = [self.check_line_and_out_random_distance(l, self.distance) for l in self.ori_start]
            new_distance_array = np.concatenate(new_distance, axis=0)  # distance索引表（含nan值）
            new_distance_bool = ~np.isnan(new_distance_array)
            new_distance_index = np.argwhere(new_distance_bool).reshape(-1)  # 可以选择的distance index 索引表
            list_points = []
            # print(f'当前可选道路个数{new_distance_index.shape[0]}')
            if self.nb_new_roads < new_distance_index.shape[0]:
                choice_index = np.random.choice(new_distance_index, size=self.nb_new_roads, replace=False)
                for i in choice_index:
                    point = self.out_start_points_by_index(i, new_distance_array)
                    list_points.append(point)
            else:
                for i in new_distance_index:
                    point = self.out_start_points_by_index(i, new_distance_array)
                    list_points.append(point)

            self.current_road_net = Road.get_all_roads()
            cond = self.current_road_net
            self.road_start = cond['geometry'].tolist()
            self.road_start_len = len(self.road_start)

            for point in list_points:
                Road.add_road_by_coords(coords=point, level=RoadLevel.TERTIARY,
                                        state=RoadState.OPTIMIZING)
            self.last_points = np.concatenate(list_points, axis=0)
            self.point_list.append(self.last_points)
            return self.return_image_observation().transpose((2, 0, 1))

            # print(road_list)
        else:
            pass

    def simple_agent_reset(self):
        self.point_list = collections.deque(maxlen=3)
        self.current_road_net = Road.get_all_roads()
        self.road_start = Road.get_all_roads()['geometry'].tolist()
        # print(f'当前道路个数{self.road_start_len}')
        new_distance = [self.check_line_and_out_random_distance(l, self.distance) for l in self.road_start]
        new_distance_array = np.concatenate(new_distance, axis=0)  # distance索引表（含nan值）
        new_distance_bool = ~np.isnan(new_distance_array)
        new_distance_index = np.argwhere(new_distance_bool).reshape(-1)  # 可以选择的distance index 索引表
        list_points = []
        # print(f'当前可选道路个数{new_distance_index.shape[0]}')
        if self.nb_new_roads < new_distance_index.shape[0]:
            choice_index = np.random.choice(new_distance_index, size=self.nb_new_roads, replace=False)
            for i in choice_index:
                point = self.out_start_points_by_index(i, new_distance_array)
                list_points.append(point)
            self.road_start = Road.get_all_roads()['geometry'].tolist()
            self.road_start_len = len(self.road_start)
            for point in list_points:
                Road.add_road_by_coords(coords=point, level=RoadLevel.TERTIARY,
                                        state=RoadState.OPTIMIZING)
        else:
            self.if_no_choice_roads = True
        self.last_points = np.concatenate(list_points, axis=0)
        self.point_list.append(self.last_points)

    def return_image_observation(self):
        """返回状态，为 图像 格式"""
        roads = Road.get_all_roads()
        buildings = Building.get_all_buildings()
        regions = Region.get_all_regions()

        list_all = [roads, buildings, regions]
        image_data, ax = plot_as_array(list_all, 512, 512,
                                       y_lim=(-100 * 1.2, 400 * 1.2), x_lim=(-100, 450 * 1.2),
                                       transparent=True, antialiased=False)
        # print(image_data.shape)
        return image_data.numpy()

    def render(self):
        # pil_image = Image.fromarray(self.return_image_observation())
        # 显示图像
        cv2.imshow('RoadNetOpt', self.return_image_observation())
        cv2.waitKey(20)

    def step(self, action):
        """返回new_observation, rewards, done, Done"""
        ori_points = self.last_points
        self.episode_step += 1
        # if self.simple_agent:
        #     print(f'现在是第 {self.episode_step} 步')
        # else:
        #     print(f'现在是第 {self.episode_step} 轮')
        i = action
        x_move = np.reshape(np.cos(i[:, 0]) * i[:, 1], (-1, 1))
        y_move = np.reshape(np.sin(i[:, 0]) * i[:, 1], (-1, 1))
        move = np.concatenate((x_move, y_move), axis=1)
        self.last_points = ori_points + move
        self.point_list.append(self.last_points)

        # 给每条路添加新的 最末点， 以此使路网生长
        for i in range(0, self.nb_new_roads):
            agent_road = Road.get_all_roads().iloc[i - self.nb_new_roads]
            my_road = Road.add_point_to_road(agent_road, point=self.last_points[i].reshape((1, 2)))
        # 返回下一时刻状态
        new_observation = self.return_image_observation()
        # 根据下一时刻状态，判断该动作下获得的奖励
        # reward = np.zeros((self.nb_new_roads, 1))
        # 判断单体路生长是否结束
        # print(f'是否走了回头路{self.if_the_way_back()}')
        done, split_list = self.done()
        reward = self.reward(done)
        # 判断路网生长是否结束
        if not self.simple_agent:
            Done = self.Done(done)
        else:
            Done = self.simple_agent_Done()
            if done:
                self.split_road_after_done(split_list)
        # if Done:
        #     self.split_road_after_done(split_list)

        if self.if_render:
            self.render()

        return new_observation.transpose((2, 0, 1)), reward, done, Done

    def reward(self, done):
        # print(self.last_points)
        # return np.zeros((self.nb_new_roads,1))

        # roads = Road.get_all_roads()
        buildings = Building.get_all_buildings()
        regions = Region.get_all_regions()
        min_x, max_x = -100, 450 * 1.2
        min_y, max_y = -100 * 1.2, 400 * 1.2
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
        reward_agent = RewardAgent(points, buire_img.numpy()[:, :, :3])
        back_penalty = np.zeros((self.nb_new_roads, 1)) + self.if_the_way_back() * (-30)  # 加了回头路惩罚， 回头就给-30分
        step_penalty = np.ones((self.nb_new_roads, 1)) * (-1)  # 加了步数惩罚， 促进智能体尽快完成任务
        reward_all = reward_agent.agent_reward() + back_penalty + step_penalty
        return reward_all*(1-done)  # 单条路结束了，此时该路reward就为0

    def if_out_region(self):
        # 定义两个区间的边界
        bins1 = self.road_net_x_region  # 第一个数的区间
        bins2 = self.road_net_y_region  # 第二个数的区间

        # 判断每个数是否在对应的区间内，返回一个0或1的数组
        # 0表示不在区间内，1表示在区间内
        res1 = np.where((self.last_points > bins1[0]) & (self.last_points < bins1[1]), True, False)[:, 0]  # 判断第一列
        res2 = np.where((self.last_points > bins2[0]) & (self.last_points < bins2[1]), True, False)[:, 1]  # 判断第二列

        # 判断每一行是否都为1，即都在区间内，返回一个布尔数组
        done_region = ~np.all(np.stack([res1, res2], axis=1), axis=1).reshape(-1, 1)
        # print(f'是否在设计区域外{done_region}')
        return done_region

    def if_the_way_back(self):
        if len(self.point_list) > 2:
            ori_voc = self.point_list[-2] - self.point_list[-3]
            now_voc = self.point_list[-1] - self.point_list[-2]
            dot = np.dot(ori_voc, now_voc.T)
            dot = np.diag(dot, k=0)
            return (dot < 0).reshape(-1, 1)
        else:
            return np.zeros((self.nb_new_roads, 1))

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
        tolerance = 0.1
        list_done = []
        split_list = []
        for i in range(0, self.nb_new_roads):
            agent_road = self.road_end[ori_len + i].buffer(tolerance)
            num = 0
            split = []
            for j in range(0, ori_len):
                ori_road = self.road_end[j].buffer(tolerance)
                intersection = agent_road.intersection(ori_road)
                if intersection.geom_type == 'Polygon' and not intersection.is_empty:
                    intersect_point = geo.Point(intersection.exterior.coords[0])
                    t = self.road_end[j].project(intersect_point) / self.road_end[j].length
                    if not (t < 0.1 or 1 - t < 0.1):
                        split.append(cond['uid'].iloc[j])
                        split.append(t)
                    num += 1
                elif intersection.geom_type == 'MultiPolygon':
                    for polygon in intersection.geoms:
                        intersect_point = geo.Point(polygon.exterior.coords[0])
                        t = self.road_end[j].project(intersect_point) / self.road_end[j].length
                        if not (t < 0.1 or 1 - t < 0.1):
                            split.append(cond['uid'].iloc[j])
                            split.append(t)
                    num += len(intersection.geoms)
            if num > 2:
                list_done.append(1)
            else:
                list_done.append(0)
            if len(split) != 0:
                split_list.append(split)
        done_region = self.if_out_region()
        done_intersection = np.array(list_done).reshape(-1, 1)
        agent_done = np.logical_or(done_region, done_intersection)
        return agent_done, split_list

    def Done(self, done):
        if np.all(done) or self.episode_step >= 200:
            return True
        else:
            return False

    def simple_agent_Done(self):
        """定义单智能体一个一个训练，判断大循环结束的方法, 目前是超过固定步数 和 没有路可以优化，未来可能会置入密度评价"""
        if self.episode_step >= 200 or self.if_no_choice_roads:
            return True
        else:
            return False

    def split_road_after_done(self, split_list):
        # print(split_list)
        if len(split_list) != 0:
            for split in split_list:
                uid = split[0]
                distance_normalized = split[1]
                road = Road.get_road_by_uid(uid)
                Road.split_road(road, distance_normalized, normalized=True, update_nodes_immediately=True)


# if __name__ == '__main__':
#     data = io_utils.load_data(r"try2.bin")
#     A = RoadNet(data)
#     start = time.perf_counter()
#     A.reset()
#     A.render()
#     if A.simple_agent:
#         done = False
#     else:
#         done = np.zeros((A.nb_new_roads, 1))
#     episode_return = 0
#     for e in range(1000):
#         # a = np.array([(0.3, -0.5), (0.4, 0.2), (0.2, 0)])
#         if A.simple_agent:
#             if not done:
#                 a = np.random.uniform(low=-1, high=1, size=(2,))
#                 b = A.action_space_bound
#                 c = A.action_space_boundMove
#                 a_a = a * b + c
#                 action = a_a.reshape(-1, 2)
#                 next_state, reward, done, Done = A.step(action)
#                 state = next_state
#                 episode_return += reward
#                 print(f'当前奖励{reward}')
#                 print(f'当前累计奖励{episode_return}')
#                 print(f'单路是否结束{done}')
#                 print(f'总体路网是否结束{Done}')
#                 A.render()
#                 if Done:
#                     break
#             else:
#                 print(f'进入下一次择优')
#                 A.simple_agent_reset()
#                 A.render()
#                 a = np.random.uniform(low=-1, high=1, size=(2,))
#                 b = A.action_space_bound
#                 c = A.action_space_boundMove
#                 a_a = a * b + c
#                 action = a_a.reshape(-1, 2)
#                 next_state, reward, done, Done = A.step(action)
#                 state = next_state
#                 episode_return += reward
#                 print(f'当前奖励{reward}')
#                 print(f'当前累计奖励{episode_return}')
#                 print(f'单路是否结束{done}')
#                 print(f'总体路网是否结束{Done}')
#                 A.render()
#                 if Done:
#                     break
#         else:
#             action_list = []
#             for i in range(A.nb_new_roads):
#                 a = np.random.uniform(low=-1, high=1, size=(2,))
#                 b = A.action_space_bound
#                 c = A.action_space_boundMove
#                 a_a = a * b + c
#                 if done[i]:
#                     a_a = np.zeros((1, 2))
#                 action_list.append(a_a)
#             action = np.array(action_list).reshape(-1, 2)  # (3, 2)
#             next_state, reward, done, Done = A.step(action)
#             state = next_state
#             episode_return += reward
#             print(f'当前奖励{reward}')
#             print(f'当前累计奖励{episode_return}')
#             print(f'单路是否结束{done}')
#             print(f'总体路网是否结束{Done}')
#             A.render()
#             if Done:
#                 break
#     # print(Road.get_all_roads())
#     print(Road.get_all_roads())
#     A.reset()
#     print(Road.get_all_roads())
#     end = time.perf_counter()
#     print('Running time: %s Seconds' % (end - start))
