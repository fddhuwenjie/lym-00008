import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import WCNF
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat, AssumptionCDCLSolver

with open("minimal_debug_output.txt", "w") as f:
    def log(s):
        f.write(s + "\n")
        print(s)

    log("="*60)
    log("MINIMAL DEBUG: 2-VAR CONTRADICTORY INSTANCE")
    log("="*60)

    weighted_clauses = [
        (100, [1, 2]),
        (100, [-1, -2]),
        (10, [1]),
        (20, [2]),
    ]
    wcnf = WCNF(num_vars=2, num_clauses=4, top=100, clauses=weighted_clauses, comments=[])
    
    log("\nWCNF:")
    log(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}, top={wcnf.top}")
    for i, (w, lits) in enumerate(wcnf.clauses):
        hard = "HARD" if w >= wcnf.top else "soft"
        log(f"  [{i}] {hard} w={w}: {lits}")

    log("\nBrute force:")
    bf_w, bf_a, bf_u = brute_force_maxsat(wcnf)
    log(f"  weight={bf_w}, assign={bf_a}, unsat={bf_u}")

    log("\nConvert to CNF with assumptions:")
    cnf, assumptions, soft_indices = wcnf.to_cnf_with_assumptions()
    log(f"  CNF vars={cnf.num_vars}, clauses={cnf.num_clauses}")
    log(f"  assumptions={assumptions}")
    log(f"  soft_indices={soft_indices}")
    for i, c in enumerate(cnf.clauses):
        log(f"    [{i}] {c}")

    log("\nFirst assumption-based solve:")
    solver = AssumptionCDCLSolver(cnf, assumptions)
    result, core = solver.solve_with_assumptions(max_time=5.0)
    log(f"  sat={result.sat}")
    log(f"  core={core}")
    if result.assignment:
        log(f"  assignment={result.assignment}")

    log("\nOLL MaxSAT full solve:")
    import time
    t0 = time.time()
    oll = oll_maxsat_solve(wcnf, max_time=10.0)
    log(f"  optimal_weight={oll.optimal_weight}")
    log(f"  status={oll.status}")
    log(f"  time={time.time()-t0:.4f}s")
    log(f"  cores_found={oll.cores_found}")
    log(f"  iterations={oll.iterations}")
    log(f"  assignment={oll.assignment}")
    log(f"  unsatisfied_soft_indices={oll.unsatisfied_soft_indices}")
