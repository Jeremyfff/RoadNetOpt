import torch.nn as nn
import torch
import torch.optim as optim
import numpy as np
from torchsummary import summary
from env import RoadNet


class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.CNN = nn.Sequential(
            nn.Conv2d(4, 64, 4, 2),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 64, 4, 2),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 64, 3, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2)
        )

    def forward(self, x):
        return self.CNN(x)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
A = CNN().to(device)
print(A)
summary(A, input_size=(4, 512, 512))