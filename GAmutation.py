import random
import copy
import ApproxLibManager as ALM


def mut(pop_axmul, pop_axadd, mutation_rate=0.3):
    """
    定长多级基因的突变策略：在指定 Level 内探索更优的变体
    """
    new_axmul = copy.deepcopy(pop_axmul)
    new_axadd = copy.deepcopy(pop_axadd)

    for i in range(len(new_axmul)):
        if random.random() < mutation_rate:
            # 突变乘法器
            if len(new_axmul[i]) > 0:
                # 随机挑选一个 Level 进行变异
                level_to_mut = random.randint(0, len(new_axmul[i]) - 1)
                # 获取该 Level 的最大变体索引
                max_var_m = len(ALM.MUL8_POOL[level_to_mut]) - 1

                # 只有当变体数量 > 1 时才变异 (完美避开 Level 0)
                if max_var_m > 0:
                    new_axmul[i][level_to_mut] = random.randint(0, max_var_m)

            # 突变加法器
            if len(new_axadd[i]) > 0:
                level_to_mut_a = random.randint(0, len(new_axadd[i]) - 1)
                max_var_a = len(ALM.ADD16_POOL[level_to_mut_a]) - 1

                if max_var_a > 0:
                    new_axadd[i][level_to_mut_a] = random.randint(0, max_var_a)

    return new_axmul, new_axadd








