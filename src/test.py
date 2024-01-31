import numpy as np
import ctypes
from src.lib.accelerator import *
arr1 = np.random.random((10, 2)).astype(np.float32)[:, 0]
print(f'arr 1 {arr1}')

arr2 = np.arange(2, 22, 2, dtype=np.float32).reshape(-1, 1)
print(f'arr 2 {arr2}')

arr3 = np.arange(0, 20, 2, dtype=np.int32)
print(f'arr 3 {arr3}')


arr4 = np.arange(20, 40, 2, dtype=np.int32).reshape(-1, 2)
print(f'arr 4 {arr4}')

params = arrs_addr_len(arr1, arr2, arr3, arr4)
for i in range(int(len(params) / 2)):
    print(params[2 * i])
print("===================================")
print(arr3.ctypes.data)
print()
print("===================================")
cCommon.Test(*params)
