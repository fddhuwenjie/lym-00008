import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import parse_dimacs
import time

print("Debugging CDCL solver...")

dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
cnf = parse_dimacs(dimacs_unsat)
print(f"CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
print(f"Clauses: {cnf.clauses}")

# Manually trace the solver
from sat_solver.cdcl import CDCLSolver

solver = CDCLSolver(cnf, enable_proof=True)

print("\nInitial state:")
print(f"  num_vars: {solver.num_vars}")
print(f"  clauses: {solver.clauses}")

# Initial propagation
print("\nInitial propagation...")
conflict = solver._propagate()
print(f"  conflict after initial propagate: {conflict}")
print(f"  trail: {solver.trail}")
print(f"  decision_level: {solver.decision_level}")

if conflict is None:
    # Pick a variable
    var = solver._pick_branching_variable()
    print(f"\nPicked variable: {var}")
    
    # Make a decision
    solver.decisions += 1
    solver.decision_level += 1
    solver.trail_lim.append(len(solver.trail))
    print(f"  trail_lim after append: {solver.trail_lim}")
    
    solver._assign(var if True else -var, reason=None)
    print(f"  trail after assign: {solver.trail}")
    print(f"  var 1 value: {solver.vars[1].value}")
    print(f"  var 2 value: {solver.vars[2].value}")
    
    # Propagate
    print("\nPropagating after decision...")
    conflict = solver._propagate()
    print(f"  conflict: {conflict}")
    print(f"  trail: {solver.trail}")
    print(f"  var 1 value: {solver.vars[1].value}")
    print(f"  var 2 value: {solver.vars[2].value}")
    
    if conflict is not None:
        print(f"\nAnalyzing conflict: {conflict}")
        learnt_clause, backtrack_level = solver._analyze_conflict(conflict)
        print(f"  learnt_clause: {learnt_clause}")
        print(f"  backtrack_level: {backtrack_level}")
        
        # Check decision levels of literals in learnt clause
        print("\n  Decision levels in learnt clause:")
        for lit in learnt_clause:
            print(f"    lit {lit}: var {abs(lit)} level {solver.vars[abs(lit)].decision_level}")
        
        print(f"\n  Current decision_level: {solver.decision_level}")
        print(f"  backtrack_level < decision_level: {backtrack_level < solver.decision_level}")
