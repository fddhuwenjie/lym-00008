import sys
sys.path.insert(0, '.')

from sat_solver.dimacs import WCNF, parse_wcnf, parse_wcnf_file
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat, maxsat_solve_from_wcnf
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)
from app import create_test_instances
import os


def save_test_instances():
    instances = create_test_instances()
    os.makedirs("test_instances", exist_ok=True)

    for name, (desc, wcnf) in instances.items():
        filepath = f"test_instances/{name}.wcnf"
        with open(filepath, "w") as f:
            f.write(wcnf.to_wcnf())
        print(f"Saved {name}: {desc} -> {filepath}")
        print(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}, top={wcnf.top}")
        print()

    return instances


def test_wcnf_parsing():
    print("=" * 60)
    print("TEST 1: WCNF Parsing")
    print("=" * 60)

    wcnf_text = """c test wcnf
p wcnf 3 4 100
100 1 2 0
100 -2 3 0
5 1 0
10 -3 0
"""
    wcnf = parse_wcnf(wcnf_text)
    print(f"Parsed: num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}, top={wcnf.top}")
    print(f"Clauses: {wcnf.clauses}")
    assert wcnf.num_vars == 3
    assert wcnf.num_clauses == 4
    assert wcnf.top == 100
    assert wcnf.is_hard(0) == True
    assert wcnf.is_hard(2) == False
    print("OK: WCNF parsing works correctly")
    print()


def test_vertex_cover_encoding():
    print("=" * 60)
    print("TEST 2: Vertex Cover Encoding/Decoding")
    print("=" * 60)

    graph = WeightedGraph(
        num_vertices=4,
        edges=[(1, 2), (1, 3), (2, 3), (3, 4)],
        vertex_weights={1: 5, 2: 10, 3: 15, 4: 20},
    )
    wcnf = encode_weighted_vertex_cover(graph)
    print(f"Encoded WCNF: {wcnf.num_vars} vars, {wcnf.num_clauses} clauses")
    print(f"  Hard clauses (edges): {len([c for c in wcnf.clauses if c[0] >= wcnf.top])}")
    print(f"  Soft clauses (vertices): {len([c for c in wcnf.clauses if c[0] < wcnf.top])}")

    bf_cover, bf_weight = brute_force_min_vertex_cover(graph)
    print(f"\nBrute force min vertex cover: {sorted(bf_cover)}, weight={bf_weight}")
    assert is_valid_vertex_cover(bf_cover, graph)

    result = oll_maxsat_solve(wcnf, max_time=10.0)
    print(f"OLL MaxSAT result: optimal_weight={result.optimal_weight}, status={result.status}")
    print(f"  Time: {result.time_seconds:.4f}s, cores: {result.cores_found}, iterations: {result.iterations}")

    cover, weight = decode_vertex_cover(result.assignment, graph)
    print(f"Decoded cover: {sorted(cover)}, weight={weight}")
    assert is_valid_vertex_cover(cover, graph)
    assert weight == bf_weight, f"OLL weight {weight} != brute force {bf_weight}"
    print("OK: Vertex cover encoding/decoding works correctly")
    print()


def test_maxsat_small_brute_force():
    print("=" * 60)
    print("TEST 3: MaxSAT vs Brute Force (small instances)")
    print("=" * 60)

    instances = create_test_instances()

    for name in ["mixed_hard_soft_10var", "pure_soft_8var", "vertex_cover_6node"]:
        desc, wcnf = instances[name]
        print(f"\nInstance: {name} - {desc}")
        print(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}")

        bf_weight, bf_assign, bf_unsat = brute_force_maxsat(wcnf)
        print(f"  Brute force: optimal_weight={bf_weight}, unsatisfied={bf_unsat}")

        oll_result = oll_maxsat_solve(wcnf, max_time=30.0)
        print(f"  OLL MaxSAT: optimal_weight={oll_result.optimal_weight}, status={oll_result.status}")
        print(f"    Time: {oll_result.time_seconds:.4f}s, cores: {oll_result.cores_found}, iterations: {oll_result.iterations}")
        print(f"    Unsatisfied soft indices: {oll_result.unsatisfied_soft_indices}")

        assert oll_result.optimal_weight == bf_weight, \
            f"Mismatch! OLL={oll_result.optimal_weight}, BF={bf_weight}"
        assert oll_result.unsatisfied_soft_indices == bf_unsat, \
            f"Unsatisfied mismatch! OLL={oll_result.unsatisfied_soft_indices}, BF={bf_unsat}"
        print(f"  OK: Match! OLL = Brute Force = {bf_weight}")

    print("\nOK: All small instances verified against brute force")
    print()


def test_maxsat_performance():
    print("=" * 60)
    print("TEST 4: Performance Test (50 variables)")
    print("=" * 60)

    instances = create_test_instances()
    name = "mixed_hard_soft_50var"
    desc, wcnf = instances[name]

    print(f"Instance: {name} - {desc}")
    print(f"  num_vars={wcnf.num_vars}, num_clauses={wcnf.num_clauses}")

    import time
    t0 = time.time()
    result = oll_maxsat_solve(wcnf, max_time=30.0)
    elapsed = time.time() - t0

    print(f"  OLL MaxSAT: optimal_weight={result.optimal_weight}, status={result.status}")
    print(f"  Time: {elapsed:.4f}s, cores: {result.cores_found}, iterations: {result.iterations}")
    print(f"  Unsatisfied soft indices: {result.unsatisfied_soft_indices}")

    assert elapsed < 5.0, f"Too slow! {elapsed:.2f}s > 5s"
    assert result.status == "optimal"
    print(f"  OK: Performance OK: {elapsed:.4f}s < 5s")
    print()


def test_to_cnf_with_assumptions():
    print("=" * 60)
    print("TEST 5: WCNF to CNF with Assumptions")
    print("=" * 60)

    wcnf_text = """c test
p wcnf 3 4 100
100 1 2 0
5 1 0
10 2 0
15 3 0
"""
    wcnf = parse_wcnf(wcnf_text)
    cnf, assumptions, soft_indices = wcnf.to_cnf_with_assumptions()

    print(f"Original WCNF: {wcnf.num_vars} vars, {wcnf.num_clauses} clauses")
    print(f"CNF with assumptions: {cnf.num_vars} vars, {cnf.num_clauses} clauses")
    print(f"Assumption vars: {assumptions}")
    print(f"Soft clause indices: {soft_indices}")
    print(f"CNF clauses: {cnf.clauses}")

    assert len(assumptions) == 3
    assert cnf.num_vars == 3 + 3
    print("OK: WCNF to CNF with assumptions works correctly")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MAXSAT TEST SUITE")
    print("=" * 60 + "\n")

    try:
        save_test_instances()
        test_wcnf_parsing()
        test_to_cnf_with_assumptions()
        test_vertex_cover_encoding()
        test_maxsat_small_brute_force()
        test_maxsat_performance()

        print("=" * 60)
        print("ALL TESTS PASSED! OK")
        print("=" * 60)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
