import numpy as np
def get_arg(kwargs: dict, name: str, default: any = None):
    if name in kwargs:
        return kwargs[name]
    else:
        return default

def gaussian(x, mu, sigma):
    return np.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * np.sqrt(2 * np.pi))