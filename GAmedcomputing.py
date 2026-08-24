import itertools
import random
import ApproxLibManager as ALM
from DFGparsing import RegMatch  # 引入你的解析器

import math # 在文件开头引入



WEIGHT_AREA = 1
WEIGHT_POWER = 0
EPSILON = 1e-5


# ================= 1. 动态批量解析 CDFG =================
def load_and_parse_dfg(file_path):
    """独立的解析器，返回拓扑排序后的 DFG 以及所需的算子顺序"""
    dfg_parser = RegMatch()
    try:
        with open(file_path, "r") as f:
            dfg_parser.data = f.read()
        dfg_parser.format_data()
        parsed_dfg = dfg_parser.search_order()
        parsed_dfg.sort(key=lambda x: x['order'])

        # 提取当前 DFG 依赖的算子执行序列 (如: ['add', 'add', 'mul'])
        op_sequence = []
        for node in parsed_dfg:
            func_type = node['functions'].get('function', '').lower().strip()
            if 'add' in func_type:
                op_sequence.append('add')
            elif 'mul' in func_type:
                op_sequence.append('mul')

        return parsed_dfg, op_sequence
    except Exception as e:
        print(f"解析 {file_path} 失败: {e}")
        return None, []


# 将你生成的 11 个文件的文件名填入此处 (请确保它们存放在 applications/ 目录下)
CDFG_FILES = [
     "tree1.cdfg", "tree2.cdfg",
    "tree5.cdfg","tree.cdfg","tree3.cdfg", "tree4.cdfg"
]#"tree.cdfg","tree3.cdfg", "tree4.cdfg",
#, "tree5.cdfg","tree6.cdfg", "tree7.cdfg", "tree8.cdfg","tree9.cdfg", "tree10.cdfg","tree11.cdfg"
# 在模块加载时预先解析所有文件，避免 GA 迭代中重复产生 I/O 开销
ALL_DFGS = []
for f_name in CDFG_FILES:
    dfg_data, ops_req = load_and_parse_dfg(f"applications/{f_name}")
    if dfg_data:
        ALL_DFGS.append({'name': f_name, 'dfg': dfg_data, 'ops_req': ops_req})
print(f"GAmedcomputing: 成功预加载并解析了 {len(ALL_DFGS)} 个数据流图。")


# ================= 2. 泛化的误差仿真引擎 =================
def simulate_cdfg_error(dfg, op_instances, num_samples=100000):
    """
    dfg: 解析后的单一数据流图
    op_instances: 按拓扑执行顺序排列的近似算子字典列表 (例如 [add_op, add_op, mul_op])
    """
    total_error = 0.0
    c_funcs = [ALM.LIB_CACHE.get(op['name']) for op in op_instances]

    for _ in range(num_samples):
        wires_exact = {}
        wires_approx = {}
        final_write_wire = None
        op_idx = 0  # 统筹追踪算子分配

        for node in dfg:
            op_type = node['functions'].get('function', '').lower().strip()
            write = node['functions'].get('write', '').strip()
            final_write_wire = write

            # 处理 reads
            raw_reads = node['functions'].get('read', [])
            if isinstance(raw_reads, str):
                reads = [r.strip() for r in raw_reads.split(',')]
            else:
                reads = [r.strip() for r in raw_reads]

            val_exact = []
            val_approx = []
            for r in reads:
                if not r: continue
                if r not in wires_exact:
                    rand_val = random.randint(0, 127)  # 限制激励范围防溢出
                    wires_exact[r] = rand_val
                    wires_approx[r] = rand_val
                val_exact.append(wires_exact[r])
                val_approx.append(wires_approx[r])

            # 执行计算
            if 'add' in op_type:
                wires_exact[write] = sum(val_exact)
                c_func = c_funcs[op_idx] if op_idx < len(c_funcs) else None
                if c_func:
                    wires_approx[write] = c_func(val_approx[0], val_approx[1])
                else:
                    wires_approx[write] = sum(val_approx)
                op_idx += 1

            elif 'mul' in op_type:
                wires_exact[write] = val_exact[0] * val_exact[1]
                c_func = c_funcs[op_idx] if op_idx < len(c_funcs) else None
                if c_func:
                    wires_approx[write] = c_func(val_approx[0], val_approx[1])
                else:
                    wires_approx[write] = val_approx[0] * val_approx[1]
                op_idx += 1

        if final_write_wire and final_write_wire in wires_exact:
            total_error += abs(wires_exact[final_write_wire] - wires_approx[final_write_wire])

    return total_error / num_samples


# ================= 全局平均评估函数 =================
def evaluate_library_quality(ax_mul_genes, ax_add_genes):
    if not ALL_DFGS:
        return 0.0

    # 【完美映射】：enumerate 提供 level，gene 提供 variant
    selected_muls = [ALM.MUL8_POOL[level][variant] for level, variant in enumerate(ax_mul_genes)]
    selected_adds = [ALM.ADD16_POOL[level][variant] for level, variant in enumerate(ax_add_genes)]

    total_log_q = 0.0

    # 遍历所有的数据流图 例出所有可能
    for dfg_info in ALL_DFGS:
        dfg = dfg_info['dfg']
        op_reqs = dfg_info['ops_req']

        pool_list = []
        for req in op_reqs:
            if req == 'add':
                pool_list.append(selected_adds)
            elif req == 'mul':
                pool_list.append(selected_muls)

        if not pool_list:
            continue

        configurations = list(itertools.product(*pool_list))
        total_R_for_this_dfg = 0.0

        for config in configurations:
            # 此处应调用你真实的误差仿真代码
            e_cdfg = simulate_cdfg_error(dfg, config)#计算系统误差

            # 注意这里使用了 EXACT_AREA_ADD8
            #计算精确面积
            exact_area_total = sum(ALM.EXACT_AREA_ADD16 if req == 'add' else ALM.EXACT_AREA_MUL8 for req in op_reqs)
            #计算近似面积
            approx_area_total = sum(op['area'] for op in config)
            s_area = (exact_area_total - approx_area_total) / exact_area_total if exact_area_total > 0 else 0

            exact_power_total = sum(ALM.EXACT_POWER_ADD16 if req == 'add' else ALM.EXACT_POWER_MUL8 for req in op_reqs)
            approx_power_total = sum(op['power'] for op in config)
            s_power = (exact_power_total - approx_power_total) / exact_power_total if exact_power_total > 0 else 0

            # 防止数值爆炸的安全误差截断
            safe_error = max(e_cdfg, 0.001)
            R_w = ((WEIGHT_AREA * s_area + WEIGHT_POWER * s_power) / safe_error) * 100

            total_R_for_this_dfg += R_w

        Q_L_this_dfg = total_R_for_this_dfg / len(configurations)
        total_log_q += math.log(Q_L_this_dfg + 1e-9)

    final_global_Q_L = math.exp(total_log_q / len(ALL_DFGS))
    return final_global_Q_L





