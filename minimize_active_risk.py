import os.path

import process_historical_data as historical
import datetime as dt
import pandas as pd
import numpy as np
import math
import cplex
import copy

# ============================================================
# This file gives us a sample to use Cplex Python API to
# establish a Quadratic Programming model and then solve it.
# The Quadratic Programming problem displayed below is as:
#                  min z = xCx
#    subject to:      cash > [cash_drag]
# ============================================================


sec_list = ["BMO CN", "BNS CN", "TD CN", "CM CN", "RY CN", "NA CN"]
cash_drag = 50/10000

# ============================================================
# calculate portfolio statistical values
returns_matrix = historical.calc_returns_matrix(sec_list)
cov_matrix = returns_matrix.cov()
sec_list.append("cash")
# ============================================================

# Input all the data and parameters here
num_decision_var = len(sec_list)
num_constraints = 2

# Establish the Linear Programming Model
myProblem = cplex.Cplex()

# Add the decision variables and set their lower bound and upper bound (if necessary)
_names = ["w"+str(i) for i in sec_list]
bound = 0.03
myProblem.variables.add(ub=[bound]*num_decision_var, lb=[-bound]*num_decision_var, names=_names)

# Add constraints
constraint_rows = [[_names, [0, 0, 0, 0, 0, 0, 1]], [_names, [1]*num_decision_var]]
myProblem.linear_constraints.add(
        lin_expr=constraint_rows,
        rhs=[cash_drag, 0],
        names=["c{0}".format(i+1) for i in range(2)],
        senses=["G", "E"]
        )

qmat = []
for row_cov in cov_matrix.values:
    qmat.append([[j for j in range(num_decision_var)], 1e9*row_cov]) #default tolerance is set to 1e6. we need to increase the quadratic problem to optimize on a higher tolerance level.
myProblem.objective.set_quadratic(qmat)

# Solve the model and print the answer
myProblem.solve()
myProblem.objective.set_sense(myProblem.objective.sense.minimize)
_solution = myProblem.solution.get_values()
_solution_active_wt = np.asarray(myProblem.solution.get_values(), dtype=np.float32) #assume the portfolio is in 100% cash. The index is an equal weight of the 6 bank stocks.
print(f"Solution: the 1 day active risk is {10000*math.sqrt(_solution_active_wt.dot(cov_matrix.values).dot(_solution_active_wt))}bps")
print(f"Solution: the active portfolio is:")
print(_solution_active_wt)

# Display the active risk of the portfolio that keeps the remaining investments equally weighted
stock_active_wt = ((1-cash_drag)/6)-(1/6)
_default = [stock_active_wt]*(num_decision_var-1)
_default.append(cash_drag)
_default_active_wt = np.asarray(_default, dtype=np.float32)
print(f"Default: the 1 day active risk is {10000*math.sqrt(_default_active_wt.dot(cov_matrix.values).dot(_default_active_wt))}bps")
print(f"Default: the active portfolio is:")
print(_default_active_wt)

# active_risk = 10000*math.sqrt(_solution_active_wt.dot(cov_matrix.values).dot(_solution_active_wt))
# output_lis = copy.deepcopy(_solution_active_wt)
# output_lis = np.append(output_lis, cash_lbound)
# output_lis = np.append(output_lis, cash_ubound)
# output_lis = np.append(output_lis, active_risk)
#
# col_name = sec_list
# col_name.append("lower")
# col_name.append("upper")
# col_name.append("active_risk")
#
# output = pd.DataFrame([output_lis], columns=col_name)
# output.to_csv("analysis.csv", header=True, index=False, sep=',', mode='w')