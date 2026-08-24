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

The implementation generalizes the hardware-saving term as a weighted combination of area and power saving. Its default settings optimize area only.

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
| Random input range | 0 to 127 | `GAmedcomputing.py` |
| Area weight | 1 | `GAmedcomputing.py` |
| Power weight | 0 | `GAmedcomputing.py` |
| Error floor used by the implementation | 0.001 | `GAmedcomputing.py` |
| Random seed | Not fixed | - |

The current source snapshot includes one exact level (Level 0) and three active approximate levels for both adders and multipliers. The exact unit in Level 0 is fixed because it is the only candidate in that subset.

The active DFG list is configured in `CDFG_FILES` in [`GAmedcomputing.py`](GAmedcomputing.py). The default list contains six three-node structures corresponding to the representative addition/multiplication patterns described in the paper.

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

## Results Reported in the Paper

The paper evaluates AutoALib with two representative ADSE frameworks:

- **ENAP**, a heuristic genetic-search framework.
- **FPAX**, a neural-network-based framework that uses transfer learning.

Four benchmark applications are evaluated under multiple MED constraints: FIR, 3x3 convolution, Sobel, and DCT. The original search algorithms and settings of ENAP and FPAX are retained; only the AxLib is replaced.

The reported results show that:

- AxLibs with higher $Q(L)$ values consistently enable more favorable candidate configuration spaces.
- AutoALib improves the final ADSE area-saving results in both ENAP and FPAX.
- The maximum reported improvement in area saving is approximately **62%**, obtained for 3x3 convolution under `MED < 15` with FPAX.
- The maximum reported improvement in cost effectiveness, measured as area saving per unit of MED, is approximately **91%**, obtained for FIR under `MED < 10` with FPAX.

These values are the experimental results reported in the accompanying paper. Reproduction requires the corresponding ENAP/FPAX flows, application inputs, synthesis setup, and error constraints in addition to the core AutoALib implementation in this repository.

## Troubleshooting

### No approximate units are loaded

Run the program from the repository root and confirm that `approlib/*.so` exists. If the supplied shared libraries are incompatible with the current Linux distribution or processor architecture, rebuild them from the corresponding C sources.

### `cannot open shared object file`

Check the current working directory and the `.so` architecture. The precompiled libraries are intended for Linux x86-64 and cannot normally be loaded directly on Windows.

### Results change between runs

The current implementation does not set a random seed. Add a fixed `random.seed(...)` before population initialization and error simulation when deterministic repetition is required.

## Citation

If AutoALib is useful in your work, please cite the accompanying manuscript:

```bibtex
@article{dou2026autoalib,
  author  = {Yuqin Dou and Jianxu Wei and Heyang Yao and Jiang Li and Xiaojuan Lian and Yijun Cui and Weiqiang Liu},
  title   = {AutoALib: Automatic Construction of High-Quality Approximate Unit Libraries for Approximate Design Space Exploration},
  year    = {2026},
  note    = {Manuscript}
}
```

Please replace the manuscript metadata above with the final journal, volume, pages, and DOI after publication.

## Third-Party Units and Attribution

The approximate arithmetic units in `approlib/` are derived from EvoApproxLib. Their C source files retain the original license notices and citation information. If these units are used in research, please also cite:

> V. Mrazek, L. Sekanina, and Z. Vasicek, "Libraries of Approximate Circuits: Automated Design and Application in CNN Accelerators," *IEEE Journal on Emerging and Selected Topics in Circuits and Systems*, vol. 10, no. 4, pp. 406-418, 2020.

This repository currently does not contain a separate top-level `LICENSE` file. Review the notices in the included third-party source files and add an appropriate project-level license before redistribution.

## Related Work

- Y. Dou, C. Wang, R. Woods, and W. Liu, "ENAP: An Efficient Number-Aware Pruning Framework for Design Space Exploration of Approximate Configurations," *IEEE Transactions on Circuits and Systems I: Regular Papers*, 2023.
- Y. Dou, C. Wang, H. Waris, R. Woods, and W. Liu, "FPAX: A Fast Prior Knowledge-Based Framework for DSE in Approximate Configurations," *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems*, 2023.

## Contact

Questions, bug reports, and reproducibility feedback are welcome through [GitHub Issues](https://github.com/Jianxu-Wei/AutoALib/issues).

