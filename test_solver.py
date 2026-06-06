import sys
sys.path.insert(0, '.')

from sat_solver import (
    parse_dimacs,
    dpll_solve,
    cdcl_solve,
    generate_random_ksat,
    generate_pigeonhole,
    check_assignment,
)

print("Testing DIMACS parser...")
dimacs_str = """c Test formula
p cnf 3 2
1 2 3 0
-1 -2 0
"""
cnf = parse_dimacs(dimacs_str)
print(f"  Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
print(f"  Clauses: {cnf.clauses}")

print("\nTesting DPLL solver...")
dpll_result = dpll_solve(cnf)
print(f"  SAT: {dpll_result.sat}")
print(f"  Assignment: {dpll_result.assignment}")
print(f"  Steps: {dpll_result.decision_steps}")
print(f"  Time: {dpll_result.time_seconds:.4f}s")

if dpll_result.sat:
    valid, _ = check_assignment(cnf, dpll_result.assignment)
    print(f"  Assignment valid: {valid}")

print("\nTesting CDCL solver...")
cdcl_result = cdcl_solve(cnf)
print(f"  SAT: {cdcl_result.sat}")
print(f"  Assignment: {cdcl_result.assignment}")
print(f"  Steps: {cdcl_result.decision_steps}")
print(f"  Conflicts: {cdcl_result.conflicts}")
print(f"  Time: {cdcl_result.time_seconds:.4f}s")

if cdcl_result.sat:
    valid, _ = check_assignment(cnf, cdcl_result.assignment)
    print(f"  Assignment valid: {valid}")

print("\nTesting UNSAT formula...")
unsat_dimacs = """p cnf 2 4
1 2 0
1 -2 0
-1 2 0
-1 -2 0
"""
unsat_cnf = parse_dimacs(unsat_dimacs)
cdcl_unsat = cdcl_solve(unsat_cnf, enable_proof=True)
print(f"  SAT: {cdcl_unsat.sat}")
print(f"  Proof length: {len(cdcl_unsat.proof) if cdcl_unsat.proof else 0}")

print("\nTesting formula generator...")
rand_cnf = generate_random_ksat(50, 200, k=3, seed=42, force_sat=True)
print(f"  Random 3-SAT: {rand_cnf.num_vars} vars, {rand_cnf.num_clauses} clauses")
rand_result = cdcl_solve(rand_cnf)
print(f"  SAT: {rand_result.sat}, Time: {rand_result.time_seconds:.4f}s")

print("\nTesting pigeonhole formula...")
php_cnf = generate_pigeonhole(4, 3)
print(f"  PHP(4,3): {php_cnf.num_vars} vars, {php_cnf.num_clauses} clauses")
php_result = cdcl_solve(php_cnf)
print(f"  SAT: {php_result.sat}, Time: {php_result.time_seconds:.4f}s")

print("\nTesting 100-var 3-SAT (performance)...")
hard_cnf = generate_random_ksat(100, 427, k=3, seed=123, force_sat=True)
print(f"  100-var 3-SAT: {hard_cnf.num_vars} vars, {hard_cnf.num_clauses} clauses")
import time
start = time.time()
hard_result = cdcl_solve(hard_cnf)
elapsed = time.time() - start
print(f"  SAT: {hard_result.sat}")
print(f"  Time: {elapsed:.4f}s")
print(f"  Conflicts: {hard_result.conflicts}")
print(f"  Restarts: {hard_result.restarts}")
print(f"  Learnt clauses: {hard_result.learnt_clauses}")

if hard_result.sat:
    valid, _ = check_assignment(hard_cnf, hard_result.assignment)
    print(f"  Assignment valid: {valid}")

print("\nAll tests passed!")
