import math
import traceback
import uuid
from typing import Union
import numpy as np
import pandas as pd
import geopandas as gpd
from geo import Road, Building, Region
from utils.graphic_uitls import plot_as_array
from utils import point_utils, io_utils
from utils import RoadState, RoadLevel
from graphic_module import GraphicManager
from DDPG.reward_agent import RewardAgent

print('env2 loaded')


class RoadNet:
    def __init__(self, num_agents, max_episode_step=200, region_min=(-40, -50), region_max=(500, 500)):
        # 将之前的静态变量变为在RoadNet初始化时可以设置
        self.num_agents = num_agents  # 在RoadNet层面无需区分是多个一起还是一个一个，在后面使用不同的reset策略即可
        self.max_episode_step = max_episode_step  # 在这里限制最大步数
        self.region_min = region_min  # 即原来的road_net_x_region 和 road_net_y_region
        self.region_max = region_max

        self.action_space_bound = np.array([(math.pi, 30)])  # [((-π~π), (-30~30))]
        self.action_space_boundMove = np.array([(0, 30)])  # [((-π~π), (0~60))]
        self.observation_space_shape = (512, 512, 4)  # [height, width, channel]

        self.episode_step: int = 0  # 当前步数
        self.raw_roads: gpd.GeoDataFrame = Road.get_all_roads()  # 保存原有道路， 分裂后的新道路不在其中
        self.agents: dict[uuid.UUID: pd.Series] = {}  # 所有的新的道路智能体
        self.agents_done: dict[uuid.UUID, bool] = {}  # 个体是否完成

        Road.cache()  # 保存当前路网状态，以备复原

    def reset(self):
        """初始化新的道路，分随机初始化、选定道路初始化(TODO)"""
        Road.restore()  # 复原路网
        self.episode_step = 0  # 重置步数
        self.clear_and_spawn_agents()  # 生成智能体
        return self.get_image_observation()

    def clear_and_spawn_agents(self):
        self.agents = {}
        self.agents_done = {}
        selected_road_uids = set()
        count = 0  # 这个变量是统计while 循环的次数的，防止始终找不到合适的路而陷入无限循环
        while len(self.agents) < self.num_agents:
            count += 1
            if count > 1000: break  # 如果很多轮依旧找不满合适的路，则停止
            random_road = self.raw_roads.sample().iloc[0]  # 在原始的路网中随机一条路
            if random_road['uid'] in selected_road_uids: continue  # 如果随机到的路已经被选中了，则重新选
            if random_road['uid'] not in Road.get_all_roads()['uid'].values: continue
            selected_road_uids.add(random_road['uid'])  # 将随机到的路加入已被选择的路的set
            spawn_point = Road.interpolate_road_by_random_position(random_road)
            if spawn_point is None: continue  # 如果找不到符合路网间距规范的点，则重新选一条路
            Road.split_road_by_coord(random_road, spawn_point)  # 在路上随机一个点并尝试分裂
            uid = Road.add_road_by_coords(spawn_point, RoadLevel.TERTIARY, RoadState.OPTIMIZING)  # 生成新路
            new_road = Road.get_road_by_uid(uid)

            self.agents[uid] = new_road  # 将新路加入self.agents
            self.agents_done[uid] = False  # 初始默认done的状态为False

    def get_image_observation(self):
        """返回状态，为 图像 格式"""
        image_data, ax = plot_as_array(
            gdf=[Road.get_all_roads(), Building.get_all_buildings(), Region.get_all_regions()],
            width=self.observation_space_shape[1],
            height=self.observation_space_shape[0],
            y_lim=(-100 * 1.2, 400 * 1.2),
            x_lim=(-100, 450 * 1.2),
            transparent=True, antialiased=False)
        # print(image_data.shape)
        return image_data.numpy()

    def render(self):
        GraphicManager.instance.bilt_to('RoadNet Observation', self.get_image_observation())

    def step(self, action):
        """返回new_observation, rewards, done, all_done"""
        self.episode_step += 1
        dx = np.reshape(np.cos(action[:, 0]) * action[:, 1], (-1, 1))
        dy = np.reshape(np.sin(action[:, 0]) * action[:, 1], (-1, 1))
        moves = np.concatenate((dx, dy), axis=1)
        # 给每条路添加新的 最末点， 以此使路网生长
        for i, uid in enumerate(self.agents.keys()):
            if self.agents_done[uid]: continue  # 如果该道路已经停止，则不再添加
            lst_pt = Road.get_road_last_point(self.agents[uid])  # 获取道路的最后一个点
            new_pt = lst_pt + moves[i].reshape(1, 2)  # 根据move计算新的点的位置
            self.agents[uid] = Road.add_point_to_road(self.agents[uid], point=new_pt)  # 向道路添加点

        for i, uid in enumerate(self.agents.keys()):
            self.agents_done[uid] = self._is_agent_done(uid)  # 计算每条路是否结束

        new_observation, reward, done, all_done = self.get_image_observation(), \
            self.reward(), self.agents_done, self._all_done()
        return new_observation, reward, done, all_done

    def _get_last_points(self):
        """获取所有agent道路的最后一个点，返回[n, 2]形状的np array"""
        last_points = []
        for i, road in enumerate(self.agents.values()):
            last_points.append(Road.get_road_last_point(road))
        return np.vstack(last_points)

    def reward(self):
        # 此处未修改
        buildings = Building.get_all_buildings()
        regions = Region.get_all_regions()
        world_x_range = (-100, 450 * 1.2)
        world_y_range = (-100 * 1.2, 400 * 1.2)
        image_x_range = (0, 512)
        image_y_range = (0, 512)
        list_buire = [buildings, regions]
        buire_img, ax = plot_as_array(list_buire, image_x_range[1], image_y_range[1],
                                      y_lim=world_y_range, x_lim=world_x_range,
                                      transparent=True, antialiased=False)
        last_points = self._get_last_points()
        scaled_points_x = np.interp(last_points[:, 0], world_x_range, image_x_range)
        scaled_points_y = np.interp(last_points[:, 1], world_y_range, image_y_range)
        points = np.column_stack((scaled_points_x, scaled_points_y))

        reward_agent = RewardAgent(points, buire_img.numpy()[:, :, :3])
        return reward_agent.agent_reward()

    def _is_in_region(self, uid) -> bool:
        """判断uid编号的道路的是否在区域内。该函数仅对最后一个点有效，因此需要每步调用"""
        lst_pt = tuple(Road.get_road_last_point(self.agents[uid])[0])
        in_region = True
        in_region &= self.region_min[0] < lst_pt[0] < self.region_max[0]
        in_region &= self.region_min[1] < lst_pt[1] < self.region_max[1]
        return in_region

    def _is_way_forward(self, uid) -> bool:
        """判断uid编号的道路是否向前运动。需要每步调用"""
        coords = list(self.agents[uid]['geometry'].coords)
        if len(coords) < 3:
            return True
        vec1 = point_utils.vector_from_points(coords[-2], coords[-1])
        vec2 = point_utils.vector_from_points(coords[-3], coords[-2])
        return point_utils.vector_dot(vec1, vec2) > 0

    def _is_intersect_with_raw_roads(self, uid):
        """判断uid编号的道路是否与原始路网相交。该函数仅对最后一段线段有效，因此需要每步调用"""
        road = self.agents[uid]
        coords = list(self.agents[uid]['geometry'].coords)
        if len(coords) < 3:
            return False  # 如果线段数小于2， 即点数小于3，则不做判断
        last_element = Road.get_road_last_element(road).buffer(1e-5)
        intersects = self.raw_roads['geometry'].intersects(last_element)
        return intersects.sum() > 0  # 由于判断的是最后一段线段，因此只要大于0就是相交，无需考虑起点和原始路径的相交问题

    def _is_agent_done(self, uid) -> bool:
        """判断uid的道路是否完成"""
        if self.agents_done[uid]: return True  # 如果在agents_done中已经标记为完成，则直接返回完成
        if self.episode_step > self.max_episode_step: return True  # 如果达到最大步数，则返回完成
        done = False
        done |= not self._is_in_region(uid)
        # done |= not self._is_way_forward(uid)
        done |= self._is_intersect_with_raw_roads(uid)
        return done

    def _all_done(self):
        """是否所有的agent都完成了"""
        return all(self.agents_done.values())


mRoadNet: Union[RoadNet, None] = None
mRewardSum = 0

mTargetOptimizedAgentNum = 0  # 仅限顺序模式
mCurrentOptimizedAgentNum = 0  # 仅限顺序模式


def synchronous_mode_init(num_agents):
    """同步模式，若干agent同时跑"""
    global mRoadNet
    _ = io_utils.load_data('../data/VirtualEnv/try2.bin')
    Building.data_to_buildings(_)
    Region.data_to_regions(_)
    Road.data_to_roads(_)

    mRoadNet = RoadNet(num_agents)


def synchronous_mode_reset():
    global mRoadNet, mRewardSum
    mRoadNet.reset()
    mRoadNet.render()
    mRewardSum = 0
    print('road net reset')


def synchronous_mode_step(_) -> bool:
    global mRoadNet, mRewardSum
    try:
        print(f'当前轮次 {mRoadNet.episode_step}======================')
        action_list = []
        b = mRoadNet.action_space_bound
        c = mRoadNet.action_space_boundMove
        for i in range(len(mRoadNet.agents)):
            a = np.random.uniform(low=-1, high=1, size=(2,))
            _action = a * b + c
            action_list.append(_action)
        action = np.vstack(action_list)
        print(f'action {action}')
        next_state, reward, done, all_done = mRoadNet.step(action)
        mRewardSum += reward

        print(f'当前奖励 {reward}')
        print(f'当前累计奖励 {mRewardSum}')
        print(f'单路是否结束 {list(done.values())}')
        print(f'总体路网是否结束 {all_done}')
        print('==================================')
        mRoadNet.render()
        return all_done

    except Exception as e:
        print(e)
        traceback.print_exc()
        return True


def sequential_mode_init(num_agents):
    """顺序模式， agent一个一个跑"""
    global mRoadNet, mTargetOptimizedAgentNum
    _ = io_utils.load_data('../data/VirtualEnv/try2.bin')
    Building.data_to_buildings(_)
    Region.data_to_regions(_)
    Road.data_to_roads(_)
    mRoadNet = RoadNet(1)
    mTargetOptimizedAgentNum = num_agents


def sequential_mode_reset():
    global mRoadNet, mRewardSum, mCurrentOptimizedAgentNum

    mRoadNet.reset()
    mRoadNet.render()
    mRewardSum = 0
    mCurrentOptimizedAgentNum = 0
    print('road net reset')


def sequential_mode_step(_) -> bool:
    global mRoadNet, mRewardSum, mCurrentOptimizedAgentNum
    if mCurrentOptimizedAgentNum >= mTargetOptimizedAgentNum:
        return True

    print(f'当前轮次 {mRoadNet.episode_step}======================')

    b = mRoadNet.action_space_bound
    c = mRoadNet.action_space_boundMove
    a = np.random.uniform(low=-1, high=1, size=(2,))
    action = a * b + c
    print(f'action {action}')
    next_state, reward, done, all_done = mRoadNet.step(action)
    mRewardSum += reward

    print(f'当前奖励 {reward}')
    print(f'当前累计奖励 {mRewardSum}')
    print(f'单路是否结束 {list(done.values())}')
    print(f'总体路网是否结束 {all_done}')
    print('==================================')
    mRoadNet.render()

    if all_done:  # 这里一个单智能体的完成就会all done ，但不代表整体完成
        mRoadNet.clear_and_spawn_agents()
        mCurrentOptimizedAgentNum += 1

    return False


if __name__ == '__main__':
    pass
