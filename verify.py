import sys
sys.path.insert(0, '.')

from sat_solver import parse_dimacs, cdcl_solve, check_assignment

with open("verification_result.txt", "w") as f:
    f.write("Testing SAT Solver...\n")
    
    dimacs_sat = """p cnf 3 2
1 2 3 0
-1 -2 0
"""
    cnf = parse_dimacs(dimacs_sat)
    f.write(f"Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses\n")
    
    result = cdcl_solve(cnf)
    f.write(f"SAT result: {result.sat}\n")
    f.write(f"Time: {result.time_seconds:.4f}s\n")
    
    if result.sat and result.assignment:
        valid, _ = check_assignment(cnf, result.assignment)
        f.write(f"Assignment valid: {valid}\n")
        f.write(f"Assignment: {result.assignment}\n")
    
    dimacs_unsat = """p cnf 2 4
1 2 0
1 -2 0
-1 2 0
-1 -2 0
"""
    cnf2 = parse_dimacs(dimacs_unsat)
    result2 = cdcl_solve(cnf2)
    f.write(f"\nUNSAT result: {result2.sat}\n")
    f.write(f"Time: {result2.time_seconds:.4f}s\n")
    
    f.write("\nAll tests completed!\n")
