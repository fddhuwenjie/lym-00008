import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import WCNF
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)

graph = WeightedGraph(
    num_vertices=4,
    edges=[(1, 2), (1, 3), (2, 3), (3, 4)],
    vertex_weights={1: 5, 2: 10, 3: 15, 4: 20},
)
wcnf = encode_weighted_vertex_cover(graph)

print("Vertex Cover WCNF:")
print(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}, top={wcnf.top}")
for i, (w, lits) in enumerate(wcnf.clauses):
    hard = "HARD" if w >= wcnf.top else "soft"
    print(f"  [{i}] {hard} w={w}: {lits}")

print("\nBrute force vertex cover:")
bf_cover, bf_weight = brute_force_min_vertex_cover(graph)
print(f"  Cover={sorted(bf_cover)}, weight={bf_weight}")
print(f"  Valid: {is_valid_vertex_cover(bf_cover, graph)}")

print("\nBrute force MaxSAT:")
bf_w, bf_a, bf_u = brute_force_maxsat(wcnf)
print(f"  Satisfied weight={bf_w}")
print(f"  Assignment={bf_a}")
print(f"  Unsatisfied soft={bf_u}")
cover, weight = decode_vertex_cover(bf_a, graph)
print(f"  Decoded cover={sorted(cover)}, weight={weight}")
print(f"  Valid: {is_valid_vertex_cover(cover, graph)}")

total_soft = sum(w for w, _ in wcnf.clauses if w < wcnf.top)
print(f"\nTotal soft weight: {total_soft}")
print(f"Optimal satisfied = total - min_cover_weight = {total_soft} - {bf_weight} = {total_soft - bf_weight}")

print("\nOLL MaxSAT:")
import time
t0 = time.time()
oll = oll_maxsat_solve(wcnf, max_time=10.0)
print(f"  Satisfied weight={oll.optimal_weight}")
print(f"  Status={oll.status}")
print(f"  Time={time.time()-t0:.4f}s")
print(f"  Cores={oll.cores_found}, iterations={oll.iterations}")
print(f"  Assignment={oll.assignment}")
print(f"  Unsatisfied soft={oll.unsatisfied_soft_indices}")
if oll.assignment:
    cover2, weight2 = decode_vertex_cover(oll.assignment, graph)
    print(f"  Decoded cover={sorted(cover2)}, weight={weight2}")
    print(f"  Valid: {is_valid_vertex_cover(cover2, graph)}")

print("\nChecking assignment manually:")
if oll.assignment:
    soft_sat = 0
    soft_unsat = []
    hard_ok = True
    for i, (w, lits) in enumerate(wcnf.clauses):
        clause_sat = False
        for lit in lits:
            var = abs(lit)
            val = oll.assignment.get(var, False)
            if (lit > 0) == val:
                clause_sat = True
                break
        if w >= wcnf.top:
            if not clause_sat:
                hard_ok = False
                print(f"  HARD clause [{i}] {lits} NOT satisfied!")
        else:
            if clause_sat:
                soft_sat += w
                print(f"  soft [{i}] {lits} w={w}: SAT (total now {soft_sat})")
            else:
                soft_unsat.append(i)
                print(f"  soft [{i}] {lits} w={w}: UNSAT")
    print(f"\n  Hard clauses OK: {hard_ok}")
    print(f"  Calculated soft weight: {soft_sat}")
    print(f"  Unsatisfied soft: {sorted(soft_unsat)}")
    print(f"  Match: {soft_sat == oll.optimal_weight and sorted(soft_unsat) == oll.unsatisfied_soft_indices}")
