





#选择算子2
import GAmedcomputing


def evaluate_and_select(pop_axmul, pop_axadd, top_k=5):
    """
    评估种群，并保留 Top-K 精英个体
    """
    evaluated_population = []

    for i in range(len(pop_axmul)):
        mul_genes = pop_axmul[i]
        add_genes = pop_axadd[i]

        fitness_ecc = GAmedcomputing.evaluate_library_quality(mul_genes, add_genes)

        evaluated_population.append({
            'mul_genes': mul_genes,
            'add_genes': add_genes,
            'fitness': fitness_ecc  # 排序的 key ('fitness') 保持不变，这样 sort 函数就不用改
        })

    # 按照 Q(L) 降序排序 (质量越高越好)
    evaluated_population.sort(key=lambda x: x['fitness'], reverse=True)

    # 选取精英解作为下一代的基础
    elites = evaluated_population[:top_k]

    new_pop_mul = [ind['mul_genes'] for ind in elites]
    new_pop_add = [ind['add_genes'] for ind in elites]
    elite_fitness = [ind['fitness'] for ind in elites]

    return new_pop_mul, new_pop_add, elite_fitness
