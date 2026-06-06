import sys
sys.path.insert(0, '.')

error_file = open("import_error.txt", "w")

try:
    error_file.write("Importing dimacs...\n")
    error_file.flush()
    from sat_solver import dimacs
    error_file.write("Importing dpll...\n")
    error_file.flush()
    from sat_solver import dpll
    error_file.write("Importing cdcl...\n")
    error_file.flush()
    from sat_solver import cdcl
    error_file.write("Importing formula_generator...\n")
    error_file.flush()
    from sat_solver import formula_generator
    error_file.write("Importing sudoku...\n")
    error_file.flush()
    from sat_solver import sudoku
    error_file.write("Importing proof...\n")
    error_file.flush()
    from sat_solver import proof
    error_file.write("Importing benchmarks...\n")
    error_file.flush()
    from sat_solver import benchmarks
    error_file.write("All imports successful!\n")
    error_file.flush()
    
    error_file.write("\nTesting simple parse...\n")
    error_file.flush()
    from sat_solver import parse_dimacs
    dimacs_str = """p cnf 3 2
1 2 3 0
-1 -2 0
"""
    cnf = parse_dimacs(dimacs_str)
    error_file.write(f"Parsed: {cnf.num_vars} vars, {cnf.num_clauses} clauses\n")
    error_file.flush()
    
    error_file.write("\nTesting DPLL...\n")
    error_file.flush()
    from sat_solver import dpll_solve
    result = dpll_solve(cnf)
    error_file.write(f"DPLL SAT: {result.sat}\n")
    error_file.flush()
    
    error_file.write("\nTesting CDCL...\n")
    error_file.flush()
    from sat_solver import cdcl_solve
    result2 = cdcl_solve(cnf)
    error_file.write(f"CDCL SAT: {result2.sat}\n")
    error_file.write(f"CDCL Time: {result2.time_seconds:.4f}s\n")
    error_file.flush()
    
    if result2.sat and result2.assignment:
        from sat_solver import check_assignment
        valid, _ = check_assignment(cnf, result2.assignment)
        error_file.write(f"Assignment valid: {valid}\n")
        error_file.flush()
    
    error_file.write("\nTesting UNSAT...\n")
    error_file.flush()
    unsat_dimacs = """p cnf 2 4
1 2 0
1 -2 0
-1 2 0
-1 -2 0
"""
    cnf2 = parse_dimacs(unsat_dimacs)
    result3 = cdcl_solve(cnf2)
    error_file.write(f"UNSAT result: {result3.sat}\n")
    error_file.write(f"UNSAT Time: {result3.time_seconds:.4f}s\n")
    error_file.flush()
    
    error_file.write("\nTesting formula generation...\n")
    error_file.flush()
    from sat_solver import generate_random_ksat
    cnf3 = generate_random_ksat(20, 80, k=3, seed=42)
    error_file.write(f"Generated: {cnf3.num_vars} vars, {cnf3.num_clauses} clauses\n")
    result4 = cdcl_solve(cnf3)
    error_file.write(f"Solve result: {result4.sat} in {result4.time_seconds:.4f}s\n")
    error_file.flush()
    
    error_file.write("\nAll tests passed!\n")
    error_file.flush()
    
except Exception as e:
    error_file.write(f"ERROR: {e}\n")
    import traceback
    traceback.print_exc(file=error_file)
    error_file.flush()
finally:
    error_file.close()
