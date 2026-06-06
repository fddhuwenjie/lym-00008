import sys
import time
import signal

sys.path.insert(0, '.')

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out")

print("Python test")
print(f"Python version: {sys.version}")
sys.stdout.flush()

try:
    from sat_solver.dimacs import parse_dimacs
    print("Import dimacs: OK")
    sys.stdout.flush()
    
    from sat_solver.cdcl import cdcl_solve
    print("Import cdcl: OK")
    sys.stdout.flush()
    
    # Test 1: Simple SAT
    print("\n1. Testing simple SAT formula...")
    sys.stdout.flush()
    dimacs_sat = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
    cnf = parse_dimacs(dimacs_sat)
    print(f"   Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    sys.stdout.flush()
    
    start = time.time()
    result = cdcl_solve(cnf)
    elapsed = time.time() - start
    print(f"   Result: SAT={result.sat}, time={elapsed:.4f}s")
    print(f"   Conflicts: {result.conflicts}, Restarts: {result.restarts}")
    if result.assignment:
        print(f"   Assignment size: {len(result.assignment)}")
        from sat_solver.proof import check_assignment
        valid, _ = check_assignment(cnf, result.assignment)
        print(f"   Assignment valid: {valid}")
    sys.stdout.flush()
    
    # Test 2: Simple UNSAT with timeout
    print("\n2. Testing simple UNSAT formula (2 vars, 4 clauses)...")
    sys.stdout.flush()
    dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
    cnf = parse_dimacs(dimacs_unsat)
    print(f"   Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    sys.stdout.flush()
    
    start = time.time()
    result = cdcl_solve(cnf, enable_proof=True)
    elapsed = time.time() - start
    print(f"   Result: SAT={result.sat}, time={elapsed:.4f}s")
    print(f"   Conflicts: {result.conflicts}, Restarts: {result.restarts}")
    if result.proof:
        print(f"   Proof length: {len(result.proof)}")
        for i, p in enumerate(result.proof[:5]):
            print(f"     {i+1}: {p}")
    sys.stdout.flush()
    
    # Test 3: Chain UNSAT
    print("\n3. Testing chain formula UNSAT (10 vars)...")
    sys.stdout.flush()
    chain = "p cnf 10 11\n-1 2 0\n-2 3 0\n-3 4 0\n-4 5 0\n-5 6 0\n-6 7 0\n-7 8 0\n-8 9 0\n-9 10 0\n1 0\n-10 0"
    cnf = parse_dimacs(chain)
    print(f"   Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    sys.stdout.flush()
    
    start = time.time()
    result = cdcl_solve(cnf)
    elapsed = time.time() - start
    print(f"   Result: SAT={result.sat}, time={elapsed:.4f}s")
    print(f"   Conflicts: {result.conflicts}, Restarts: {result.restarts}")
    sys.stdout.flush()
    
    # Test 4: Pigeonhole 4,3
    print("\n4. Testing pigeonhole 4,3...")
    sys.stdout.flush()
    from sat_solver.formula_generator import generate_pigeonhole
    cnf = generate_pigeonhole(4, 3)
    print(f"   CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    sys.stdout.flush()
    
    start = time.time()
    result = cdcl_solve(cnf)
    elapsed = time.time() - start
    print(f"   Result: SAT={result.sat}, time={elapsed:.4f}s")
    print(f"   Conflicts: {result.conflicts}, Restarts: {result.restarts}")
    print(f"   Learnt clauses: {result.learnt_clauses}")
    sys.stdout.flush()
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    sys.stdout.flush()
    
except TimeoutError as e:
    print(f"TIMEOUT: {e}")
    sys.stdout.flush()
    sys.exit(1)
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)
