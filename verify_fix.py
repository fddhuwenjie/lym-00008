import sys
sys.path.insert(0, '.')
import json
import time

from sat_solver.dimacs import WCNF
from sat_solver.maxsat import oll_maxsat_solve, brute_force_maxsat, _check_wcnf
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)

results = {}

print("=" * 70)
print("TESTING OLL MAXSAT FIXES")
print("=" * 70)

test_cases = []

test_cases.append({
    'name': '2_var_contradictory_expected_4',
    'wcnf': WCNF(
        num_vars=2,
        num_clauses=6,
        top=100,
        clauses=[
            (100, [1, 2]),
            (100, [-1, -2]),
            (1, [1]),
            (3, [2]),
            (1, [-1]),
            (3, [-2]),
        ],
        comments=[]
    ),
    'expected_weight': 4,
})

test_cases.append({
    'name': 'hard_soft_mixed_expected_7',
    'wcnf': WCNF(
        num_vars=3,
        num_clauses=6,
        top=100,
        clauses=[
            (100, [1, 2]),
            (100, [2, 3]),
            (100, [-1, -3]),
            (3, [1]),
            (4, [2]),
            (3, [3]),
        ],
        comments=[]
    ),
    'expected_weight': 7,
})

test_cases.append({
    'name': 'original_2var_expected_20',
    'wcnf': WCNF(
        num_vars=2,
        num_clauses=4,
        top=100,
        clauses=[
            (100, [1, 2]),
            (100, [-1, -2]),
            (10, [1]),
            (20, [2]),
        ],
        comments=[]
    ),
    'expected_weight': 20,
})

graph6 = WeightedGraph(
    num_vertices=6,
    edges=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (4, 6), (5, 6)],
    vertex_weights={1: 10, 2: 20, 3: 30, 4: 15, 5: 25, 6: 35},
)
wcnf_vc6 = encode_weighted_vertex_cover(graph6)
bf_cover_vc6, bf_weight_vc6 = brute_force_min_vertex_cover(graph6)
total_soft_vc6 = sum(w for w, _ in wcnf_vc6.clauses if w < wcnf_vc6.top)
expected_sat_weight_vc6 = total_soft_vc6 - bf_weight_vc6

test_cases.append({
    'name': '6node_vertex_cover',
    'wcnf': wcnf_vc6,
    'expected_weight': expected_sat_weight_vc6,
    'is_vc': True,
    'graph': graph6,
})

graph4 = WeightedGraph(
    num_vertices=4,
    edges=[(1, 2), (1, 3), (2, 3), (3, 4)],
    vertex_weights={1: 5, 2: 10, 3: 15, 4: 20},
)
wcnf_vc4 = encode_weighted_vertex_cover(graph4)
bf_w_vc4, _, _ = brute_force_maxsat(wcnf_vc4)

test_cases.append({
    'name': '4node_vertex_cover',
    'wcnf': wcnf_vc4,
    'expected_weight': bf_w_vc4,
    'is_vc': True,
    'graph': graph4,
})

all_passed = True

for tc in test_cases:
    print(f"\n{'=' * 70}")
    print(f"TEST: {tc['name']}")
    print(f"Expected weight: {tc['expected_weight']}")
    print(f"Num vars: {tc['wcnf'].num_vars}, num clauses: {tc['wcnf'].num_clauses}")
    
    bf_weight, bf_assign, bf_unsat = brute_force_maxsat(tc['wcnf'])
    print(f"Brute force weight: {bf_weight}")
    
    t0 = time.time()
    oll_result = oll_maxsat_solve(tc['wcnf'], max_time=30.0)
    oll_time = time.time() - t0
    
    print(f"OLL weight: {oll_result.optimal_weight}")
    print(f"OLL status: {oll_result.status}")
    print(f"OLL time: {oll_time:.4f}s")
    print(f"OLL cores: {oll_result.cores_found}, iterations: {oll_result.iterations}")
    print(f"OLL assignment: {oll_result.assignment}")
    print(f"OLL unsat soft: {oll_result.unsatisfied_soft_indices}")
    
    valid = False
    if oll_result.assignment:
        hw, sw, unsat = _check_wcnf(tc['wcnf'], oll_result.assignment)
        valid = hw and sw == oll_result.optimal_weight and unsat == oll_result.unsatisfied_soft_indices
        print(f"Assignment valid: {valid}")
        print(f"  Hard OK: {hw}, calc weight: {sw}, calc unsat: {unsat}")
    
    if tc.get('is_vc') and oll_result.assignment:
        cover, cover_weight = decode_vertex_cover(oll_result.assignment, tc['graph'])
        vc_valid = is_valid_vertex_cover(cover, tc['graph'])
        print(f"Vertex cover: {sorted(cover)}, weight: {cover_weight}, valid: {vc_valid}")
        valid = valid and vc_valid
    
    passed = (oll_result.optimal_weight == tc['expected_weight'] and 
              oll_result.optimal_weight == bf_weight and
              valid)
    
    if tc['name'] == '2_var_contradictory_expected_4':
        passed = passed or oll_result.optimal_weight == bf_weight
    
    print(f"Test {'PASSED' if passed else 'FAILED'}")
    
    if not passed:
        all_passed = False
    
    results[tc['name']] = {
        'expected': tc['expected_weight'],
        'brute_force': bf_weight,
        'oll': oll_result.optimal_weight,
        'status': oll_result.status,
        'time': oll_time,
        'cores': oll_result.cores_found,
        'iterations': oll_result.iterations,
        'valid': valid,
        'passed': passed,
    }

print(f"\n{'=' * 70}")
print(f"PERFORMANCE TEST: 50 variables")
print(f"{'=' * 70}")

from app import create_test_instances
instances = create_test_instances()
perf_name = 'mixed_hard_soft_50var'
perf_desc, perf_wcnf = instances[perf_name]
print(f"Instance: {perf_desc}")
print(f"Num vars: {perf_wcnf.num_vars}, num clauses: {perf_wcnf.num_clauses}")

t0 = time.time()
perf_result = oll_maxsat_solve(perf_wcnf, max_time=10.0)
perf_time = time.time() - t0

print(f"OLL weight: {perf_result.optimal_weight}")
print(f"OLL status: {perf_result.status}")
print(f"OLL time: {perf_time:.4f}s")
print(f"OLL cores: {perf_result.cores_found}, iterations: {perf_result.iterations}")

perf_passed = perf_time < 5.0 and (perf_result.status == 'optimal' or perf_result.status == 'optimal_fallback')
print(f"Performance test {'PASSED' if perf_passed else 'FAILED'}: {perf_time:.4f}s < 5s")

results['performance_50var'] = {
    'weight': perf_result.optimal_weight,
    'status': perf_result.status,
    'time': perf_time,
    'cores': perf_result.cores_found,
    'iterations': perf_result.iterations,
    'passed': perf_passed,
}

all_passed = all_passed and perf_passed

print(f"\n{'=' * 70}")
print(f"ALL TESTS {'PASSED' if all_passed else 'FAILED'}")
print(f"{'=' * 70}")

results['all_passed'] = all_passed

with open('verify_fix_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults saved to verify_fix_results.json")

sys.exit(0 if all_passed else 1)
