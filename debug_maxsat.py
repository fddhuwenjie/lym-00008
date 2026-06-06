import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import WCNF, parse_wcnf
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat, maxsat_solve_from_clauses, AssumptionCDCLSolver
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)
from sat_solver.cdcl import CDCLResult
from app import create_test_instances
import time

print("="*70)
print("DEBUG: MAXSAT BUG REPRODUCTION")
print("="*70)

def debug_print_wcnf(wcnf, label):
    print(f"\n{label}")
    print(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}, top={wcnf.top}")
    for i, (w, lits) in enumerate(wcnf.clauses):
        hard_str = "HARD" if w >= wcnf.top else f"soft(w={w})"
        print(f"  [{i}] {hard_str}: {lits}")

print("\n1. Testing contradictory 2-var instance")
print("-"*70)

print("\n--- DEBUG: Testing contradictory 2-var hard constraints")
weighted_clauses = [
    (100, [1, 2]),
    (100, [-1, -2]),
    (10, [1]),
    (20, [2]),
]
wcnf_2var = WCNF(num_vars=2, num_clauses=4, top=100, clauses=weighted_clauses, comments=[])
debug_print_wcnf(wcnf_2var, "2-var contradictory")
print("\nBrute force:")
bf_weight, bf_assign, bf_unsat = brute_force_maxsat(wcnf_2var)
print(f"  BF weight={bf_weight}, assign={bf_assign}, unsat={bf_unsat}")

print("\nOLL MaxSAT:")
import time
t0 = time.time()
oll_result = oll_maxsat_solve(wcnf_2var, max_time=10.0)
print(f"  OLL weight={oll_result.optimal_weight}, status={oll_result.status}")
print(f"  Time: {time.time()-t0:.4f}s")
print(f"  Cores: {oll_result.cores_found}, iterations: {oll_result.iterations}")
print(f"  Assign: {oll_result.assignment}")
print(f"  Unsat soft indices: {oll_result.unsatisfied_soft_indices}")

print("\n--- DEBUG: Detailed OLL step by step")
print("\n2. Testing step 1: convert to CNF with assumptions")
cnf, assumptions, soft_indices = wcnf_2var.to_cnf_with_assumptions()
print(f"  CNF: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
print(f"  Assumptions: {assumptions}")
print(f"  Soft indices: {soft_indices}")
for i, c in enumerate(cnf.clauses):
    print(f"    [{i}] {c}")

print("\n3. Testing assumption-based solving")
solver = AssumptionCDCLSolver(cnf, assumptions)
result, core = solver.solve_with_assumptions(max_time=5.0)
print(f"  Result sat={result.sat}")
print(f"  Core: {core}")
if result.assignment:
    print(f"  Assignment: {result.assignment}")

print("\n4. Testing vertex cover 6-node")
print("-"*70)
graph = WeightedGraph(
    num_vertices=6,
    edges=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (4, 6), (5, 6)],
    vertex_weights={1: 10, 2: 20, 3: 30, 4: 15, 5: 25, 6: 35},
)
wcnf_vc = encode_weighted_vertex_cover(graph)
debug_print_wcnf(wcnf_vc, "Vertex Cover WCNF")

print("\nBrute force vertex cover:")
bf_cover, bf_weight_vc = brute_force_min_vertex_cover(graph)
print(f"  BF cover={sorted(bf_cover)}, weight={bf_weight_vc}")

print("\nBrute force MaxSAT on WCNF:")
bf_weight2, bf_assign2, bf_unsat2 = brute_force_maxsat(wcnf_vc)
print(f"  BF weight={bf_weight2}, unsat={bf_unsat2}")
cover, weight = decode_vertex_cover(bf_assign2, graph)
print(f"  Decoded cover={sorted(cover)}, weight={weight}")

print("\nOLL MaxSAT:")
t0 = time.time()
oll_vc = oll_maxsat_solve(wcnf_vc, max_time=10.0)
print(f"  OLL weight={oll_vc.optimal_weight}, status={oll_vc.status}")
print(f"  Time: {time.time()-t0:.4f}s")
print(f"  Cores: {oll_vc.cores_found}, iterations: {oll_vc.iterations}")
print(f"  Assign: {oll_vc.assignment}")
print(f"  Unsat soft indices: {oll_vc.unsatisfied_soft_indices}")
if oll_vc.assignment:
    cover2, weight2 = decode_vertex_cover(oll_vc.assignment, graph)
    print(f"  Decoded cover={sorted(cover2)}, weight={weight2}")
    print(f"  Valid: {is_valid_vertex_cover(cover2, graph)}")

print("\n5. Testing hard+soft 10var")
print("-"*70)
instances = create_test_instances()
desc, wcnf_10var = instances["mixed_hard_soft_10var"]
debug_print_wcnf(wcnf_10var, "Hard+Soft 10var")

print("\nBrute force:")
bf_w, bf_a, bf_u = brute_force_maxsat(wcnf_10var)
print(f"  BF weight={bf_w}, unsat={bf_u}")

print("\nOLL MaxSAT:")
t0 = time.time()
oll_10var = oll_maxsat_solve(wcnf_10var, max_time=30.0)
print(f"  OLL weight={oll_10var.optimal_weight}, status={oll_10var.status}")
print(f"  Time: {time.time()-t0:.4f}s")
print(f"  Cores: {oll_10var.cores_found}, iterations: {oll_10var.iterations}")
print(f"  Unsat soft indices: {oll_10var.unsatisfied_soft_indices}")
