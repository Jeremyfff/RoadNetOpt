import numpy as np
import time


def get_arg(kwargs: dict, name: str, default: any = None):
    if name in kwargs:
        return kwargs[name]
    else:
        return default


def gaussian(x, mu, sigma):
    return np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * np.sqrt(2 * np.pi))


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"函数 {func.__name__} 执行时间为: {execution_time} 秒")
        return result

    return wrapper
