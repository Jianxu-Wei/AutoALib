# 算法1
import copy
import json
import random
import statistics
from datetime import datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import GAChose
import GAcross
import GAmutation
import ApproxLibManager as ALM

# --- 实验超参数 ---
NUM_EXPERIMENTS = 10         # 独立完整实验次数，每次重新初始化
INITIAL_POPULATION_SIZE = 10  # 只用于初始化
ELITE_SIZE = 5               # 每轮保存并用于交叉的父代数量
OFFSPRING_SIZE = 10          # 每轮新生成、需要评价的后代数量
MAX_GENERATIONS = 20         # 初始化完成之后的演化轮数
MUTATION_RATE = 0.3          # 每个后代独立触发变异的概率

# 结果保存在本文件所在目录的 results 文件夹，可改为其他目录。
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def initialize_population(pop_size):
    pop_axmul = []
    pop_axadd = []
    for _ in range(pop_size):
        # 索引代表 Level，值代表选中了该 Level 的第几个变体。
        mul_genes = [random.randint(0, len(level_group) - 1) for level_group in ALM.MUL8_POOL]
        add_genes = [random.randint(0, len(level_group) - 1) for level_group in ALM.ADD16_POOL]
        pop_axmul.append(mul_genes)
        pop_axadd.append(add_genes)
    return pop_axmul, pop_axadd


def select_from_saved_fitness(pop_axmul, pop_axadd, fitnesses, top_k):
    """按已保存的适应度选择前若干个体，不重复调用评价函数。"""
    if not (len(pop_axmul) == len(pop_axadd) == len(fitnesses)):
        raise ValueError("乘法器基因、加法器基因与适应度的数量必须一致")
    if not 1 <= top_k <= len(fitnesses):
        raise ValueError("保留数量必须在 1 与候选个体总数之间")

    ranked = sorted(
        zip(pop_axmul, pop_axadd, fitnesses),
        key=lambda individual: individual[2],
        reverse=True,
    )[:top_k]
    return (
        [copy.deepcopy(mul_genes) for mul_genes, _, _ in ranked],
        [copy.deepcopy(add_genes) for _, add_genes, _ in ranked],
        [fitness for _, _, fitness in ranked],
    )


def report_best(stage, elite_mul, elite_add, fitnesses, evaluation_count):
    mul_str = ", ".join(f"L{level} 第{variant + 1}个" for level, variant in enumerate(elite_mul[0]))
    add_str = ", ".join(f"L{level} 第{variant + 1}个" for level, variant in enumerate(elite_add[0]))
    print(
        f"{stage} | Best Q(L): {fitnesses[0]:.4f} "
        f"MUL[{mul_str}] ADD[{add_str}] | 累计评价: {evaluation_count}"
    )


def decode_units(genes, pool):
    """把基因索引解析为可写入 JSON 的单元名称和硬件数据。"""
    units = []
    for level, variant_idx in enumerate(genes):
        unit = pool[level][variant_idx]
        units.append({
            "level": level,
            "variant_index": variant_idx,  # 从 0 开始，和程序内部基因一致
            "name": unit["name"],
            "area": unit.get("area"),
            "power": unit.get("power"),
        })
    return units


def atomic_write_text(path, content):
    """先写临时文件，再替换结果文件，避免中断留下半个 JSON。"""
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        temporary_path.write_text(content, encoding="utf-8")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def render_result_text(result):
    parameters = result["parameters"]
    status = "已完成" if result["status"] == "completed" else "运行中（已保存最近完成的一轮）"
    lines = [
        "AutoALib 实验结果",
        f"运行编号: {result['run_id']}",
        f"状态: {status}",
        f"开始时间: {result['started_at']}",
        f"更新时间: {result['updated_at']}",
        f"已完成演化轮数: {result['completed_generations']}/{parameters['max_generations']}",
        "说明: 第 0 轮为初始化，不计入演化轮数。",
        f"累计候选库评价次数: {result['evaluation_count']}",
        f"当前最优 Q(L): {result['best_fitness']:.12g}",
        f"运行时间（秒）: {result['elapsed_seconds']:.6f}",
        "",
        "实验参数:",
        f"初始个体数: {parameters['initial_population_size']}",
        f"保留父代数: {parameters['elite_size']}",
        f"每轮后代数: {parameters['offspring_size']}",
        f"演化轮数上限: {parameters['max_generations']}",
        f"每个后代的变异概率: {parameters['mutation_rate']}",
    ]
    experiment_lines = []
    if result.get("experiment_index") is not None:
        experiment_lines.append(f"独立实验序号: {result['experiment_index']}")
    if result.get("random_seed") is not None:
        experiment_lines.append(f"随机种子: {result['random_seed']}")
    lines[2:2] = experiment_lines
    for key, label in (("multipliers", "最优乘法器配置"), ("adders", "最优加法器配置")):
        lines.extend(["", f"{label}:"])
        for unit in result["best_library"][key]:
            lines.append(
                f"Level {unit['level']} | 第 {unit['variant_index'] + 1} 个单元 | "
                f"名称: {unit['name']} | 面积: {unit['area']} | 功耗: {unit['power']}"
            )

    lines.extend(["", "保存的父代（按适应度降序，基因索引从 0 开始）:"])
    for rank, (mul, add, fitness) in enumerate(
        zip(result["parent_mul"], result["parent_add"], result["parent_fitnesses"]),
        start=1,
    ):
        lines.append(f"排名 {rank} | Q(L): {fitness:.12g} | MUL{mul} ADD{add}")

    lines.extend(["", "每轮最优记录（第 0 轮为初始化）:"])
    for record in result["generation_history"]:
        lines.append(
            f"第 {record['generation']} 轮 | 累计评价: {record['evaluation_count']} | "
            f"Best Q(L): {record['best_fitness']:.12g} | "
            f"MUL{record['best_mul_genes']} ADD{record['best_add_genes']}"
        )
    return "\n".join(lines) + "\n"


def save_results(result):
    """同时保存结构化 JSON 和可直接阅读的 UTF-8 TXT。"""
    json_content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    txt_content = render_result_text(result)
    atomic_write_text(Path(result["output_files"]["json"]), json_content)
    atomic_write_text(Path(result["output_files"]["txt"]), txt_content)


def save_generation(result, generation, elite_mul, elite_add, fitnesses,
                    evaluation_count, started_clock):
    """保存本轮的父代、评分和最优记录，不进行额外的适应度评价。"""
    result.update({
        "status": "completed" if generation == result["parameters"]["max_generations"] else "running",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "completed_generations": generation,
        "elapsed_seconds": round(perf_counter() - started_clock, 6),
        "evaluation_count": evaluation_count,
        "parent_mul": copy.deepcopy(elite_mul),
        "parent_add": copy.deepcopy(elite_add),
        "parent_fitnesses": list(fitnesses),
        "best_fitness": fitnesses[0],
        "best_library": {
            "multipliers": decode_units(elite_mul[0], ALM.MUL8_POOL),
            "adders": decode_units(elite_add[0], ALM.ADD16_POOL),
        },
    })
    result["best_fitness_history"].append(fitnesses[0])
    result["generation_history"].append({
        "generation": generation,
        "evaluation_count": evaluation_count,
        "best_fitness": fitnesses[0],
        "best_mul_genes": copy.deepcopy(elite_mul[0]),
        "best_add_genes": copy.deepcopy(elite_add[0]),
    })
    save_results(result)


def run_aaa_framework(experiment_index=None, random_seed=None, output_dir=None):
    if not 2 <= ELITE_SIZE <= INITIAL_POPULATION_SIZE:
        raise ValueError("父代数量至少为 2，且不能超过初始个体数量")
    if OFFSPRING_SIZE < 1 or MAX_GENERATIONS < 0:
        raise ValueError("每轮后代数量必须为正，演化轮数不能为负")
    if not 0 <= MUTATION_RATE <= 1:
        raise ValueError("变异概率必须在 0 与 1 之间")

    if random_seed is not None:
        random.seed(random_seed)

    started_clock = perf_counter()
    started_at = datetime.now().astimezone()
    run_id = f"autoalib_{started_at:%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    output_dir = Path(RESULTS_DIR if output_dir is None else output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": 1,
        "run_id": run_id,
        "experiment_index": experiment_index,
        "random_seed": random_seed,
        "started_at": started_at.isoformat(timespec="seconds"),
        "parameters": {
            "initial_population_size": INITIAL_POPULATION_SIZE,
            "elite_size": ELITE_SIZE,
            "offspring_size": OFFSPRING_SIZE,
            "max_generations": MAX_GENERATIONS,
            "mutation_rate": MUTATION_RATE,
        },
        "output_files": {
            "json": str(output_dir / f"{run_id}.json"),
            "txt": str(output_dir / f"{run_id}.txt"),
        },
        "best_fitness_history": [],
        "generation_history": [],
    }

    print("--- 开始运行 AAA 近似资源库构建框架 ---")
    print("约束条件: 覆盖所有误差等级，且 Level 0 为精确计算单元")
    print(
        f"初始个体: {INITIAL_POPULATION_SIZE} | 父代: {ELITE_SIZE} | "
        f"每轮后代: {OFFSPRING_SIZE} | 演化轮数: {MAX_GENERATIONS}"
    )

    # 1. 初始个体只评价一次，保存前若干个父代的基因与适应度。
    pop_axmul, pop_axadd = initialize_population(INITIAL_POPULATION_SIZE)
    elite_mul, elite_add, fitnesses = GAChose.evaluate_and_select(
        pop_axmul, pop_axadd, top_k=ELITE_SIZE
    )
    evaluation_count = INITIAL_POPULATION_SIZE
    save_generation(result, 0, elite_mul, elite_add, fitnesses,
                    evaluation_count, started_clock)
    report_best("Initialization", elite_mul, elite_add, fitnesses, evaluation_count)
    print(f"JSON 结果路径: {result['output_files']['json']}")
    print(f"TXT 结果路径: {result['output_files']['txt']}")

    for gen in range(MAX_GENERATIONS):
        # 2. 现有交叉函数返回父代副本加后代，截取新增的后代参与变异。
        #    原父代及其评分始终保存在 elite_mul、elite_add、fitnesses 中。
        parent_count = len(elite_mul)
        crossed_mul, crossed_add = GAcross.cross(
            elite_mul,
            elite_add,
            target_pop_size=parent_count + OFFSPRING_SIZE,
        )
        offspring_mul, offspring_add = GAmutation.mut(
            crossed_mul[parent_count:],
            crossed_add[parent_count:],
            mutation_rate=MUTATION_RATE,
        )

        # 3. 只评价本轮后代。top_k 等于后代数，保留全部后代及其评分。
        offspring_mul, offspring_add, offspring_fitnesses = GAChose.evaluate_and_select(
            offspring_mul, offspring_add, top_k=OFFSPRING_SIZE
        )
        evaluation_count += len(offspring_fitnesses)

        # 4. 五个父代与十个后代合并，直接按保存的十五个评分选前五个。
        elite_mul, elite_add, fitnesses = select_from_saved_fitness(
            elite_mul + offspring_mul,
            elite_add + offspring_add,
            fitnesses + offspring_fitnesses,
            top_k=ELITE_SIZE,
        )
        save_generation(result, gen + 1, elite_mul, elite_add, fitnesses,
                        evaluation_count, started_clock)
        report_best(
            f"Generation {gen + 1}/{MAX_GENERATIONS}",
            elite_mul,
            elite_add,
            fitnesses,
            evaluation_count,
        )

    # 5. 最后一轮后代已经评价并参与合并选择，输出当前排名第一的父代。
    print("\n" + "=" * 70)
    print("--- 搜索完成: 最终构建的最优近似资源库 ---")
    print(f"最终 Best Q(L): {fitnesses[0]:.6f} | 总评价次数: {evaluation_count}")
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
    print(f"JSON 结果已保存: {result['output_files']['json']}")
    print(f"TXT 结果已保存: {result['output_files']['txt']}")

    return result


def save_experiment_summary(summary, started_clock):
    """每完成一次独立实验，更新整批实验的 JSON/TXT 汇总。"""
    experiments = summary["experiments"]
    scores = [item["best_fitness"] for item in experiments]
    summary.update({
        "status": "completed" if len(experiments) == summary["requested_experiments"] else "running",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "completed_experiments": len(experiments),
        "elapsed_seconds": round(perf_counter() - started_clock, 6),
        "total_evaluation_count": sum(item["evaluation_count"] for item in experiments),
        "statistics": None,
    })
    if scores:
        best = max(experiments, key=lambda item: item["best_fitness"])
        summary["statistics"] = {
            "max_best_fitness": max(scores),
            "min_best_fitness": min(scores),
            "mean_best_fitness": statistics.mean(scores),
            "sample_std_best_fitness": statistics.stdev(scores) if len(scores) > 1 else None,
            "best_experiment_index": best["experiment_index"],
            "mean_elapsed_seconds": statistics.mean(item["elapsed_seconds"] for item in experiments),
        }

    parameters = summary["parameters"]
    lines = [
        "AutoALib 独立实验汇总",
        f"批次编号: {summary['batch_id']}",
        f"状态: {'已完成' if summary['status'] == 'completed' else '运行中'}",
        f"开始时间: {summary['started_at']}",
        f"更新时间: {summary['updated_at']}",
        f"已完成独立实验: {summary['completed_experiments']}/{summary['requested_experiments']}",
        f"已完成实验的评价次数合计: {summary['total_evaluation_count']}",
        f"批次运行时间（秒）: {summary['elapsed_seconds']:.6f}",
        "",
        "每次独立实验的参数:",
        f"初始个体数: {parameters['initial_population_size']}",
        f"保留父代数: {parameters['elite_size']}",
        f"每次迭代生成的后代数: {parameters['offspring_size']}",
        f"初始化之后的迭代次数: {parameters['max_generations']}",
        f"后代变异概率: {parameters['mutation_rate']}",
    ]
    if summary["statistics"] is not None:
        stats = summary["statistics"]
        sample_std = stats["sample_std_best_fitness"]
        lines.extend([
            "",
            "已完成实验的最优评分统计:",
            f"最大值: {stats['max_best_fitness']:.12g}",
            f"最小值: {stats['min_best_fitness']:.12g}",
            f"平均值: {stats['mean_best_fitness']:.12g}",
            f"样本标准差: {sample_std if sample_std is not None else '至少完成两次实验后计算'}",
            f"最高评分对应实验序号: {stats['best_experiment_index']}",
        ])

    lines.extend(["", "各次独立实验结果:"])
    for item in experiments:
        lines.extend([
            f"实验 {item['experiment_index']:02d} | 随机种子: {item['random_seed']} | "
            f"最优 Q(L): {item['best_fitness']:.12g} | "
            f"评价次数: {item['evaluation_count']} | 耗时（秒）: {item['elapsed_seconds']:.6f}",
            f"  最优乘法器基因: {item['best_mul_genes']}",
            f"  最优加法器基因: {item['best_add_genes']}",
            f"  JSON: {item['output_files']['json']}",
            f"  TXT: {item['output_files']['txt']}",
        ])

    atomic_write_text(
        Path(summary["output_files"]["json"]),
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    )
    atomic_write_text(Path(summary["output_files"]["txt"]), "\n".join(lines) + "\n")


def run_independent_experiments(num_experiments=None):
    """独立执行多次完整搜索，不在实验之间传递父代或适应度。"""
    count = NUM_EXPERIMENTS if num_experiments is None else num_experiments
    if not isinstance(count, int) or count < 1:
        raise ValueError("独立实验次数必须为正整数")

    started_clock = perf_counter()
    started_at = datetime.now().astimezone()
    batch_id = f"batch_{started_at:%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    batch_dir = Path(RESULTS_DIR).expanduser().resolve() / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    # 每次使用不同的种子；种子生成器不依赖前一次搜索的随机状态。
    seeds = random.SystemRandom().sample(range(1, 2**31), count)
    summary = {
        "schema_version": 1,
        "batch_id": batch_id,
        "started_at": started_at.isoformat(timespec="seconds"),
        "requested_experiments": count,
        "parameters": {
            "initial_population_size": INITIAL_POPULATION_SIZE,
            "elite_size": ELITE_SIZE,
            "offspring_size": OFFSPRING_SIZE,
            "max_generations": MAX_GENERATIONS,
            "mutation_rate": MUTATION_RATE,
        },
        "experiment_seeds": seeds,
        "output_files": {
            "json": str(batch_dir / "summary.json"),
            "txt": str(batch_dir / "summary.txt"),
        },
        "experiments": [],
    }
    save_experiment_summary(summary, started_clock)

    for experiment_index, seed in enumerate(seeds, start=1):
        print(f"\n--- 独立实验 {experiment_index}/{count} | 随机种子: {seed} ---")
        result = run_aaa_framework(
            experiment_index=experiment_index,
            random_seed=seed,
            output_dir=batch_dir / f"experiment_{experiment_index:02d}",
        )
        summary["experiments"].append({
            "experiment_index": experiment_index,
            "random_seed": seed,
            "run_id": result["run_id"],
            "best_fitness": result["best_fitness"],
            "evaluation_count": result["evaluation_count"],
            "elapsed_seconds": result["elapsed_seconds"],
            "best_mul_genes": copy.deepcopy(result["parent_mul"][0]),
            "best_add_genes": copy.deepcopy(result["parent_add"][0]),
            "best_library": copy.deepcopy(result["best_library"]),
            "output_files": dict(result["output_files"]),
        })
        save_experiment_summary(summary, started_clock)

    print(f"\n{count} 次独立实验已完成，累计评价: {summary['total_evaluation_count']}")
    print(f"汇总 JSON: {summary['output_files']['json']}")
    print(f"汇总 TXT: {summary['output_files']['txt']}")
    return summary


if __name__ == '__main__':
    run_independent_experiments()


