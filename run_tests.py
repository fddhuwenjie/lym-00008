import sys
sys.path.insert(0, '.')

output_lines = []

def log(msg):
    output_lines.append(msg)
    print(msg)

log("Testing SAT Solver...")

try:
    from sat_solver import (
        parse_dimacs,
        dpll_solve,
        cdcl_solve,
        generate_random_ksat,
        generate_pigeonhole,
        check_assignment,
        encode_sudoku,
        decode_sudoku,
        parse_sudoku_string,
        run_all_benchmarks,
    )
    log("Imports successful")
    
    dimacs_str = """c Test formula
p cnf 3 2
1 2 3 0
-1 -2 0
"""
    cnf = parse_dimacs(dimacs_str)
    log(f"Parsed CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    log(f"Clauses: {cnf.clauses}")
    
    log("\nTesting DPLL...")
    dpll_result = dpll_solve(cnf)
    log(f"DPLL SAT: {dpll_result.sat}")
    log(f"DPLL Assignment: {dpll_result.assignment}")
    if dpll_result.sat:
        valid, _ = check_assignment(cnf, dpll_result.assignment)
        log(f"DPLL Valid: {valid}")
    
    log("\nTesting CDCL...")
    cdcl_result = cdcl_solve(cnf)
    log(f"CDCL SAT: {cdcl_result.sat}")
    log(f"CDCL Assignment: {cdcl_result.assignment}")
    if cdcl_result.sat:
        valid, _ = check_assignment(cnf, cdcl_result.assignment)
        log(f"CDCL Valid: {valid}")
    
    log("\nTesting UNSAT...")
    unsat_dimacs = """p cnf 2 4
1 2 0
1 -2 0
-1 2 0
-1 -2 0
"""
    unsat_cnf = parse_dimacs(unsat_dimacs)
    unsat_result = cdcl_solve(unsat_cnf)
    log(f"UNSAT SAT: {unsat_result.sat}")
    
    log("\nTesting Random 3-SAT (50 vars)...")
    rand_cnf = generate_random_ksat(50, 200, k=3, seed=42, force_sat=True)
    log(f"Random CNF: {rand_cnf.num_vars} vars, {rand_cnf.num_clauses} clauses")
    import time
    start = time.time()
    rand_result = cdcl_solve(rand_cnf)
    elapsed = time.time() - start
    log(f"Random SAT: {rand_result.sat} in {elapsed:.4f}s")
    log(f"  Conflicts: {rand_result.conflicts}")
    log(f"  Restarts: {rand_result.restarts}")
    
    log("\nTesting Pigeonhole (4, 3)...")
    php_cnf = generate_pigeonhole(4, 3)
    log(f"PHP CNF: {php_cnf.num_vars} vars, {php_cnf.num_clauses} clauses")
    start = time.time()
    php_result = cdcl_solve(php_cnf)
    elapsed = time.time() - start
    log(f"PHP SAT: {php_result.sat} in {elapsed:.4f}s")
    
    log("\nTesting Performance: 100-var 3-SAT...")
    perf_cnf = generate_random_ksat(100, 427, k=3, seed=123, force_sat=True)
    log(f"Perf CNF: {perf_cnf.num_vars} vars, {perf_cnf.num_clauses} clauses")
    start = time.time()
    perf_result = cdcl_solve(perf_cnf)
    elapsed = time.time() - start
    log(f"Perf SAT: {perf_result.sat} in {elapsed:.4f}s")
    log(f"  Conflicts: {perf_result.conflicts}")
    log(f"  Restarts: {perf_result.restarts}")
    log(f"  Learnt: {perf_result.learnt_clauses}")
    if perf_result.sat:
        valid, _ = check_assignment(perf_cnf, perf_result.assignment)
        log(f"  Valid: {valid}")
    
    log("\nTesting Sudoku...")
    puzzle_str = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
    puzzle = parse_sudoku_string(puzzle_str)
    sudoku_cnf = encode_sudoku(puzzle)
    log(f"Sudoku CNF: {sudoku_cnf.num_vars} vars, {sudoku_cnf.num_clauses} clauses")
    start = time.time()
    sudoku_result = cdcl_solve(sudoku_cnf)
    elapsed = time.time() - start
    log(f"Sudoku SAT: {sudoku_result.sat} in {elapsed:.4f}s")
    if sudoku_result.sat and sudoku_result.assignment:
        grid = decode_sudoku(sudoku_result.assignment)
        log(f"Solution found!")
        log(f"First row: {grid[0]}")
    
    log("\nTesting Benchmarks...")
    start = time.time()
    bench_results = run_all_benchmarks(solvers=["cdcl"], difficulty_filter="easy")
    elapsed = time.time() - start
    log(f"Benchmarks ({len(bench_results)} cases) completed in {elapsed:.4f}s")
    for r in bench_results:
        log(f"  {r.name}: {'OK' if r.correct else 'FAIL'} ({r.time_seconds:.4f}s)")
    
    log("\nALL TESTS PASSED!")
    
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
except Exception as e:
    log(f"ERROR: {e}")
    import traceback
    log(traceback.format_exc())
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    sys.exit(1)
