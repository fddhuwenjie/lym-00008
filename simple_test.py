import sys
print("Python test")
print(f"Python version: {sys.version}")
sys.stdout.flush()

import time
time.sleep(1)

try:
    sys.path.insert(0, '.')
    from sat_solver.dimacs import parse_dimacs
    print("Import dimacs: OK")
    sys.stdout.flush()
    
    from sat_solver.cdcl import cdcl_solve
    print("Import cdcl: OK")
    sys.stdout.flush()
    
    # Simple test
    print("\nTesting simple UNSAT...")
    sys.stdout.flush()
    dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
    cnf = parse_dimacs(dimacs_unsat)
    print(f"Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    sys.stdout.flush()
    
    result = cdcl_solve(cnf, enable_proof=True)
    print(f"Result: SAT={result.sat}, time={result.time_seconds:.4f}s")
    sys.stdout.flush()
    
    if result.proof:
        print(f"Proof length: {len(result.proof)}")
        for p in result.proof[:3]:
            print(f"  {p}")
        sys.stdout.flush()
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    sys.stdout.flush()
