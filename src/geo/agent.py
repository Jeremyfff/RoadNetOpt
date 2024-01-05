import torch


class Agent:
    def __init__(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def calculate_reward(self):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError
