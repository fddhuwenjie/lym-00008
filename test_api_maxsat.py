import sys
sys.path.insert(0, '.')
import requests
import json
import time

base_url = "http://localhost:8008"

def test_endpoint(name, method, path, data=None):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    url = f"{base_url}{path}"
    start = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(url, json=data, timeout=60)
        
        elapsed = time.time() - start
        print(f"HTTP {response.status_code} in {elapsed:.4f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MAXSAT API TEST SUITE")
    print("="*60)

    print("\nChecking server availability...")
    try:
        r = requests.get(f"{base_url}/", timeout=5)
        print(f"Server is up: {r.json()}")
    except:
        print("Server is not responding!")
        sys.exit(1)

    wcnf_text = """c test wcnf
p wcnf 3 4 100
100 1 2 0
100 -2 3 0
5 1 0
10 -3 0
"""
    test_endpoint("WCNF Parse", "POST", "/api/wcnf/parse", {"wcnf": wcnf_text})

    with open("test_instances/mixed_hard_soft_10var.wcnf", "r") as f:
        wcnf_small = f.read()
    result2 = test_endpoint("MaxSAT Solve - Mixed 10var", "POST", "/api/maxsat/solve", 
                           {"wcnf": wcnf_small, "max_time": 30.0})
    if result2:
        print(f"\n  optimal_weight: {result2.get('optimal_weight')}")
        print(f"  time_seconds: {result2.get('time_seconds')}")
        print(f"  status: {result2.get('status')}")
        print(f"  assignment_valid: {result2.get('assignment_valid')}")
        print(f"  brute_force_match: {result2.get('brute_force_match')}")

    with open("test_instances/pure_soft_8var.wcnf", "r") as f:
        wcnf_soft = f.read()
    result3 = test_endpoint("MaxSAT Solve - Pure Soft 8var", "POST", "/api/maxsat/solve",
                           {"wcnf": wcnf_soft, "max_time": 30.0})
    if result3:
        print(f"\n  optimal_weight: {result3.get('optimal_weight')}")
        print(f"  time_seconds: {result3.get('time_seconds')}")
        print(f"  status: {result3.get('status')}")

    with open("test_instances/vertex_cover_6node.wcnf", "r") as f:
        wcnf_vc = f.read()
    result4 = test_endpoint("MaxSAT Solve - Vertex Cover 6node", "POST", "/api/maxsat/solve",
                           {"wcnf": wcnf_vc, "max_time": 30.0})
    if result4:
        print(f"\n  optimal_weight: {result4.get('optimal_weight')}")
        print(f"  time_seconds: {result4.get('time_seconds')}")
        print(f"  status: {result4.get('status')}")

    with open("test_instances/mixed_hard_soft_50var.wcnf", "r") as f:
        wcnf_50 = f.read()
    start_time = time.time()
    result5 = test_endpoint("MaxSAT Solve - Mixed 50var Performance", "POST", "/api/maxsat/solve",
                           {"wcnf": wcnf_50, "max_time": 30.0})
    total_time = time.time() - start_time
    if result5:
        print(f"\n  optimal_weight: {result5.get('optimal_weight')}")
        print(f"  solver_time: {result5.get('time_seconds')}s")
        print(f"  total_time_with_http: {total_time:.4f}s")
        print(f"  status: {result5.get('status')}")
        if result5.get('time_seconds', 100) < 5.0:
            print(f"  PASS: Solver time < 5s")
        else:
            print(f"  FAIL: Solver time > 5s")

    result6 = test_endpoint("Vertex Cover Solve End-to-End", "POST", "/api/vertexcover/solve", {
        "num_vertices": 6,
        "edges": [[1,2], [1,3], [2,3], [2,4], [3,5], [4,5], [4,6], [5,6]],
        "vertex_weights": {"1": 10, "2": 20, "3": 30, "4": 15, "5": 25, "6": 35},
        "max_time": 30.0
    })
    if result6:
        print(f"\n  cover: {result6.get('cover')}")
        print(f"  total_weight: {result6.get('total_weight')}")
        print(f"  valid: {result6.get('valid')}")
        print(f"  brute_force_match: {result6.get('brute_force_match')}")

    result7 = test_endpoint("MaxSAT Verify - Brute Force", "POST", "/api/maxsat/verify",
                           {"wcnf": wcnf_small})
    if result7:
        print(f"\n  oll_optimal_weight: {result7.get('oll_optimal_weight')}")
        print(f"  brute_force_optimal_weight: {result7.get('brute_force_optimal_weight')}")
        print(f"  match: {result7.get('match')}")

    result8 = test_endpoint("MaxSAT from Weighted Clauses", "POST", "/api/maxsat/solve", {
        "weighted_clauses": [
            [100, [1, 2]],
            [100, [-1, -2]],
            [10, [1]],
            [20, [2]]
        ],
        "num_vars": 2,
        "top": 100,
        "max_time": 10.0
    })
    if result8:
        print(f"\n  optimal_weight: {result8.get('optimal_weight')}")
        print(f"  status: {result8.get('status')}")

    result9 = test_endpoint("Get Test Instances", "GET", "/api/maxsat/test-instances")
    if result9:
        print(f"\n  Available instances: {list(result9.keys())}")

    print("\n" + "="*60)
    print("ALL API TESTS COMPLETED")
    print("="*60)
