import torch.nn as nn
import torch
import torch.optim as optim
import numpy as np
from torchsummary import summary
from env import RoadNet
from CNN import CNN


class PolicyNet(nn.Module):
    def __init__(self, nb_actions, action_space_bound, action_space_boundMove, CNN):
        super(PolicyNet, self).__init__()
        self.CNN = CNN
        self.action_space_bound = action_space_bound
        self.action_space_boundMove = action_space_boundMove

        self.model = nn.Sequential(
            nn.Linear(14*14*64, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, nb_actions)
        )

    def forward(self, status):
        status = self.CNN(status)
        status = status.view(status.size(0), -1)
        status = self.model(status)
        status = torch.tanh(status)
        action = status * self.action_space_bound + self.action_space_boundMove
        return action


class CriticNet(nn.Module):
    def __init__(self, nb_actions, CNN):
        super(CriticNet, self).__init__()
        self.CNN = CNN
        self.model = nn.Sequential(
            nn.Linear(14*14*64 + nb_actions, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 1)
        )

    def forward(self, status, action):
        status = self.CNN(status)
        status = status.view(status.size(0), -1)
        status = torch.cat([status, action], dim=1)
        critic = self.model(status)
        return critic


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
CNN = CNN().to(device)
A = torch.tensor(RoadNet.action_space_bound).to(device)
B = torch.tensor(RoadNet.action_space_boundMove).to(device)
policy = PolicyNet(2, A, B, CNN).to(device)
critic = CriticNet(2, CNN).to(device)
print(policy)
print(critic)
summary(policy, input_size=(4, 512, 512))