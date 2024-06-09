import os.path
import datetime as dt
import pandas as pd
import numpy as np
import math
import cplex
import copy

def minimize_active_risk(benchmark_portfolio:dict, cash_drag:float, tr_matrix:pd.DataFrame) -> dict:
        """
        ============================================================
        This file gives us a sample to use Cplex Python API to
        establish a Quadratic Programming model and then solve it.
        The Quadratic Programming problem displayed below is as:
                         min z = xCx
           subject to:      cash > [cash_drag]
        ============================================================
        :param benchmark_portfolio: dictionary of the universe of assets that we can use to optimize and their weights represented in the benchmark_portfolio. The last asset has to be cash.
        :param cash_drag: cash drag constraint
        :param tr_matrix: returns matrix of the universe of assets
        :return:
        """

        sec_list = list(benchmark_portfolio.keys())

        # Input all the data and parameters here
        num_decision_var = len(benchmark_portfolio)

        # Establish the Linear Programming Model
        myProblem = cplex.Cplex()

        # Add the decision variables and set their lower bound and upper bound (if necessary)
        _names = ["w"+str(i) for i in sec_list]

        #add constrainst where assets cannot be over/under weight by 10%
        bound = 0.1
        myProblem.variables.add(ub=[bound]*num_decision_var, lb=[-bound]*num_decision_var, names=_names)

        # Add constraints
        _constraint1_var = [0]*(num_decision_var-1)
        _constraint1_var += [1] # assume the last asset is cash

        constraint_rows = [[_names, _constraint1_var], [_names, [1]*num_decision_var]]
        myProblem.linear_constraints.add(
                lin_expr=constraint_rows,
                rhs=[cash_drag, 0],
                names=["c{0}".format(i+1) for i in range(2)],
                senses=["G", "E"]
                )

        qmat = []

        # calculate covariance matrix with returns
        cov_matrix = tr_matrix.cov()
        for row_cov in cov_matrix.values:
            qmat.append([[j for j in range(num_decision_var)], 1e9*row_cov]) #default tolerance is set to 1e6. we need to increase the quadratic problem to optimize on a higher tolerance level.
        myProblem.objective.set_quadratic(qmat)

        # Solve the model and print the answer
        myProblem.solve()
        myProblem.objective.set_sense(myProblem.objective.sense.minimize)

        # objective_value = myProblem.solution.get_objective_value()
        solution_value = myProblem.solution.get_values()

        solution_output = {}
        for j, col in enumerate(tr_matrix.columns):
                solution_output[col] = solution_value[j] + benchmark_portfolio.get(col)

        return solution_output

        #
        # _solution = myProblem.solution.get_values()
        # _solution_active_wt = np.asarray(myProblem.solution.get_values(), dtype=np.float32) #assume the portfolio is in 100% cash. The index is an equal weight of the 6 bank stocks.
        # print(f"Solution: the 1 day active risk is {10000*math.sqrt(_solution_active_wt.dot(cov_matrix.values).dot(_solution_active_wt))}bps")
        # print(f"Solution: the active portfolio is:")
        # print(_solution_active_wt)
        #
        # # Display the active risk of the portfolio that keeps the remaining investments equally weighted
        # stock_active_wt = ((1-cash_drag)/6)-(1/6)
        # _default = [stock_active_wt]*(num_decision_var-1)
        # _default.append(cash_drag)
        # _default_active_wt = np.asarray(_default, dtype=np.float32)
        # print(f"Default: the 1 day active risk is {10000*math.sqrt(_default_active_wt.dot(cov_matrix.values).dot(_default_active_wt))}bps")
        # print(f"Default: the active portfolio is:")
        # print(_default_active_wt)