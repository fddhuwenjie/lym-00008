import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import WCNF, parse_wcnf
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat, maxsat_solve_from_clauses
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)
from app import create_test_instances
import time
import os

print("\n" + "="*70)
print("COMPREHENSIVE MAXSAT FUNCTIONALITY TEST")
print("="*70)

all_passed = True

print("\n1. Testing WCNF Parsing and Serialization")
print("-" * 70)
wcnf_text = """c test wcnf
p wcnf 3 4 100
100 1 2 0
100 -2 3 0
5 1 0
10 -3 0
"""
wcnf = parse_wcnf(wcnf_text)
assert wcnf.num_vars == 3
assert wcnf.num_clauses == 4
assert wcnf.top == 100
assert wcnf.is_hard(0) == True
assert wcnf.is_hard(2) == False
print(f"  OK: Parsed WCNF: {wcnf.num_vars} vars, {wcnf.num_clauses} clauses, top={wcnf.top}")

serialized = wcnf.to_wcnf()
wcnf2 = parse_wcnf(serialized)
assert wcnf2.num_vars == wcnf.num_vars
assert wcnf2.num_clauses == wcnf.num_clauses
assert wcnf2.top == wcnf.top
print(f"  OK: Serialization roundtrip works")

print("\n2. Testing WCNF to CNF with Assumptions")
print("-" * 70)
cnf, assumptions, soft_indices = wcnf.to_cnf_with_assumptions()
print(f"  Original: {wcnf.num_vars} vars, {wcnf.num_clauses} clauses")
print(f"  With assumptions: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
print(f"  Assumption vars: {assumptions}")
print(f"  Soft indices: {soft_indices}")
assert len(assumptions) == 2
assert cnf.num_vars == 5
print(f"  OK: WCNF to CNF conversion works")

print("\n3. Testing Vertex Cover Encoding/Decoding")
print("-" * 70)
graph = WeightedGraph(
    num_vertices=4,
    edges=[(1, 2), (1, 3), (2, 3), (3, 4)],
    vertex_weights={1: 5, 2: 10, 3: 15, 4: 20},
)
wcnf_vc = encode_weighted_vertex_cover(graph)
print(f"  Encoded: {wcnf_vc.num_vars} vars, {wcnf_vc.num_clauses} clauses")
print(f"    Hard (edges): {len([c for c in wcnf_vc.clauses if c[0] >= wcnf_vc.top])}")
print(f"    Soft (vertices): {len([c for c in wcnf_vc.clauses if c[0] < wcnf_vc.top])}")

bf_cover, bf_weight = brute_force_min_vertex_cover(graph)
print(f"  Brute force: cover={sorted(bf_cover)}, weight={bf_weight}")
assert is_valid_vertex_cover(bf_cover, graph)

result_vc = oll_maxsat_solve(wcnf_vc, max_time=30.0)
print(f"  OLL MaxSAT: optimal_weight={result_vc.optimal_weight}, status={result_vc.status}")
print(f"    Time: {result_vc.time_seconds:.4f}s, cores: {result_vc.cores_found}, iterations: {result_vc.iterations}")

cover, weight = decode_vertex_cover(result_vc.assignment, graph)
print(f"  Decoded: cover={sorted(cover)}, weight={weight}")
assert is_valid_vertex_cover(cover, graph)
assert weight == bf_weight, f"OLL weight {weight} != BF {bf_weight}"
print(f"  OK: Vertex cover matches brute force")

print("\n4. Testing MaxSAT vs Brute Force (all small instances)")
print("-" * 70)
instances = create_test_instances()

for name in ["mixed_hard_soft_10var", "pure_soft_8var", "vertex_cover_6node"]:
    desc, wcnf_inst = instances[name]
    print(f"\n  Instance: {name}")
    print(f"    {desc}")
    print(f"    {wcnf_inst.num_vars} vars, {wcnf_inst.num_clauses} clauses")
    
    bf_weight, bf_assign, bf_unsat = brute_force_maxsat(wcnf_inst)
    print(f"    Brute force: weight={bf_weight}, unsatisfied={bf_unsat}")
    
    t0 = time.time()
    oll_result = oll_maxsat_solve(wcnf_inst, max_time=30.0)
    elapsed = time.time() - t0
    print(f"    OLL: weight={oll_result.optimal_weight}, status={oll_result.status}")
    print(f"      Time: {elapsed:.4f}s, cores: {oll_result.cores_found}, iterations: {oll_result.iterations}")
    print(f"      Unsatisfied: {oll_result.unsatisfied_soft_indices}")
    
    assert oll_result.optimal_weight == bf_weight, \
        f"MISMATCH! OLL={oll_result.optimal_weight}, BF={bf_weight}"
    assert oll_result.unsatisfied_soft_indices == bf_unsat, \
        f"Unsatisfied mismatch! OLL={oll_result.unsatisfied_soft_indices}, BF={bf_unsat}"
    print(f"    OK: Match! OLL = BF = {bf_weight}")

print("\n5. Testing 50-Variable Performance")
print("-" * 70)
name = "mixed_hard_soft_50var"
desc, wcnf_50 = instances[name]
print(f"  Instance: {name}")
print(f"    {desc}")
print(f"    {wcnf_50.num_vars} vars, {wcnf_50.num_clauses} clauses")

t0 = time.time()
result_50 = oll_maxsat_solve(wcnf_50, max_time=30.0)
elapsed = time.time() - t0

print(f"  Result: optimal_weight={result_50.optimal_weight}, status={result_50.status}")
print(f"  Time: {elapsed:.4f}s, cores: {result_50.cores_found}, iterations: {result_50.iterations}")
print(f"  Unsatisfied soft indices: {result_50.unsatisfied_soft_indices}")

assert result_50.status == "optimal" or result_50.status == "optimal_fallback", f"Not optimal: {result_50.status}"
assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s > 5s"
print(f"  OK: Performance OK - {elapsed:.4f}s < 5s")

print("\n6. Testing Weighted Clauses API")
print("-" * 70)
weighted_clauses = [
    (100, [1, 2]),
    (100, [-1, -2]),
    (10, [1]),
    (20, [2]),
]
result_clauses = maxsat_solve_from_clauses(weighted_clauses, num_vars=2, top=100, max_time=10.0)
print(f"  From weighted clauses: optimal_weight={result_clauses.optimal_weight}")
print(f"  Assignment: {result_clauses.assignment}")
print(f"  Unsatisfied: {result_clauses.unsatisfied_soft_indices}")
assert result_clauses.status == "optimal" or result_clauses.status == "optimal_fallback"
assert result_clauses.optimal_weight == 20
print(f"  OK: Weighted clauses API works")

print("\n7. Saving Test Instance Files")
print("-" * 70)
os.makedirs("test_instances", exist_ok=True)
for name, (desc, wcnf_inst) in instances.items():
    filepath = f"test_instances/{name}.wcnf"
    with open(filepath, "w") as f:
        f.write(wcnf_inst.to_wcnf())
    print(f"  Saved: {filepath}")

print("\n" + "="*70)
print("ALL TESTS PASSED!")
print("="*70)

print("\nSummary of Test Instances:")
print("-" * 70)
for name, (desc, wcnf_inst) in instances.items():
    print(f"  {name:30s}: {wcnf_inst.num_vars:3d} vars, {wcnf_inst.num_clauses:4d} clauses - {desc}")

print("\nAPI Endpoints Available:")
print("-" * 70)
print("  POST /api/wcnf/parse          - Parse WCNF text")
print("  POST /api/maxsat/solve         - Solve MaxSAT (WCNF or weighted clauses)")
print("  POST /api/maxsat/verify        - Compare OLL vs brute force")
print("  GET  /api/maxsat/test-instances - Get test instances")
print("  POST /api/vertexcover/encode   - Encode graph to WCNF")
print("  POST /api/vertexcover/solve    - Solve vertex cover end-to-end")
print("\nServer command: py app.py (runs on port 8008)")
print("\nTo test with curl:")
print('  curl -X POST http://localhost:8008/api/maxsat/solve ^')
print('    -H "Content-Type: application/json" ^')
print('    -d "{\"wcnf\": \"$(cat test_instances/mixed_hard_soft_10var.wcnf)\"}"')
