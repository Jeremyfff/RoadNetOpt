import cv2
import numpy as np #目前仍然以numpy对接，后期改成tensor
from utils import image_utils as iu

class RewardAgent():
    def __init__(self,last_points,buildings_img):
        self.agent_position = last_points
        self.env_buildings = buildings_img 
        '''后续补充其他评价来源
        self.graph = graph
        self.road = roads
        self.env_terrain = terrain
        self.agent_direction = direction
        '''
        self.building_weight = 1
        self.graph_weight = 1
        self.road_weight = 1
        self.terrain_weight = 1
        self.direction_weight = 1
        #后续补充调整其他评价的权重关系

    def building_rewards(self):
        '''限制不能进入的区域,传入当前建筑图像与智能体位置
        返回规则: 得分区间[-1,0.2],越靠近建筑越接近于-1'''

        imgGray = self.env_buildings
        # imgGray = cv2.blur_image(imgGray[:, :, :3])
        imgGray = cv2.GaussianBlur(imgGray, (5,5), 0)
        imgGray = cv2.cvtColor(imgGray, cv2.COLOR_BGR2GRAY)
        inds = self.agent_position.astype(int)
        pixel_values = imgGray[inds[:, 1], inds[:, 0]]
        min1 = 126 # np.min(imgGray)
        max1 = np.max(imgGray)
        reward = -1 + 1.2*(1 / np.log(max1-min1+1) * np.log(np.abs(pixel_values- min1+1))) # 非线性变化
        # reward = (pixel_values-min1)/(max1-min1)-1 #线性变化
        return reward.reshape((-1, 1))


    def graph_rewards(self):
        return 0
    
    def road_rewards(self):
        return 0
    
    def terrain_rewards(self):
        return 0
    
    def direction_rewards(self):
        return 0
    
    def agent_reward(self):
        reward = self.building_rewards()*self.building_weight + self.graph_rewards()*self.graph_weight + self.road_rewards()*self.road_weight + self.terrain_rewards() * self.terrain_weight + self.direction_rewards() * self.direction_weight
        return reward