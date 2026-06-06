import sys
import time
sys.path.insert(0, '.')

from sat_solver.dimacs import parse_dimacs
from sat_solver.cdcl import cdcl_solve
from sat_solver.formula_generator import generate_random_ksat
from sat_solver.proof import check_assignment

print("=" * 60)
print("Performance Test: 100-var 3-SAT")
print("=" * 60)

print("\nGenerating 100-var 3-SAT formula at phase transition...")
cnf = generate_random_ksat(100, 427, 3, seed=123, force_sat=True)
print(f"CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")

print("\nSolving with CDCL...")
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start

print(f"\nResults:")
print(f"  SAT: {result.sat}")
print(f"  Time: {elapsed:.4f}s")
print(f"  Conflicts: {result.conflicts}")
print(f"  Restarts: {result.restarts}")
print(f"  Learnt clauses: {result.learnt_clauses}")
print(f"  Decision steps: {result.decision_steps}")

if result.sat and result.assignment:
    valid, _ = check_assignment(cnf, result.assignment)
    print(f"  Assignment valid: {valid}")

if elapsed < 10:
    print(f"\n✓ PERFORMANCE PASS: {elapsed:.4f}s < 10s")
else:
    print(f"\n✗ PERFORMANCE FAIL: {elapsed:.4f}s > 10s")

print("\n" + "=" * 60)
