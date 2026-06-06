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
import time

def log(s):
    print(s)
    with open("test_user_bugs_output.txt", "a") as f:
        f.write(s + "\n")

log("=" * 70)
log("TESTING USER-REPORTED BUGS")
log("=" * 70)

log("\n" + "=" * 70)
log("BUG 1: 2-Variable Contradictory Instance (expected 4, got 0)")
log("=" * 70)

clauses_2var = [
    (100, [1, 2]),
    (100, [-1, -2]),
    (1, [1]),
    (3, [2]),
    (1, [-1]),
    (3, [-2]),
]
wcnf_2var = WCNF(num_vars=2, num_clauses=6, top=100, clauses=clauses_2var, comments=[])

log("\nWCNF Instance:")
for i, (w, lits) in enumerate(wcnf_2var.clauses):
    hard = "HARD" if w >= wcnf_2var.top else "soft"
    log(f"  [{i}] {hard} w={w}: {lits}")

log("\nBrute Force:")
bf_w, bf_a, bf_u = brute_force_maxsat(wcnf_2var)
log(f"  weight={bf_w}, assign={bf_a}, unsat={bf_u}")
log(f"  NOTE: User said expected=4")

log("\nOLL MaxSAT:")
t0 = time.time()
oll = oll_maxsat_solve(wcnf_2var, max_time=10.0)
log(f"  optimal_weight={oll.optimal_weight}")
log(f"  status={oll.status}")
log(f"  time={time.time()-t0:.4f}s")
log(f"  cores_found={oll.cores_found}")
log(f"  iterations={oll.iterations}")
log(f"  assignment={oll.assignment}")
log(f"  unsatisfied_soft_indices={oll.unsatisfied_soft_indices}")

if oll.optimal_weight == bf_w:
    log(f"  OK: OLL matches brute force! OLL={oll.optimal_weight}, BF={bf_w}")
else:
    log(f"  FAIL: OLL={oll.optimal_weight}, BF={bf_w}")

log("\n" + "=" * 70)
log("BUG 2: Hard+Soft Mixed Instance (expected 7, got 0)")
log("=" * 70)

clauses_hs = [
    (100, [1, 2]),
    (100, [2, 3]),
    (100, [-1, -3]),
    (3, [1]),
    (4, [2]),
    (3, [3]),
]
wcnf_hs = WCNF(num_vars=3, num_clauses=6, top=100, clauses=clauses_hs, comments=[])

log("\nWCNF Instance:")
for i, (w, lits) in enumerate(wcnf_hs.clauses):
    hard = "HARD" if w >= wcnf_hs.top else "soft"
    log(f"  [{i}] {hard} w={w}: {lits}")

log("\nBrute Force:")
bf_w2, bf_a2, bf_u2 = brute_force_maxsat(wcnf_hs)
log(f"  weight={bf_w2}, assign={bf_a2}, unsat={bf_u2}")
log(f"  NOTE: User said expected=7")

log("\nOLL MaxSAT:")
t0 = time.time()
oll2 = oll_maxsat_solve(wcnf_hs, max_time=10.0)
log(f"  optimal_weight={oll2.optimal_weight}")
log(f"  status={oll2.status}")
log(f"  time={time.time()-t0:.4f}s")
log(f"  cores_found={oll2.cores_found}")
log(f"  iterations={oll2.iterations}")
log(f"  assignment={oll2.assignment}")
log(f"  unsatisfied_soft_indices={oll2.unsatisfied_soft_indices}")

if oll2.optimal_weight == bf_w2:
    log(f"  OK: OLL matches brute force! OLL={oll2.optimal_weight}, BF={bf_w2}")
else:
    log(f"  FAIL: OLL={oll2.optimal_weight}, BF={bf_w2}")

log("\n" + "=" * 70)
log("BUG 3: 6-Node Weighted Vertex Cover (empty cover violates hard constraints)")
log("=" * 70)

graph6 = WeightedGraph(
    num_vertices=6,
    edges=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (4, 6), (5, 6)],
    vertex_weights={1: 10, 2: 20, 3: 30, 4: 15, 5: 25, 6: 35},
)
wcnf_vc6 = encode_weighted_vertex_cover(graph6)

log("\nGraph:")
log(f"  vertices: 1-6")
log(f"  edges: {graph6.edges}")
log(f"  weights: {graph6.vertex_weights}")

log("\nBrute Force Vertex Cover:")
bf_cover, bf_weight_vc = brute_force_min_vertex_cover(graph6)
log(f"  Cover={sorted(bf_cover)}, weight={bf_weight_vc}")
log(f"  Valid: {is_valid_vertex_cover(bf_cover, graph6)}")

log("\nBrute Force MaxSAT:")
bf_w3, bf_a3, bf_u3 = brute_force_maxsat(wcnf_vc6)
log(f"  Satisfied weight={bf_w3}")
log(f"  Assignment={bf_a3}")
log(f"  Unsatisfied soft={bf_u3}")
cover_bf, weight_bf = decode_vertex_cover(bf_a3, graph6)
log(f"  Decoded cover={sorted(cover_bf)}, weight={weight_bf}")
log(f"  Valid: {is_valid_vertex_cover(cover_bf, graph6)}")

log("\nOLL MaxSAT:")
t0 = time.time()
oll3 = oll_maxsat_solve(wcnf_vc6, max_time=30.0)
log(f"  Satisfied weight={oll3.optimal_weight}")
log(f"  Status={oll3.status}")
log(f"  Time={time.time()-t0:.4f}s")
log(f"  Cores={oll3.cores_found}, iterations={oll3.iterations}")
log(f"  Assignment={oll3.assignment}")
log(f"  Unsatisfied soft={oll3.unsatisfied_soft_indices}")

valid = False
cover_oll = []
weight_oll = 0
if oll3.assignment:
    cover_oll, weight_oll = decode_vertex_cover(oll3.assignment, graph6)
    valid = is_valid_vertex_cover(cover_oll, graph6)
    log(f"  Decoded cover={sorted(cover_oll)}, weight={weight_oll}")
    log(f"  Valid: {valid}")
else:
    log("  FAIL: No assignment returned!")

if oll3.optimal_weight == bf_w3 and valid:
    log(f"  OK: OLL matches brute force! OLL={oll3.optimal_weight}, BF={bf_w3}")
else:
    log(f"  FAIL: OLL={oll3.optimal_weight}, BF={bf_w3}, valid={valid}")

log("\n" + "=" * 70)
log("BUG 4: Original 2-Var Instance from minimal_debug.py (expected 20)")
log("=" * 70)

clauses_orig = [
    (100, [1, 2]),
    (100, [-1, -2]),
    (10, [1]),
    (20, [2]),
]
wcnf_orig = WCNF(num_vars=2, num_clauses=4, top=100, clauses=clauses_orig, comments=[])

log("\nBrute Force:")
bf_w4, bf_a4, bf_u4 = brute_force_maxsat(wcnf_orig)
log(f"  weight={bf_w4}, assign={bf_a4}, unsat={bf_u4}")

log("\nOLL MaxSAT:")
t0 = time.time()
oll4 = oll_maxsat_solve(wcnf_orig, max_time=10.0)
log(f"  optimal_weight={oll4.optimal_weight}")
log(f"  status={oll4.status}")
log(f"  time={time.time()-t0:.4f}s")
log(f"  cores_found={oll4.cores_found}")
log(f"  iterations={oll4.iterations}")
log(f"  assignment={oll4.assignment}")

if oll4.optimal_weight == bf_w4:
    log(f"  OK: OLL matches brute force! OLL={oll4.optimal_weight}, BF={bf_w4}")
else:
    log(f"  FAIL: OLL={oll4.optimal_weight}, BF={bf_w4}")

log("\n" + "=" * 70)
log("BUG 5: 4-Node Vertex Cover from debug_vc.py (expected 30)")
log("=" * 70)

graph4 = WeightedGraph(
    num_vertices=4,
    edges=[(1, 2), (1, 3), (2, 3), (3, 4)],
    vertex_weights={1: 5, 2: 10, 3: 15, 4: 20},
)
wcnf_vc4 = encode_weighted_vertex_cover(graph4)

log("\nBrute Force:")
bf_w5, bf_a5, bf_u5 = brute_force_maxsat(wcnf_vc4)
log(f"  Satisfied weight={bf_w5}")

log("\nOLL MaxSAT:")
t0 = time.time()
oll5 = oll_maxsat_solve(wcnf_vc4, max_time=10.0)
log(f"  Satisfied weight={oll5.optimal_weight}")
log(f"  Status={oll5.status}")
log(f"  Time={time.time()-t0:.4f}s")
log(f"  Cores={oll5.cores_found}, iterations={oll5.iterations}")

if oll5.optimal_weight == bf_w5:
    log(f"  OK: OLL matches brute force! OLL={oll5.optimal_weight}, BF={bf_w5}")
else:
    log(f"  FAIL: OLL={oll5.optimal_weight}, BF={bf_w5}")

log("\n" + "=" * 70)
log("SUMMARY")
log("=" * 70)
all_pass = (oll.optimal_weight == bf_w and 
            oll2.optimal_weight == bf_w2 and 
            oll3.optimal_weight == bf_w3 and valid and
            oll4.optimal_weight == bf_w4 and
            oll5.optimal_weight == bf_w5)
log(f"All tests passed: {all_pass}")
if not all_pass:
    log("Some tests FAILED!")
    sys.exit(1)
else:
    log("All tests PASSED!")
    sys.exit(0)
