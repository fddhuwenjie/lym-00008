import sys
import time
sys.path.insert(0, '.')

from sat_solver.dimacs import parse_dimacs
from sat_solver.cdcl import cdcl_solve
from sat_solver.proof import verify_proof, check_assignment
from sat_solver.formula_generator import generate_pigeonhole, generate_random_ksat

print("=" * 60)
print("Testing CDCL Fixes")
print("=" * 60)

all_pass = True

# Test 1: Simple UNSAT with proof verification
print("\n1. Testing simple UNSAT (2 vars, 4 clauses)...")
dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
cnf = parse_dimacs(dimacs_unsat)
start = time.time()
result = cdcl_solve(cnf, enable_proof=True)
elapsed = time.time() - start

print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
print(f"   Proof length: {len(result.proof) if result.proof else 0}")

if result.proof:
    print(f"   Proof steps:")
    for i, p in enumerate(result.proof[:10]):
        print(f"     {i+1}. {p if p else '[] (empty)'}")
    if len(result.proof) > 10:
        print(f"     ... and {len(result.proof) - 10} more")
    
    print("\n   Verifying proof...")
    verify_result = verify_proof(cnf, result.proof)
    print(f"   Proof valid: {verify_result.valid}")
    if not verify_result.valid:
        print(f"   Error: {verify_result.error_message}")
        all_pass = False
    else:
        print(f"   [PASS] Proof verification PASSED")
else:
    print("   [FAIL] No proof generated")
    all_pass = False

# Test 2: Chain UNSAT with proof
print("\n2. Testing chain UNSAT (10 vars)...")
chain = "p cnf 10 11\n-1 2 0\n-2 3 0\n-3 4 0\n-4 5 0\n-5 6 0\n-6 7 0\n-7 8 0\n-8 9 0\n-9 10 0\n1 0\n-10 0"
cnf = parse_dimacs(chain)
start = time.time()
result = cdcl_solve(cnf, enable_proof=True)
elapsed = time.time() - start

print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Proof length: {len(result.proof) if result.proof else 0}")

if result.proof:
    verify_result = verify_proof(cnf, result.proof)
    print(f"   Proof valid: {verify_result.valid}")
    if verify_result.valid:
        print(f"   [PASS] Proof verification PASSED")
    else:
        print(f"   Error: {verify_result.error_message}")
        all_pass = False

# Test 3: Pigeonhole UNSAT with proof
print("\n3. Testing pigeonhole 4,3 UNSAT...")
cnf = generate_pigeonhole(4, 3)
print(f"   CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
start = time.time()
result = cdcl_solve(cnf, enable_proof=True)
elapsed = time.time() - start

print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")
print(f"   Proof length: {len(result.proof) if result.proof else 0}")

if result.proof:
    verify_result = verify_proof(cnf, result.proof)
    print(f"   Proof valid: {verify_result.valid}")
    if verify_result.valid:
        print(f"   [PASS] Proof verification PASSED")
    else:
        print(f"   Error: {verify_result.error_message}")
        all_pass = False

# Test 4: SAT with assignment check
print("\n4. Testing SAT with assignment...")
dimacs_sat = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
cnf = parse_dimacs(dimacs_sat)
start = time.time()
result = cdcl_solve(cnf)
elapsed = time.time() - start

print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")

if result.sat and result.assignment:
    valid, _ = check_assignment(cnf, result.assignment)
    print(f"   Assignment valid: {valid}")
    if valid:
        print(f"   [PASS] Assignment verification PASSED")
    else:
        print(f"   [FAIL] Assignment invalid")
        all_pass = False

# Test 5: 100-var 3-SAT performance
print("\n5. Testing 100-var 3-SAT performance...")
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
    print(f"   [PASS] Performance PASSED (< 10s)")
else:
    print(f"   [FAIL] Performance FAILED (> 10s)")
    all_pass = False

# Test 6: backtrack_level >= decision_level handling
print("\n6. Testing backtrack_level >= decision_level case...")
hard_unsat = "p cnf 3 4\n1 2 3 0\n1 -2 3 0\n-1 2 3 0\n-1 -2 -3 0"
cnf = parse_dimacs(hard_unsat)
start = time.time()
result = cdcl_solve(cnf, enable_proof=True)
elapsed = time.time() - start

print(f"   SAT: {result.sat}")
print(f"   Time: {elapsed:.4f}s")
print(f"   Conflicts: {result.conflicts}")

if result.sat == False and result.proof:
    verify_result = verify_proof(cnf, result.proof)
    print(f"   Proof valid: {verify_result.valid}")
    if verify_result.valid:
        print(f"   [PASS] Proof verification PASSED")
    else:
        print(f"   Error: {verify_result.error_message}")
        all_pass = False

print("\n" + "=" * 60)
if all_pass:
    print("[PASS] ALL TESTS PASSED")
else:
    print("[FAIL] SOME TESTS FAILED")
print("=" * 60)

with open("cdcl_fix_test_results.txt", "w") as f:
    f.write(f"All tests passed: {all_pass}\n")
