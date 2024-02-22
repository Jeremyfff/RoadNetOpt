import numpy as np
import torch
from utils import io_utils
from env import RoadNet
from ReplayBuffer import ReplayBuffer
from agent import Agent
from tqdm import tqdm

data = io_utils.load_data(r"try2.bin")
env = RoadNet(data)

nb_actions = 2
action_space_bound = torch.tensor(env.action_space_bound)
action_space_boundMove = torch.tensor(env.action_space_boundMove)
sigma = 1
actor_lr = 1e-4
critic_lr = 1e-3
tau = 0.001
gamma = 0.9
batch_size = 5
path = ''
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
agent = Agent(nb_actions, action_space_bound, action_space_boundMove, actor_lr, critic_lr, tau, gamma, device)

state = env.reset()
done = np.zeros((env.nb_new_roads, 1))
episode_return = 0

if path != '':
    agent.actor.load_state_dict(torch.load(path))

while True:
    action_list = []
    for i in range(0, env.nb_new_roads):
        action = agent.take_action(state)
        noise = sigma * np.random.randn(nb_actions)  # 后面可能换成ou噪声，增加噪声强度逐渐衰减的功能
        action = action + noise
        if done[i]:
            action = np.zeros((1, 2))
        action_list.append(action)
    action = np.array(action_list).reshape(-1, 2)
    next_state, reward, done, Done = env.step(action)
    state = next_state
    episode_return += reward
    print(f'当前奖励{reward}, 总奖励{episode_return}')
    env.render()

    if Done:
        # sigma *= 0.98
        break
