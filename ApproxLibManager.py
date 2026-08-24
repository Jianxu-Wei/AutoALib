#enap
'''#算法3
import os
from ctypes import *

# ================= 1. 精确算子基准 =================
EXACT_AREA_ADD8 = 70.4
EXACT_POWER_ADD8 = 0.034
EXACT_AREA_ADD16 = 141.7
EXACT_POWER_ADD16 = 0.072
EXACT_AREA_MUL8 = 709.6
EXACT_POWER_MUL8 = 0.391

# ================= 2. 候选池与误差分级 (二维结构) =================
ADD8_POOL = [
# Level 0
   [{'name': 'exact_add8', 'area': EXACT_AREA_ADD8, 'power': EXACT_POWER_ADD8},
       #{'name': 'add8u_5R3', 'area': 63.8, 'power': 0.029},
   # {'name': 'add8s_6FR', 'area': 67.1, 'power': 0.032}
    ],

# Level 1
   [{'name': 'add8u_5QL', 'area': 57.3, 'power': 0.024},
    {'name': 'add8u_70Z', 'area': 57.7, 'power': 0.020}],
   [{'name': 'add8u_5SY', 'area': 28.2, 'power': 0.012},
    {'name': 'add8u_5SY', 'area': 28.2, 'power': 0.012}],  # Level 2
   [{'name': 'add8u_006', 'area': 15.0, 'power': 0.0046},
    {'name': 'add8u_006', 'area': 15.0, 'power': 0.0046}], # Level 3
   [{'name': 'add8u_8ES', 'area': 8.0 , 'power': 0.0015},
    {'name': 'add8u_8ES', 'area': 8.0 , 'power': 0.0015}]  # Level 4
]

ADD16_POOL = [
    # Level 0
    [{'name': 'exact_add16', 'area': EXACT_AREA_ADD16, 'power': EXACT_POWER_ADD16}
       # {'name': 'add16u_0RN', 'area': 115.9, 'power': 0.060},
        #{'name': 'add16u_1AB', 'area': 116.8, 'power': 0.057},
        #{'name': 'add16u_2CD', 'area': 114.2, 'power': 0.062}
    ],
    # Level 1
    [

       # {'name': 'add16se_2JY', 'area': 120.1, 'power': 0.062},
       # {'name': 'add16u_0NK', 'area': 115.0, 'power': 0.057},
        {'name': 'add16u_0RN', 'area': 115.9, 'power': 0.060}
    ],
# Level 2
    [

       # {'name': 'add16se_2GE', 'area': 106.1, 'power': 0.052},
       # {'name': 'add16u_08F', 'area': 106.1, 'power': 0.052},
        {'name': 'add16u_0EM', 'area': 115.0, 'power': 0.057}
    ],
# Level 3
    [

       # {'name': 'add16u_0FJ', 'area': 98.1, 'power': 0.050},
        {'name': 'add16u_0Q7', 'area': 100.4, 'power': 0.051},
        #{'name': 'add16u_1JH', 'area': 100.4, 'power': 0.051}
    ],
    # Level 4
    #[

        #{'name': 'add16u_05T', 'area': 82.6, 'power': 0.041},
        #{'name': 'add16u_0QC', 'area': 90.6, 'power': 0.043},
        #{'name': 'add16u_073', 'area': 90.6, 'power': 0.043}
    #],
# Level 5
    #[

       # {'name': 'add16u_09P', 'area': 73.7, 'power': 0.036},
        #{'name': 'add16u_0DL', 'area': 55.8, 'power': 0.026},
        #{'name': 'add16u_0M0', 'area': 71.3, 'power': 0.036}
    #],
]

MUL8_POOL = [[
    # Level 0
    {'name': 'exact_mul8', 'area': EXACT_AREA_MUL8, 'power': EXACT_POWER_MUL8}
        #{'name': 'mul8u_Y48', 'area': 682.8, 'power': 0.390},
       # {'name': 'mul8u_Z59', 'area': 688.2, 'power': 0.381},
       # {'name': 'mul8u_W37', 'area': 677.1, 'power': 0.395}
    ],

 # Level 1
[
#{'name': 'mul8u_1446', 'area': 683.3, 'power': 0.388},
#{'name': 'mul8u_2P7', 'area': 676.3, 'power': 0.386},
{'name': 'mul8u_Y48', 'area': 682.8, 'power': 0.390}
],
    # Level 2
[
{'name': 'mul8u_LM7', 'area': 663.6, 'power': 0.380},
#{'name': 'mul8u_125K', 'area': 674.9, 'power': 0.384},
#{'name': 'mul8u_2P7', 'area': 676.3, 'power': 0.386}
 ],
    # Level 3
[
#{'name': 'mul8u_GS2', 'area': 632.6, 'power': 0.356},
#{'name': 'mul8u_14VP', 'area': 654.2, 'power': 0.364},
{'name': 'mul8u_KEM', 'area': 637.8, 'power': 0.370}
 ],
    # Level 4
#[
#{'name': 'mul8u_QJD', 'area': 624.2 , 'power': 0.344},
#{'name': 'mul8u_GS2', 'area': 632.6, 'power': 0.356},
#{'name': 'mul8u_150Q', 'area': 660.3, 'power': 0.360}
 #],
    # Level 5
#[
#{'name': 'mul8u_2AC', 'area': 508.3, 'power': 0.311},
#{'name': 'mul8u_ZFB', 'area': 590.4, 'power': 0.301},
#{'name': 'mul8u_7C1', 'area': 606.8, 'power': 0.329},
#{'name': 'mul8u_CK5', 'area': 604.5, 'power': 0.345}
 #]
]
# ================= 3. 自动化加载引擎 =================
LIB_CACHE = {}
LIB_PATH = "./approlib/"


def init_libs():
    target_libs = []
    for level in ADD16_POOL:
        target_libs.extend([op['name'] for op in level])
    for level in MUL8_POOL:
        target_libs.extend([op['name'] for op in level])

    count = 0
    for lib_name in target_libs:
        # 如果是精确算子，可跳过加载或使用专门的精确逻辑
        if "exact_" in lib_name:
            continue

        so_path = f"{LIB_PATH}{lib_name}.so"
        if os.path.exists(so_path):
            try:
                dll = cdll.LoadLibrary(so_path)
                func = getattr(dll, lib_name)
                func.argtypes = [c_uint64, c_uint64]
                func.restype = c_uint64
                LIB_CACHE[lib_name] = func
                count += 1
            except Exception:
                pass
    print(f"ApproxLibManager: 成功加载 {count} 个近似算子。")



init_libs()'''

#fpax
import os
from ctypes import *

# ================= 1. 精确算子基准 =================
EXACT_AREA_ADD8 = 70.4
EXACT_POWER_ADD8 = 0.034
EXACT_AREA_ADD16 = 141.7
EXACT_POWER_ADD16 = 0.072
EXACT_AREA_MUL8 = 709.6
EXACT_POWER_MUL8 = 0.391

# ================= 2. 候选池与误差分级 (二维结构) =================
ADD8_POOL = [
# Level 0
   [{'name': 'exact_add8', 'area': EXACT_AREA_ADD8, 'power': EXACT_POWER_ADD8},
       #{'name': 'add8u_5R3', 'area': 63.8, 'power': 0.029},
   # {'name': 'add8s_6FR', 'area': 67.1, 'power': 0.032}
    ],

# Level 1
   [{'name': 'add8u_5QL', 'area': 57.3, 'power': 0.024},
    {'name': 'add8u_70Z', 'area': 57.7, 'power': 0.020}],
   [{'name': 'add8u_5SY', 'area': 28.2, 'power': 0.012},
    {'name': 'add8u_5SY', 'area': 28.2, 'power': 0.012}],  # Level 2
   [{'name': 'add8u_006', 'area': 15.0, 'power': 0.0046},
    {'name': 'add8u_006', 'area': 15.0, 'power': 0.0046}], # Level 3
   [{'name': 'add8u_8ES', 'area': 8.0 , 'power': 0.0015},
    {'name': 'add8u_8ES', 'area': 8.0 , 'power': 0.0015}]  # Level 4
]

ADD16_POOL = [
    # Level 0
    [{'name': 'exact_add16', 'area': EXACT_AREA_ADD16, 'power': EXACT_POWER_ADD16}
       # {'name': 'add16u_0RN', 'area': 115.9, 'power': 0.060},
        #{'name': 'add16u_1AB', 'area': 116.8, 'power': 0.057},
        #{'name': 'add16u_2CD', 'area': 114.2, 'power': 0.062}
    ],
    # Level 1
    [
{'name': 'add16u_0EM', 'area': 115.0, 'power': 0.057},
        {'name': 'add16se_2JY', 'area': 120.1, 'power': 0.062},
        {'name': 'add16u_0NK', 'area': 115.0, 'power': 0.057},
        {'name': 'add16u_0RN', 'area': 115.9, 'power': 0.060}
    ],

# Level 2
    [
{'name': 'add16u_08F', 'area': 106.1, 'power': 0.052},
        {'name': 'add16u_0FJ', 'area': 98.1, 'power': 0.050},
        {'name': 'add16u_0Q7', 'area': 100.4, 'power': 0.051},
        {'name': 'add16u_1JH', 'area': 100.4, 'power': 0.051}
    ],
    # Level 3
    [
{'name': 'add16u_0FJ', 'area': 98.1, 'power': 0.050},
{'name': 'add16u_1JH', 'area': 100.4, 'power': 0.051},
        {'name': 'add16u_05T', 'area': 82.6, 'power': 0.041},
        {'name': 'add16u_0QC', 'area': 90.6, 'power': 0.043},
     #   {'name': 'add16u_073', 'area': 90.6, 'power': 0.043}
    ],

]

MUL8_POOL = [[
    # Level 0
    {'name': 'exact_mul8', 'area': EXACT_AREA_MUL8, 'power': EXACT_POWER_MUL8}
        #{'name': 'mul8u_Y48', 'area': 682.8, 'power': 0.390},
       # {'name': 'mul8u_Z59', 'area': 688.2, 'power': 0.381},
       # {'name': 'mul8u_W37', 'area': 677.1, 'power': 0.395}
    ],

 # Level 1

    # Level 2
[

{'name': 'mul8u_LM7', 'area': 663.6, 'power': 0.380},
{'name': 'mul8u_125K', 'area': 674.9, 'power': 0.384},
{'name': 'mul8u_EXZ', 'area': 663.6, 'power': 0.380}
 ],
    # Level 3
[
{'name': 'mul8u_150Q', 'area': 660.3, 'power': 0.360},
{'name': 'mul8u_GS2', 'area': 632.6, 'power': 0.356},

{'name': 'mul8u_KEM', 'area': 637.8, 'power': 0.370}
 ],

    # Level 5
[
{'name': 'mul8u_2AC', 'area': 508.3, 'power': 0.311},

{'name': 'mul8u_7C1', 'area': 606.8, 'power': 0.329},
{'name': 'mul8u_CK5', 'area': 604.5, 'power': 0.345}
 ]
]
# ================= 3. 自动化加载引擎 =================
LIB_CACHE = {}
LIB_PATH = "./approlib/"


def init_libs():
    target_libs = []
    for level in ADD16_POOL:
        target_libs.extend([op['name'] for op in level])
    for level in MUL8_POOL:
        target_libs.extend([op['name'] for op in level])

    count = 0
    for lib_name in target_libs:
        # 如果是精确算子，可跳过加载或使用专门的精确逻辑
        if "exact_" in lib_name:
            continue

        so_path = f"{LIB_PATH}{lib_name}.so"
        if os.path.exists(so_path):
            try:
                dll = cdll.LoadLibrary(so_path)
                func = getattr(dll, lib_name)
                func.argtypes = [c_uint64, c_uint64]
                func.restype = c_uint64
                LIB_CACHE[lib_name] = func
                count += 1
            except Exception:
                pass
    print(f"ApproxLibManager: 成功加载 {count} 个近似算子。")


init_libs()