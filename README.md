# Five-Product Factory Scheduling

Production scheduling for a five-product factory, formulated as a
**Mixed-Integer Program (MIP)** and solved with [PuLP](https://github.com/coin-or/pulp)
and the CBC branch-and-bound solver. The factory chooses how many units of each
product to make so that profit, net of a fixed setup cost, is maximised under
labour, machine-time and raw-material limits.

The full write-up is in the report:
[`Production Scheduling under Resource and Setup-Cost Constraints A Mixed-Integer Programming Approach.pdf`](Production%20Scheduling%20under%20Resource%20and%20Setup-Cost%20Constraints%20A%20Mixed-Integer%20Programming%20Approach.pdf).

## Problem

| Product | Profit | Labour | Machine | Raw |
|---------|-------:|-------:|--------:|----:|
| P1      | 5      | 2      | 3       | 4   |
| P2      | 4      | 3      | 2       | 1   |
| P3      | 6      | 1      | 4       | 3   |
| P4      | 7      | 4      | 1       | 2   |
| P5      | 8      | 5      | 3       | 2   |

Capacities: labour 95, machine time 80, raw materials 70.

Additional rules: P1 is capped at 20 units, P2 + P3 must total at least 15,
P4 must be at least 5, and producing any P5 incurs a fixed setup cost of 30.

## Model

- `x_p` (integer, >= 0): units of product `p`
- `y5` (binary): 1 if P5 is produced, which triggers the setup cost

`
max   5 x1 + 4 x2 + 6 x3 + 7 x4 + 8 x5 - 30 y5
s.t.  2 x1 + 3 x2 + 1 x3 + 4 x4 + 5 x5 <= 95    (labour)
      3 x1 + 2 x2 + 4 x3 + 1 x4 + 3 x5 <= 80    (machine)
      4 x1 + 1 x2 + 3 x3 + 2 x4 + 2 x5 <= 70    (raw materials)
      x1 <= 20
      x2 + x3 >= 15
      x4 >= 5
      x5 <= 19 y5                               (fixed-charge link, M = floor(95/5))
`

The big-M value of 19 is the tightest valid bound: P5 alone cannot exceed
`floor(95 / 5)` units because of the labour limit.

## Results

| | Objective | P1 | P2 | P3 | P4 | P5 |
|---|---:|---:|---:|---:|---:|---:|
| LP relaxation (upper bound) | 202.50 | 0 | 5 | 10 | 17.5 | 0 |
| **MIP (integer optimal)** | **200.00** | 0 | 7 | 10 | 16 | 0 |

- Optimality gap between LP relaxation and MIP: 2.50 (1.25%).
- Rounding the LP solution down gives 199, which is worse than the MIP optimum
  of 200. Rounding is not a substitute for solving the integer program.
- At the MIP optimum, **labour is binding** (95 / 95), while machine time
  (70 / 80) and raw materials (69 / 70) have slack.
- The optimal plan does not produce P5, so the setup cost of 30 is never incurred.

## Run it

`ash
pip install -r requirements.txt
python factory_optimization.py
`

The script builds and solves both the LP relaxation and the full MIP, then
prints the comparison, the rounded-LP check and the resource usage. Problem
data is defined at the top of `factory_optimization.py`; `factory_data.csv`
and `resource_caps.csv` hold the same numbers in tabular form for reference.

## Files

| File | Description |
|------|-------------|
| `factory_optimization.py` | Model, solver and diagnostics |
| `factory_data.csv` | Profit and per-unit resource use for each product |
| `resource_caps.csv` | Resource capacities |
| `Production Scheduling under Resource and Setup-Cost Constraints A Mixed-Integer Programming Approach.pdf` | Project report |

## License

[MIT](LICENSE)