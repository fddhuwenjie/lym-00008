import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import parse_dimacs
from sat_solver.cdcl import cdcl_solve
import time

print("=" * 60)
print("Direct CDCL Solver Test")
print("=" * 60)

# Test 1: Simple SAT
print("\n1. Testing simple SAT formula...")
dimacs_sat = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
cnf = parse_dimacs(dimacs_sat)
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start
print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
print(f"   Restarts: {result.restarts}")
if result.assignment:
    print(f"   Assignment size: {len(result.assignment)}")

# Test 2: Simple UNSAT
print("\n2. Testing simple UNSAT formula (2 vars, 4 clauses)...")
dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
cnf = parse_dimacs(dimacs_unsat)
start = time.time()
result = cdcl_solve(cnf, enable_proof=True)
elapsed = time.time() - start
print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
if result.proof:
    print(f"   Proof length: {len(result.proof)}")
    for i, p in enumerate(result.proof[:5]):
        print(f"     {i+1}: {p}")

# Test 3: Chain UNSAT
print("\n3. Testing chain formula UNSAT (10 vars)...")
chain = "p cnf 10 11\n-1 2 0\n-2 3 0\n-3 4 0\n-4 5 0\n-5 6 0\n-6 7 0\n-7 8 0\n-8 9 0\n-9 10 0\n1 0\n-10 0"
cnf = parse_dimacs(chain)
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start
print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")

# Test 4: Pigeonhole 4,3
print("\n4. Testing pigeonhole 4,3...")
from sat_solver.formula_generator import generate_pigeonhole
cnf = generate_pigeonhole(4, 3)
print(f"   CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start
print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
print(f"   Restarts: {result.restarts}")
print(f"   Learnt clauses: {result.learnt_clauses}")

# Test 5: 100-var 3-SAT
print("\n5. Testing 100-var 3-SAT...")
from sat_solver.formula_generator import generate_random_ksat
cnf = generate_random_ksat(100, 427, 3, seed=123, force_sat=True)
print(f"   CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start
print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
print(f"   Restarts: {result.restarts}")
print(f"   Learnt clauses: {result.learnt_clauses}")
if elapsed < 10:
    print("   PERFORMANCE PASS (< 10s)")
else:
    print("   PERFORMANCE WARNING (> 10s)")

print("\n" + "=" * 60)
print("All direct tests completed!")
print("=" * 60)
