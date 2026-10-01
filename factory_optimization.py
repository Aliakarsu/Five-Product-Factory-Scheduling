"""
================================================================================
 Factory Production Scheduling as a Mixed-Integer Program (MIP)
--------------------------------------------------------------------------------
 Author : Ali Akarsu
 Solver : PuLP (Python) with the CBC branch-and-bound solver
--------------------------------------------------------------------------------
 WHAT THIS SCRIPT DOES
   1. Encodes the factory production problem (5 products, 3 resources,
      production bounds and a fixed setup cost for P5).
   2. Builds and solves the FULL MIP (integer production + binary setup).
   3. Builds and solves the LP RELAXATION (all integrality dropped) so the
      two can be compared.
   4. Reports the solutions, the optimality gap, the binding (active)
      resource constraints, and a "force-P5" what-if used in the report.

 MATHEMATICAL MODEL (see report, Section "Problem Formulation")
   Decision variables
     x_p >= 0, integer        production quantity of product p in {P1..P5}
     y5  in {0,1}             1 if P5 is produced (triggers the setup cost)
   Objective (maximise profit net of setup cost)
     max  5 x1 + 4 x2 + 6 x3 + 7 x4 + 8 x5  -  30 y5
   Subject to
     2 x1 + 3 x2 + 1 x3 + 4 x4 + 5 x5 <= 95     (labour)
     3 x1 + 2 x2 + 4 x3 + 1 x4 + 3 x5 <= 80     (machine time)
     4 x1 + 1 x2 + 3 x3 + 2 x4 + 2 x5 <= 70     (raw materials)
     x1 <= 20                                   (P1 capacity)
     x2 + x3 >= 15                              (combined P2+P3 minimum)
     x4 >= 5                                    (P4 minimum)
     x5 <= M y5      with  M = floor(95/5) = 19 (fixed-charge link for P5)
================================================================================
"""

import pulp

# 1. PROBLEM DATA #
PRODUCTS = ["P1", "P2", "P3", "P4", "P5"]

PROFIT  = {"P1": 5, "P2": 4, "P3": 6, "P4": 7, "P5": 8}   # $ per unit
LABOUR  = {"P1": 2, "P2": 3, "P3": 1, "P4": 4, "P5": 5}   # units per item
MACHINE = {"P1": 3, "P2": 2, "P3": 4, "P4": 1, "P5": 3}   # units per item
RAW     = {"P1": 4, "P2": 1, "P3": 3, "P4": 2, "P5": 2}   # units per item

LABOUR_CAP  = 95      # total labour available
MACHINE_CAP = 80      # total machine time available
RAW_CAP     = 70      # total raw materials available

SETUP_P5 = 30         # fixed setup cost incurred if any P5 is produced

# Tight, valid big-M for the setup link: P5 alone cannot exceed
# floor(LABOUR_CAP / labour_per_P5) = floor(95/5) = 19 units.
BIG_M = LABOUR_CAP // LABOUR["P5"]


# ------------------------------------------------------------------ #
# 2. MODEL BUILDER                                                   #
#    `relaxation=True`  -> LP relaxation (continuous x, y5 in [0,1])  #
#    `relaxation=False` -> full MIP (integer x, binary y5)            #
# ------------------------------------------------------------------ #
def build_and_solve(relaxation: bool):
    prob = pulp.LpProblem("Factory_Production", pulp.LpMaximize)

    # --- Decision variables -------------------------------------- #
    if relaxation:
        x  = {p: pulp.LpVariable(f"x_{p}", lowBound=0, cat="Continuous")
              for p in PRODUCTS}
        y5 = pulp.LpVariable("y5", lowBound=0, upBound=1, cat="Continuous")
    else:
        x  = {p: pulp.LpVariable(f"x_{p}", lowBound=0, cat="Integer")
              for p in PRODUCTS}
        y5 = pulp.LpVariable("y5", cat="Binary")

    # --- Objective: profit minus fixed setup cost ---------------- #
    prob += (pulp.lpSum(PROFIT[p] * x[p] for p in PRODUCTS)
             - SETUP_P5 * y5), "Net_Profit"

    # --- Resource (capacity) constraints ------------------------- #
    prob += pulp.lpSum(LABOUR[p]  * x[p] for p in PRODUCTS) <= LABOUR_CAP,  "Labour"
    prob += pulp.lpSum(MACHINE[p] * x[p] for p in PRODUCTS) <= MACHINE_CAP, "Machine"
    prob += pulp.lpSum(RAW[p]     * x[p] for p in PRODUCTS) <= RAW_CAP,     "Raw"

    # --- Additional production constraints ----------------------- #
    prob += x["P1"] <= 20,                 "P1_capacity"
    prob += x["P2"] + x["P3"] >= 15,       "P2_P3_minimum"
    prob += x["P4"] >= 5,                  "P4_minimum"

    # --- Fixed-charge link: producing P5 forces the setup cost ---- #
    prob += x["P5"] <= BIG_M * y5,         "P5_setup_link"

    # --- Solve (CBC, silent) ------------------------------------- #
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    return {
        "status":    pulp.LpStatus[prob.status],
        "objective": pulp.value(prob.objective),
        "x":         {p: x[p].value() for p in PRODUCTS},
        "y5":        y5.value(),
        "prob":      prob,
    }


# 3. SOLVE BOTH MODELS #
lp  = build_and_solve(relaxation=True)
mip = build_and_solve(relaxation=False)


def show(title, res):
    print(f"\n{'='*52}\n {title}\n{'='*52}")
    print(f" Status     : {res['status']}")
    print(f" Objective  : {res['objective']:.4f}")
    for p in PRODUCTS:
        print(f"   {p} = {res['x'][p]:.4f}")
    print(f"   y5 = {res['y5']:.4f}")


show("LP RELAXATION  (upper bound)", lp)
show("MIP  (integer optimal)", mip)

# 4. LP vs MIP COMPARISON #

gap = lp["objective"] - mip["objective"]
gap_pct = 100 * gap / mip["objective"]
print(f"\n{'='*52}\n LP vs MIP COMPARISON\n{'='*52}")
print(f" LP relaxation objective (upper bound) : {lp['objective']:.2f}")
print(f" MIP integer objective                 : {mip['objective']:.2f}")
print(f" Absolute optimality gap               : {gap:.2f}")
print(f" Relative gap                          : {gap_pct:.2f}%")

# Naive rounding-down of the LP solution (illustrates why MIP != rounded LP)
rounded = {p: int(lp["x"][p]) for p in PRODUCTS}
rounded_obj = sum(PROFIT[p] * rounded[p] for p in PRODUCTS) \
              - SETUP_P5 * (1 if rounded["P5"] > 0 else 0)
print(f"\n Rounded-down LP solution              : {rounded}")
print(f" Objective of rounded-down LP          : {rounded_obj:.2f}"
      f"   (vs MIP {mip['objective']:.2f})")

# 5. BINDING-CONSTRAINT DIAGNOSTICS (MIP) #

print(f"\n{'='*52}\n RESOURCE USAGE AT MIP OPTIMUM\n{'='*52}")
usage = {
    "Labour":  (sum(LABOUR[p]  * mip["x"][p] for p in PRODUCTS), LABOUR_CAP),
    "Machine": (sum(MACHINE[p] * mip["x"][p] for p in PRODUCTS), MACHINE_CAP),
    "Raw":     (sum(RAW[p]     * mip["x"][p] for p in PRODUCTS), RAW_CAP),
}
for name, (used, cap) in usage.items():
    state = "BINDING" if abs(used - cap) < 1e-6 else f"slack = {cap - used:.1f}"
    print(f"   {name:8s}: {used:5.1f} / {cap:<3d}  ->  {state}")
