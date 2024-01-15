import time

import torch
import torch.utils.benchmark as benchmark
import numpy as np
from PIL import Image
def print_gpu_info():
    if torch.cuda.is_available():
        # 获取可用的GPU数量
        num_gpus = torch.cuda.device_count()
        print(f"Number of available GPUs: {num_gpus}")

        # 遍历每个GPU并打印信息
        for i in range(num_gpus):
            gpu = torch.cuda.get_device_properties(i)
            print(f"GPU {i+1}: {gpu.name}, Compute Capability: {gpu.major}.{gpu.minor}, Total Memory: {gpu.total_memory / (1024**2)} MB")
    else:
        print("No GPUs available")

print_gpu_info()

def test_performance():
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # device = 'cpu'
    device = 'cuda'
    print('Using device:', device)
    # 创建一个简单的神经网络模型
    model = torch.nn.Sequential(
        torch.nn.Linear(1000, 1000),
        torch.nn.ReLU(),
        torch.nn.Linear(1000, 1000),
        torch.nn.ReLU(),
        torch.nn.Linear(1000, 1000),
        torch.nn.ReLU(),
        torch.nn.Linear(1000, 1000),
        torch.nn.ReLU(),
        torch.nn.Linear(1000, 100),
        torch.nn.ReLU(),
        torch.nn.Linear(100, 10),
        torch.nn.LogSoftmax(dim=1)
    ).to(device)

    # 生成随机输入数据
    input_data = torch.randn(64, 1000).to(device)
    target = torch.randint(0, 10, (64,)).to(device)

    # 训练模型
    criterion = torch.nn.NLLLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    start_time = time.time()
    for epoch in range(1000):
        optimizer.zero_grad()
        output = model(input_data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
    end_time = time.time()
    print('Training time:', end_time - start_time, 'seconds')

    # 模型推断
    start_time = time.time()
    with torch.no_grad():
        for _ in range(1000):
            output = model(input_data)
    end_time = time.time()
    print('Inference time:', end_time - start_time, 'seconds')
# test_performance()

# # 假设 arr 是一个 NumPy 数组
# arr = np.random.rand(256, 256, 3) * 255  # 生成一个随机的数组，表示图像
#
# # 将 NumPy 数组转换为 PIL 的 Image 对象
# img = Image.fromarray(arr.astype('uint8'))
#
# # 展示图像
# img.show()