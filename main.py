#算法1
import random
import GAChose
import GAcross
import GAmutation
import ApproxLibManager as ALM

# --- 实验超参数 ---
POPULATION_SIZE = 10
MAX_GENERATIONS = 20
ELITE_SIZE = 5


def initialize_population(pop_size):
    pop_axmul = []
    pop_axadd = []
    for _ in range(pop_size):
        # 【修改点】基因变为一维数组：索引代表 Level，值代表选中了该 Level 的第几个变体 (Variant)
        mul_genes = [random.randint(0, len(level_group) - 1) for level_group in ALM.MUL8_POOL]
        add_genes = [random.randint(0, len(level_group) - 1) for level_group in ALM.ADD16_POOL]
        pop_axmul.append(mul_genes)
        pop_axadd.append(add_genes)
    return pop_axmul, pop_axadd


def run_aaa_framework():
    print(f"--- 开始运行 AAA 近似资源库构建框架 ---")
    print(f"约束条件: 覆盖所有误差等级，且 Level 0 为精确计算单元")

    pop_axmul, pop_axadd = initialize_population(POPULATION_SIZE)
    best_fitness_history = []

    for gen in range(MAX_GENERATIONS):
        elite_mul, elite_add, fitnesses = GAChose.evaluate_and_select(pop_axmul, pop_axadd, top_k=ELITE_SIZE)

        best_q = fitnesses[0]
        best_fitness_history.append(best_q)

        # ====== 打印直观的字符串 ======
        mul_str = ", ".join([f"L{level} 第{variant + 1}个" for level, variant in enumerate(elite_mul[0])])
        add_str = ", ".join([f"L{level} 第{variant + 1}个" for level, variant in enumerate(elite_add[0])])

        print(f"Generation {gen + 1}/{MAX_GENERATIONS} | Best Q(L): {best_q:.4f} MUL[{mul_str}] ADD[{add_str}]")

        pop_axmul, pop_axadd = GAcross.cross(elite_mul, elite_add, target_pop_size=POPULATION_SIZE)
        pop_axmul, pop_axadd = GAmutation.mut(pop_axmul, pop_axadd, mutation_rate=0.3)

    print("\n" + "=" * 70)
    print("--- 搜索完成: 最终构建的最优近似资源库 ---")
    print("=" * 70)

    print("【乘法器配置 (已覆盖所有等级)】:")
    for level, variant_idx in enumerate(elite_mul[0]):
        name = ALM.MUL8_POOL[level][variant_idx]['name']
        print(f"  * 等级 Level {level}: 选中第 {variant_idx + 1} 个单元 (名称: {name})")

    print("\n【加法器配置 (已覆盖所有等级)】:")
    for level, variant_idx in enumerate(elite_add[0]):
        name = ALM.ADD16_POOL[level][variant_idx]['name']
        print(f"  * 等级 Level {level}: 选中第 {variant_idx + 1} 个单元 (名称: {name})")
    print("=" * 70)


if __name__ == '__main__':
    run_aaa_framework()



