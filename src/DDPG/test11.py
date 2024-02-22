import matplotlib.pyplot as plt
import numpy as np

# 定义对数函数
def logarithmic_function(x, min, max):
    return -1 + (1 / np.log(max - min + 1) * np.log(np.abs(x - min + 1)))

# 生成示例数据
min_value = 0
max_value = 255
x_values = np.linspace(min_value, max_value, 1000)
y_values = logarithmic_function(x_values, min_value, max_value)

# 绘制图像
plt.plot(x_values, y_values, label='Logarithmic Function')
plt.title('Logarithmic Function')
plt.xlabel('Input Values')
plt.ylabel('Output Values')
plt.legend()
plt.grid(True)
plt.show()