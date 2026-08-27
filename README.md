# AutoALib

**Automatic Construction of High-Quality Approximate Unit Libraries for Approximate Design Space Exploration**

AutoALib is a genetic-algorithm-based framework for automatically constructing compact, representative, and high-quality approximate unit libraries (AxLibs) for approximate design space exploration (ADSE).

Approximate computing reduces hardware cost by allowing controlled accuracy loss. In an ADSE flow, the selected AxLib defines the candidate units available to every arithmetic node and therefore shapes the searchable design space. AutoALib treats AxLib construction as an optimization problem before ADSE: it evaluates candidate libraries under representative local error-propagation structures and searches for the library composition that offers the best balance between output error and hardware saving.

The AutoALib framework is available to the community at [https://github.com/Jianxu-Wei/AutoALib](https://github.com/Jianxu-Wei/AutoALib).

## Highlights

- Automatically selects approximate adders and multipliers from a candidate unit pool.
- Divides candidate units into approximation-level subsets and selects one unit from each subset to preserve coverage and diversity.
- Uses six representative three-node data-flow graphs (DFGs) to model local error propagation across addition and multiplication nodes.
- Evaluates each candidate AxLib using both output error and hardware saving.
- Aggregates performance across the six DFGs with a geometric mean so that a library must perform consistently across different structures.
- Uses genetic search with elitist selection, single-point crossover, and mutation.
- Can supply a constructed AxLib to different ADSE frameworks without modifying their original search procedures.

## Method Overview

AutoALib follows six main steps:

1. **Preprocess the unit pool.** Candidate adders and multipliers are sorted by an error metric and divided into non-overlapping approximation-level subsets.
2. **Encode a candidate AxLib.** A chromosome contains separate multiplier and adder rows. Each gene stores the local index of the unit selected from the corresponding approximation-level subset.
3. **Generate an initial population.** Valid unit indices are randomly sampled to create candidate libraries of the prescribed size.
4. **Evaluate each library.** Selected units are assigned to the six three-node DFGs. The resulting configurations are evaluated by Monte Carlo simulation using output error and hardware saving.
5. **Evolve the population.** Higher-fitness candidates are selected, recombined, and mutated to explore new AxLib compositions.
6. **Return the target AxLib.** After the maximum number of generations, the highest-fitness candidate is decoded into the final adder and multiplier library.

### Fitness Function

For a configuration $c$ under DFG $D_j$, the implementation computes its quality as

```math
R_j(c) = 100 \times \frac{w_A s_A(c) + w_P s_P(c)}{\max(e_j(c), 0.001)}
```

where $s_A(c)$ and $s_P(c)$ are the fractional area and power savings, respectively. The default settings are $w_A = 1$ and $w_P = 0$, so only area saving contributes to the score.

The quality of candidate library $L$ under DFG $D_j$ is the average quality of all configurations in $C_j(L)$:

```math
Q_j(L) = \frac{1}{|C_j(L)|}\sum_{c \in C_j(L)} R_j(c)
```

The final fitness is calculated across the six DFGs as

```math
Q(L) = \exp\left(\frac{1}{6}\sum_{j=1}^{6}\log\left(Q_j(L)+10^{-9}\right)\right)
```

Although `EPSILON = 1e-5` is defined in [`GAmedcomputing.py`](GAmedcomputing.py), it is not used in the current calculation. The effective error floor is `0.001`.

## Repository Structure

| Path | Description |
| --- | --- |
| [`main.py`](main.py) | Entry point, population initialization, genetic-search loop, and final AxLib reporting. |
| [`ApproxLibManager.py`](ApproxLibManager.py) | Exact-unit baselines, active adder and multiplier candidate pools, area/power metadata, and dynamic loading of compiled approximate units. |
| [`DFGparsing.py`](DFGparsing.py) | Parser for the CDFG/DFG descriptions. |
| [`GAmedcomputing.py`](GAmedcomputing.py) | Monte Carlo error simulation and candidate-library fitness evaluation. |
| [`GAChose.py`](GAChose.py) | Fitness ranking and Top-K selection. |
| [`GAcross.py`](GAcross.py) | Single-point crossover for the multiplier and adder chromosomes. |
| [`GAmutation.py`](GAmutation.py) | Level-constrained mutation. |
| [`applications/`](applications/) | Three-node DFG benchmark descriptions used to evaluate local error propagation. |
| [`approlib/`](approlib/) | Approximate-unit C sources and precompiled Linux shared libraries. |

## Requirements

- Linux on x86-64 is recommended because the supplied approximate units are precompiled as ELF `.so` shared libraries.
- Python 3.x. The current implementation uses only the Python standard library.
- A C compiler such as GCC is required only if the shared libraries need to be rebuilt.

Run AutoALib from the repository root. The implementation uses relative paths such as `applications/` and `approlib/`.

## Quick Start

```bash
git clone https://github.com/Jianxu-Wei/AutoALib.git
cd AutoALib
python3 main.py
```

During execution, AutoALib reports the best fitness in every generation. After the search terminates, it prints the selected multiplier and adder for every approximation level.

The default evaluation uses 100,000 random vectors for every approximate configuration and enumerates all feasible assignments for each active DFG. A complete run can therefore take substantial time. For a quick smoke test, temporarily reduce the `num_samples` default in `simulate_cdfg_error()` in [`GAmedcomputing.py`](GAmedcomputing.py), then restore it for experimental evaluation.

## Default Configuration in This Repository

| Parameter | Default value | Location |
| --- | ---: | --- |
| Population size | 10 | `main.py` |
| Maximum generations | 20 | `main.py` |
| Selected Top-K individuals | 5 | `main.py`, `GAChose.py` |
| Crossover | Separate single-point crossover for multiplier and adder chromosomes | `GAcross.py` |
| Mutation probability | 0.3 per individual | `main.py`, `GAmutation.py` |
| Monte Carlo vectors | 100,000 per configuration | `GAmedcomputing.py` |
| Error floor used by the implementation | 0.001 | `GAmedcomputing.py` |


The current source snapshot includes one exact level (Level 0) and three active approximate levels for both adders and multipliers. The exact unit in Level 0 is fixed because it is the only candidate in that subset.

The active DFG list is configured in `CDFG_FILES` in [`GAmedcomputing.py`](GAmedcomputing.py). The default list contains six three-node addition/multiplication structures used for library fitness evaluation.

## Using a Different Approximate Unit Pool

1. Add the approximate-unit source file to `approlib/`.
2. Build a shared library whose exported function name matches the unit name. For example:

   ```bash
   gcc -O2 -shared -fPIC approlib/example_unit.c -o approlib/example_unit.so
   ```

3. Add the unit name, area, and power metadata to the appropriate level in `ADD16_POOL` or `MUL8_POOL` in [`ApproxLibManager.py`](ApproxLibManager.py).
4. Confirm that the function accepts two unsigned integer arguments and returns an unsigned integer compatible with the `ctypes` declaration in `ApproxLibManager.py`.
5. Run `python3 main.py` again.

To use a different error metric or benchmark structure, update the simulation and fitness logic in [`GAmedcomputing.py`](GAmedcomputing.py) and modify the active DFG list. AutoALib is not restricted to mean error distance (MED), provided that the selected metric can be computed for each configuration.


## Contact

Questions, bug reports, and reproducibility feedback are welcome through [GitHub Issues](https://github.com/Jianxu-Wei/AutoALib/issues).

