import random

from matplotlib import pyplot as plt
import gym
from gym import spaces
import numpy as np
import torch


class RoadAgent:
    def __init__(self, target):
        self.target = target

        self.action_space = spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
        # 定义观察空间为智能体在二维平面内的位置坐标
        self.observation_space = spaces.Box(low=0, high=100, shape=(2,), dtype=np.float32)  # 以 (0, 100) 为例
        self.state = torch.rand(2)

    def reset(self):
        self.state = torch.rand(2)

    def calculate_reward(self):
        distance = torch.norm(self.state - self.target)  # 计算智能体与目标点之间的欧氏距离
        reward = -distance  # 负的距离作为奖励，鼓励智能体朝着目标点移动
        return reward

    def step(self, action):
        # action = action.squeeze()
        self.state += action
        reward = self.calculate_reward()
        done = False
        return self.state, reward, done


class RnEnv(gym.Env):
    def __init__(self, N, targets):
        super(RnEnv, self).__init__()
        assert N == len(targets), "智能体数量与目标数量不匹配"
        self.N = N
        self.agents = [RoadAgent(targets[i]) for i in range(N)]
        self.step_n = 0

    def reset(self):
        # 重置环境状态并返回初始观察
        for agent in self.agents:
            agent.reset()
        self.step_n = 0
        return self.state()

    def state(self):
        state = torch.stack([agent.state for agent in self.agents])
        return state

    def step(self, action):
        assert len(action) == len(self.agents)
        reward_sum = 0
        for i in range(len(action)):
            state, reward, done = self.agents[i].step(action[i])
            reward_sum += reward
        done = self.step_n > 50
        info = {}  # 额外信息为空字典
        self.step_n += 1
        state = self.state()
        return state, reward_sum, done, info

    def render(self, mode='human'):
        if mode == 'human':
            print(f"state = {self.state()}")
            return self.state()
        elif mode == 'rgb_array':
            # 返回一个RGB数组，用于在其他地方渲染环境
            return self.state()  # 假设self.state是环境的状态
        else:
            super().render()  # 调用父类的render方法


class A2C:

    def __init__(self, model_actor, model_critic, model_critic_delay,
                 optimizer_actor, optimizer_critic):
        self.model_actor = model_actor
        self.model_critic = model_critic
        self.model_critic_delay = model_critic_delay
        self.optimizer_actor = optimizer_actor
        self.optimizer_critic = optimizer_critic

        self.model_critic_delay.load_state_dict(self.model_critic.state_dict())
        self.requires_grad(self.model_critic_delay, False)

    def soft_update(self, _from, _to):
        for _from, _to in zip(_from.parameters(), _to.parameters()):
            value = _to.data * 0.99 + _from.data * 0.01
            _to.data.copy_(value)

    def requires_grad(self, model, value):
        for param in model.parameters():
            param.requires_grad_(value)

    def train_critic(self, state, reward, next_state, over):
        debug = False
        state = state.detach()
        reward = reward.detach()
        next_state = next_state.detach()
        over = over.detach()
        if debug:
            print(f"====start training critic====")
            print(f"input state shape = {state.shape} {state.grad_fn}")
            print(f"input reward shape = {reward.shape} {reward.grad_fn}")
            print(f"input next_state shape = {next_state.shape} {next_state.grad_fn}")
            print(f"input over shape = {over.shape} {over.grad_fn}")

        self.requires_grad(self.model_critic, True)
        self.requires_grad(self.model_actor, False)

        # 计算values和targets
        value = self.model_critic(state)

        with torch.no_grad():
            target = self.model_critic_delay(next_state)
        target = target * 0.99 * (1 - over) + reward.reshape(-1, 1)

        # 时序差分误差,也就是tdloss
        loss = torch.nn.functional.mse_loss(value, target)
        if debug:
            print(f"value shape = {value.shape} {value.grad_fn}")
            print(f"target shape = {target.shape} {target.grad_fn}")
            print(f"loss = {loss} {loss.grad_fn}")

        loss.backward()
        self.optimizer_critic.step()
        self.optimizer_critic.zero_grad()
        self.soft_update(self.model_critic, self.model_critic_delay)
        output = (target - value).detach()
        if debug:
            print(f"output shape = {output.shape} {output.grad_fn}")
            print(f"====end training critic====")
        # 减去value相当于去基线
        return output

    def train_actor(self, state, action, value):
        debug = False
        state = state.detach()
        action = action.detach()

        if debug:
            print("====start train action====")
            print(f"input state shape {state.shape} {state.grad_fn}")
            print(f"input action shape {action.shape} {action.grad_fn}")
            print(f"input value shape {value.shape} {value.grad_fn}")
        self.requires_grad(self.model_critic, False)
        self.requires_grad(self.model_actor, True)

        # 获取策略网络输出的动作
        predicted_action = self.model_actor(state)

        # 计算策略梯度损失
        # 函数中的Q(state,action),这里使用critic模型估算
        loss = torch.nn.functional.mse_loss(predicted_action, action)
        if debug:
            print(f"predicted action {predicted_action.shape}  {predicted_action.grad_fn}")
            print(f"loss = {loss} {loss.grad_fn}")
        # 反向传播和优化
        loss.backward()
        self.optimizer_actor.step()
        self.optimizer_actor.zero_grad()
        if debug:
            print("====end training action====")
        return loss.item()


# 玩一局游戏并记录数据
def play(env, a2c, show=False):
    debug = False
    state = []
    action = []
    reward = []
    next_state = []
    done = []

    s = env.reset()
    d = False
    while not d:
        a = []
        for i in range(env.N):
            # 计算动作
            input = torch.FloatTensor(s).reshape(1, -1)
            a.append(a2c.model_actor(input).squeeze())

        a = torch.stack(a)
        # 执行动作
        ns, r, d, i = env.step(a)

        state.append(s)
        action.append(a)
        reward.append(r)
        next_state.append(ns)
        done.append(d)

        s = ns

        if show:
            env.render()

    state = torch.stack(state)
    action = torch.stack(action)
    reward = torch.FloatTensor(reward).unsqueeze(-1)
    next_state = torch.stack(next_state)
    done = torch.LongTensor(done).reshape(-1, 1)
    if debug:
        print(f"state.shape = {state.shape}")
        print(f"action.shape = {action.shape}")
        print(f"reward.shape = {reward.shape}")
        print(f"next_state.shape = {next_state.shape}")
        print(f"done.shape = {done.shape}")
    return state, action, reward, next_state, done, reward.sum().item()


def train(env, a2c):
    debug = False
    # 训练N局
    for epoch in range(5000):
        if debug:
            print(f"==============epoch = {epoch}====================")
        state, action, reward, next_state, over, sum_reward = play(env, a2c)

        # 合并部分字段
        state_c = state.flatten(start_dim=1)
        reward_c = reward.sum(dim=1).reshape(-1, 1)
        next_state_c = next_state.flatten(start_dim=1)

        for i in range(env.N):
            if debug:
                print(f"----------training agent {i}-------------")
            value = a2c.train_critic(state_c, reward_c, next_state_c, over)
            loss = a2c.train_actor(state_c, action[:, i], value)

        if epoch % 100 == 0:
            test_result = sum([play(env, a2c)[-1] for _ in range(10)]) / 10
            print(epoch, loss, test_result)


def init_a2c(env):
    model_actor = torch.nn.Sequential(
        torch.nn.Linear(2 * env.N, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 2),
    )

    model_critic, model_critic_delay = [
        torch.nn.Sequential(
            torch.nn.Linear(2 * env.N, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
        ) for _ in range(2)
    ]

    optimizer_actor = torch.optim.Adam(model_actor.parameters(), lr=1e-3)
    optimizer_critic = torch.optim.Adam(model_critic.parameters(), lr=5e-3)

    a2c = A2C(model_actor, model_critic, model_critic_delay, optimizer_actor,
              optimizer_critic)
    return a2c


def main():
    targets = torch.rand((3, 2))
    env = RnEnv(3, targets)
    a2c = init_a2c(env)
    train(env, a2c)


if __name__ == "__main__":
    main()
