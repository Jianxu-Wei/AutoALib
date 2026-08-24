#交叉算子
import random
import copy


def cross(pop_axmul, pop_axadd, target_pop_size):
    """
    分离式单点交叉，直到种群恢复到目标规模
    """
    new_axmul = copy.deepcopy(pop_axmul)
    new_axadd = copy.deepcopy(pop_axadd)
    elite_size = len(pop_axmul)

    if elite_size < 2:
        return new_axmul, new_axadd

    while len(new_axmul) < target_pop_size:
        p1 = random.randint(0, elite_size - 1)
        p2 = random.randint(0, elite_size - 1)
        if p1 == p2:
            continue

        child1_mul, child2_mul = pop_axmul[p1], pop_axmul[p2]
        child1_add, child2_add = pop_axadd[p1], pop_axadd[p2]

        mul_len = len(pop_axmul[p1])
        if mul_len > 1:
            cx_m = random.randint(1, mul_len - 1)
            child1_mul = pop_axmul[p1][:cx_m] + pop_axmul[p2][cx_m:]

        add_len = len(pop_axadd[p1])
        if add_len > 1:
            cx_a = random.randint(1, add_len - 1)
            child1_add = pop_axadd[p1][:cx_a] + pop_axadd[p2][cx_a:]

        new_axmul.append(child1_mul)
        new_axadd.append(child1_add)

    return new_axmul, new_axadd


