# AutoALib

**Automatic Construction of High-Quality Approximate Unit Libraries for Approximate Design Space Exploration**

AutoALib is a genetic-algorithm-based framework for automatically constructing compact, representative, and high-quality approximate unit libraries (AxLibs) for approximate design space exploration (ADSE).

Approximate computing reduces hardware cost by allowing controlled accuracy loss. In an ADSE flow, the selected AxLib defines the candidate units available to every arithmetic node and therefore shapes the searchable design space. AutoALib treats AxLib construction as an optimization problem before ADSE: it evaluates candidate libraries under representative local error-propagation structures and searches for the library composition that offers the best balance between output error and hardware saving.

The AutoALib framework is available to the community at [https://github.com/Jianxu-Wei/AutoALib](https://github.com/Jianxu-Wei/AutoALib).

## Highlights

- Selects approximate adders and multipliers from a candidate unit pool.
- Organizes candidate units into approximation-level subsets and selects one unit from each subset to preserve coverage and diversity.
- Uses six representative three-node data-flow graphs (DFGs) to model local error propagation across addition and multiplication nodes.
- Evaluates each candidate AxLib using output error and hardware saving.
- Aggregates performance across the six DFGs with a geometric mean so that a library must perform consistently across different structures.
- Uses genetic search with Top-K parent selection, separate single-point crossover, and mutation.
- Can provide a constructed AxLib to different ADSE frameworks without modifying their original search procedures.

## Method Overview

The paper describes the following six-stage workflow:

1. **Preprocess the unit pool.** Candidate adders and multipliers are sorted by an error metric and divided into non-overlapping approximation-level subsets.
2. **Encode a candidate AxLib.** A chromosome contains separate multiplier and adder rows. Each gene stores the local index of the unit selected from the corresponding approximation-level subset.
3. **Generate an initial population.** Valid unit indices are randomly sampled to create candidate libraries of the prescribed size.
4. **Evaluate each library.** The selected units are enumerated over the six three-node DFGs. Every resulting configuration is evaluated by Monte Carlo simulation using output error and hardware saving.
5. **Evolve the population.** Candidates are ranked by fitness; the Top-K candidates form the parent pool, crossover restores the target population size, and mutation is then applied to the resulting population.
6. **Return the target AxLib.** After the maximum number of generations, the highest-fitness candidate from the last evaluated generation is decoded into the final adder and multiplier library.

In the current repository snapshot, the preprocessing result is already encoded manually in `ADD16_POOL` and `MUL8_POOL` in [`ApproxLibManager.py`](ApproxLibManager.py). The code does not automatically sort a raw unit pool or create the approximation-level subsets at runtime.

### Fitness Defined in the Paper

For a configuration $c$ under DFG $D_j$, the paper defines its quality as

$$
R_j(c) = \frac{\operatorname{Save}_j(c)}{\operatorname{Error}_j(c) + \epsilon}.
$$

The quality of candidate library $L$ under $D_j$ is the average quality of all feasible configurations $C_j(L)$:

$$
Q_j(L) = \frac{1}{|C_j(L)|}\sum_{c \in C_j(L)} R_j(c).
$$

The final fitness is the geometric mean over the six DFGs:

$$
Q(L) = \left(\prod_{j=1}^{6} Q_j(L)\right)^{1/6}.
$$

### Fitness Used by the Current Code

The implementation uses the following per-configuration score:

$$
R_{\mathrm{impl}} = 100 \times \frac{w_A s_A + w_P s_P}{\max(e_{\mathrm{CDFG}}, 0.001)},
$$

where $s_A$ and $s_P$ are the fractional area and power savings. The defaults are `WEIGHT_AREA = 1` and `WEIGHT_POWER = 0`, so the current search optimizes area saving only. The DFG-level scores are averaged and then combined as

$$
Q_{\mathrm{impl}}(L) = \exp\left(\frac{1}{6}\sum_{j=1}^{6}\log(Q_j(L)+10^{-9})\right).
$$

`EPSILON = 1e-5` is defined in [`GAmedcomputing.py`](GAmedcomputing.py) but is not currently used; the effective error floor in the implementation is `0.001`.

## Repository Structure

| Path | Description |
| --- | --- |
| [`main.py`](main.py) | Entry point, population initialization, genetic-search loop, and final AxLib reporting. |
| [`ApproxLibManager.py`](ApproxLibManager.py) | Exact-unit baselines, active adder and multiplier candidate pools, area/power metadata, and dynamic loading of compiled approximate units. |
| [`DFGparsing.py`](DFGparsing.py) | Parser for the CDFG/DFG descriptions. |
| [`GAmedcomputing.py`](GAmedcomputing.py) | Monte Carlo error simulation and candidate-library fitness evaluation. |
| [`GAChose.py`](GAChose.py) | Fitness ranking and Top-K selection. |
| [`GAcross.py`](GAcross.py) | Separate single-point crossover for multiplier and adder chromosomes. |
| [`GAmutation.py`](GAmutation.py) | Level-constrained mutation of the resulting population. |
| [`applications/`](applications/) | Three-node DFG descriptions used to evaluate local error propagation. |
| [`approlib/`](approlib/) | Approximate-unit C sources and precompiled Linux shared libraries. |

## Requirements

- Linux on x86-64 for the supplied precompiled ELF `.so` libraries. On another platform, rebuild the libraries for that platform before running the experiment.
- Python 3.8 or later is recommended. The current implementation uses only the Python standard library.
- A C compiler such as GCC is required only when rebuilding shared libraries.

Run AutoALib from the repository root because the implementation uses relative paths such as `applications/` and `approlib/`.

## Important Startup Fix for the Current Snapshot

The bottom of [`DFGparsing.py`](DFGparsing.py) contains a legacy import-time demonstration that attempts to open `applications/sobel.cdfg`, but that file is not included in this repository. As a result, an unmodified `python3 main.py` currently stops with `FileNotFoundError`.

Before running AutoALib, remove or comment out these three lines at the end of `DFGparsing.py`:

```python
reg = RegMatch()
reg.load_txt()
reg.format_data()
```

This demonstration is not used by the AutoALib search. `GAmedcomputing.py` creates its own `RegMatch` instance and loads the active files listed in `CDFG_FILES`.

## Quick Start

```bash
git clone https://github.com/Jianxu-Wei/AutoALib.git
cd AutoALib

# First apply the DFGparsing.py cleanup described above.
python3 main.py
```

During execution, AutoALib reports the best fitness in every generation. After the search terminates, it prints the selected multiplier and adder for every approximation level.

The default evaluation uses 100,000 random vectors for every approximate configuration and enumerates all feasible assignments for each active DFG. A complete run can therefore take substantial time. For a quick smoke test, temporarily reduce the `num_samples` default in `simulate_cdfg_error()` in [`GAmedcomputing.py`](GAmedcomputing.py), then restore it for experimental evaluation.

## Default Configuration in This Repository

| Parameter | Effective default | Notes |
| --- | ---: | --- |
| Population size | 10 | Set in `main.py`. |
| Maximum generations | 20 | The only termination condition. |
| Top-K parent pool | 5 | Candidates are sorted by decreasing fitness. |
| Crossover | Separate single-point crossover | Crossover is always used when generating offspring; no crossover probability is defined. |
| Mutation trigger probability | 0.3 per individual | When triggered, one multiplier level and one adder level are selected. A mutation attempt can leave a gene unchanged. |
| Monte Carlo vectors | 100,000 per configuration | Default argument of `simulate_cdfg_error()`. |
| Random input range | 0 to 127 | Applied to primary DFG inputs. |
| Area weight | 1 | Area saving is active. |
| Power weight | 0 | Power saving is computed but does not affect fitness. |
| Error floor | 0.001 | Used as `max(error, 0.001)`. |
| Log stabilizer | `1e-9` | Added before the logarithm in the geometric mean. |
| Random seed | Not fixed | Results can vary between runs. |

The Top-K candidates are copied into the next population before crossover, but [`GAmutation.py`](GAmutation.py) subsequently applies mutation to the entire resulting population. Therefore, the current code does not guarantee that elite candidates remain unchanged.

The active candidate pools contain one exact level (Level 0) and three approximate levels for both adders and multipliers. Level 0 is fixed because it contains only the exact unit.

The six active DFG files are configured in `CDFG_FILES` in [`GAmedcomputing.py`](GAmedcomputing.py):

```text
tree.cdfg, tree1.cdfg, tree2.cdfg,
tree3.cdfg, tree4.cdfg, tree5.cdfg
```

## Validating a Run

At startup, `ApproxLibManager.py` prints the number of successfully loaded approximate operators. Confirm that all active non-exact operators have been loaded. Loading errors are currently suppressed, and a missing operator silently falls back to exact arithmetic during simulation; results from such a run are not a valid approximate-library evaluation.

For reproducible experiments, set a fixed random seed before both population initialization and Monte Carlo simulation, and record the platform, compiler, active pool definitions, DFG list, sample count, and fitness weights.

## Using a Different Approximate Unit Pool

1. Add the approximate-unit source file to `approlib/`.
2. Build a shared library whose exported function name matches the unit name. For example:

   ```bash
   gcc -O2 -shared -fPIC approlib/example_unit.c -o approlib/example_unit.so
   ```

3. Add the unit name, area, and power metadata to the appropriate level in `ADD16_POOL` or `MUL8_POOL` in [`ApproxLibManager.py`](ApproxLibManager.py).
4. Confirm that the function accepts two unsigned 64-bit integer arguments and returns an unsigned 64-bit integer compatible with the `ctypes` declaration in `ApproxLibManager.py`.
5. Run `python3 main.py` again and verify the loaded-operator count.

To use a different error metric or benchmark structure, update the simulation and fitness logic in [`GAmedcomputing.py`](GAmedcomputing.py) and modify the active DFG list. AutoALib is not restricted to mean error distance (MED), provided that the selected metric can be computed for each configuration.

## Current Implementation Limitations

- Approximation-level preprocessing is represented by manually defined pools rather than an automated sorting and partitioning stage.
- The import-time demonstration in `DFGparsing.py` must be removed or supplied with its missing example file before the current snapshot can start.
- Shared-library loading errors are suppressed; always verify the reported loaded-operator count.
- The random seed is not fixed, so repeated runs are not deterministic.
- The current mutation implementation performs random replacement within a level, rather than the `+1` or `-1` neighboring-index mutation described in the paper.

## Contact

Questions, bug reports, and reproducibility feedback are welcome through [GitHub Issues](https://github.com/Jianxu-Wei/AutoALib/issues).

