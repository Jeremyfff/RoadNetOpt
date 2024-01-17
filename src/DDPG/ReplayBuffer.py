import collections
import numpy as np
import random

class ReplayBuffer:
    def __init__(self, capacity):  # 经验池的最大容量
        # 创建一个队列，先进先出
        self.buffer = collections.deque(maxlen=capacity)

    # 在队列中添加数据
    def add(self, state, action, reward, next_state, done, Done):
        # 以list类型保存
        self.buffer.append((state.transpose((2, 0, 1)), action, reward, next_state.transpose((2, 0, 1)), done, Done))

    # 在队列中随机取样batch_size组数据
    def sample(self, batch_size):
        transitions = random.sample(self.buffer, batch_size)
        # 将数据集拆分开来
        state, action, reward, next_state, done, Done = zip(*transitions)
        return np.array(action), np.array(state), np.array(reward), np.array(next_state),\
               np.array(done), Done
    
    # 测量当前时刻的队列长度
    def size(self):
        return len(self.buffer)
