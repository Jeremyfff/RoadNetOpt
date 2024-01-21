import torch.nn as nn
import torch
from CNN import CNN
from DDPGNet import PolicyNet, CriticNet


class Agent:
    def __init__(self, nb_actions, action_space_bound, action_space_boundMove,
                 actor_lr, critic_lr, tau, gamma, device):
        """ 训练网络（真实）-- CNN 策略 价值（评价）"""
        self.cnn = CNN().to(device)
        self.critic = CriticNet(nb_actions, self.cnn).to(device)
        self.actor = PolicyNet(nb_actions, action_space_bound.to(device),
                               action_space_boundMove.to(device), self.cnn).to(device)

        """ 目标网络（预测）-- CNN 策略 价值（评价）"""
        self.target_cnn = CNN().to(device)
        self.target_critic = CriticNet(nb_actions, self.target_cnn).to(device)
        self.target_actor = PolicyNet(nb_actions, action_space_bound.to(device),
                                      action_space_boundMove.to(device), self.target_cnn).to(device)

        """ 使训练网络和目标网络的参数相同 """
        self.target_cnn.load_state_dict(self.cnn.state_dict())
        self.target_critic.load_state_dict(self.critic.state_dict())
        self.target_actor.load_state_dict(self.actor.state_dict())

        """ 生成优化器 """
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=critic_lr)

        """ 属性分配 """
        self.gamma = gamma  # 折扣因子
        # self.sigma = sigma  # 高斯声标准差，均值设为0
        self.tau = tau  # 目标网络软更新参数
        self.n_actions = nb_actions  # 动作空间维度
        self.device = device

    def take_action(self, state):
        state = torch.tensor(state, dtype=torch.float).unsqueeze(0).to(self.device)
        action = self.actor(state).cpu().detach().numpy()
        # action = action + self.sigma * np.random.randn(self.n_actions)
        return action

    def soft_update(self, net, target_net):
        for param_target, param in zip(target_net.parameters(), net.parameters()):
            param_target.data.copy_(param_target.data * (1 - self.tau) + param.data * self.tau)

    def update(self, i, transition_dict):  # 当多个智能体一起时，第i个智能体更新
        states = torch.tensor(transition_dict['states'], dtype=torch.float32).to(self.device)
        actions = torch.tensor(transition_dict['actions'][:, i], dtype=torch.float32).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'][:, i], dtype=torch.float32).to(self.device)
        next_states = torch.tensor(transition_dict['next_states'], dtype=torch.float32).to(self.device)
        dones = torch.tensor(transition_dict['dones'][:, i], dtype=torch.float32).to(self.device)
        Dones = torch.tensor(transition_dict['Dones'], dtype=torch.float32).view(-1, 1).to(self.device)

        next_actions = self.target_actor(next_states)
        next_q_values = self.target_critic(next_states, next_actions)
        """ 
        单条路结束了，就返回单条路结束的reward值，且此时没有之后的预测期望
        若整体结束了，也没有之后的预测期望
        """
        q_targets = rewards + self.gamma * next_q_values * (1 - dones) * (1 - Dones)  # 目标值
        q_values = self.critic(states, actions)  # 预测值
        critic_loss = torch.mean(nn.functional.mse_loss(q_values, q_targets))  # 预测值和目标值之间的均方差损失

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        actor_actions = self.actor(states)
        score = self.critic(states, actor_actions)
        actor_loss = -torch.mean(score)

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        self.soft_update(self.cnn, self.target_cnn)
        self.soft_update(self.actor, self.target_actor)
        self.soft_update(self.critic, self.target_critic)
