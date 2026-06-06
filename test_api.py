import sys
sys.path.insert(0, '.')

import json
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8008"

def make_request(endpoint, data=None, method="POST"):
    url = f"{BASE_URL}{endpoint}"
    
    if data is not None:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method=method)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(url, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
    except Exception as e:
        return {"error": str(e)}

results = []

def log_test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "details": details})
    print(f"[{status}] {name}")
    if details:
        print(f"       {details}")

print("=" * 60)
print("SAT Solver API Verification Tests")
print("=" * 60)
print()

print("1. Testing root endpoint...")
result = make_request("/", method="GET")
if "message" in result:
    log_test("Root endpoint", True, f"Message: {result['message']}")
else:
    log_test("Root endpoint", False, str(result))

print("\n2. Testing DIMACS parse...")
dimacs_str = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
result = make_request("/api/dimacs/parse", {"dimacs": dimacs_str})
if result.get("success") and result["num_vars"] == 3 and result["num_clauses"] == 2:
    log_test("DIMACS parse", True, f"{result['num_vars']} vars, {result['num_clauses']} clauses")
else:
    log_test("DIMACS parse", False, str(result))

print("\n3. Testing DPLL solve (SAT)...")
result = make_request("/api/solve/dpll", {"dimacs": dimacs_str})
if result.get("sat") == True and result.get("assignment_valid") == True:
    log_test("DPLL SAT solve", True, 
             f"Steps: {result['decision_steps']}, Time: {result['time_seconds']:.4f}s")
else:
    log_test("DPLL SAT solve", False, str(result))

print("\n4. Testing CDCL solve (SAT)...")
result = make_request("/api/solve/cdcl", {"dimacs": dimacs_str})
if result.get("sat") == True and result.get("assignment_valid") == True:
    log_test("CDCL SAT solve", True,
             f"Steps: {result['decision_steps']}, Conflicts: {result['conflicts']}, Time: {result['time_seconds']:.4f}s")
else:
    log_test("CDCL SAT solve", False, str(result))

print("\n5. Testing CDCL solve (UNSAT)...")
unsat_dimacs = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
result = make_request("/api/solve/cdcl", {"dimacs": unsat_dimacs, "enable_proof": True})
if result.get("sat") == False:
    proof_len = len(result.get("proof", [])) if result.get("proof") else 0
    log_test("CDCL UNSAT solve", True,
             f"Conflicts: {result['conflicts']}, Proof length: {proof_len}, Time: {result['time_seconds']:.4f}s")
else:
    log_test("CDCL UNSAT solve", False, str(result))

print("\n6. Testing random formula generation...")
result = make_request("/api/generate/random", {
    "num_vars": 50,
    "num_clauses": 200,
    "k": 3,
    "seed": 42,
    "force_sat": True
})
if result.get("num_vars") == 50 and result.get("num_clauses") == 200:
    log_test("Random formula generation", True,
             f"{result['num_vars']} vars, {result['num_clauses']} clauses")
    
    print("   Solving generated formula...")
    solve_result = make_request("/api/solve/cdcl", {"dimacs": result["dimacs"]})
    if solve_result.get("sat") == True and solve_result.get("assignment_valid") == True:
        log_test("  Solve generated SAT", True,
                 f"Time: {solve_result['time_seconds']:.4f}s")
    else:
        log_test("  Solve generated SAT", False, str(solve_result))
else:
    log_test("Random formula generation", False, str(result))

print("\n7. Testing pigeonhole formula generation...")
result = make_request("/api/generate/pigeonhole", {
    "num_pigeons": 4,
    "num_holes": 3
})
if result.get("num_vars") == 12:
    log_test("Pigeonhole formula generation", True,
             f"{result['num_vars']} vars, {result['num_clauses']} clauses")
    
    print("   Solving pigeonhole formula (should be UNSAT)...")
    solve_result = make_request("/api/solve/cdcl", {"dimacs": result["dimacs"]})
    if solve_result.get("sat") == False:
        log_test("  Solve pigeonhole UNSAT", True,
                 f"Time: {solve_result['time_seconds']:.4f}s, Conflicts: {solve_result['conflicts']}")
    else:
        log_test("  Solve pigeonhole UNSAT", False, str(solve_result))
else:
    log_test("Pigeonhole formula generation", False, str(result))

print("\n8. Testing 100-var 3-SAT performance...")
result = make_request("/api/generate/random", {
    "num_vars": 100,
    "num_clauses": 427,
    "k": 3,
    "seed": 123,
    "force_sat": True
})
if result.get("num_vars") == 100:
    print("   Solving 100-var 3-SAT...")
    solve_result = make_request("/api/solve/cdcl", {"dimacs": result["dimacs"]})
    time_taken = solve_result.get("time_seconds", 999)
    if solve_result.get("sat") == True and time_taken < 10:
        log_test("100-var 3-SAT performance", True,
                 f"Time: {time_taken:.4f}s (< 10s required), Conflicts: {solve_result.get('conflicts')}")
    else:
        log_test("100-var 3-SAT performance", False,
                 f"Time: {time_taken:.4f}s, SAT: {solve_result.get('sat')}")
else:
    log_test("100-var 3-SAT generation", False, str(result))

print("\n9. Testing Sudoku solve...")
puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
result = make_request("/api/sudoku/solve", {
    "puzzle": puzzle,
    "size": 9,
    "solver": "cdcl"
})
if result.get("sat") == True and result.get("solution"):
    log_test("Sudoku solve", True,
             f"Time: {result['time_seconds']:.4f}s, Solution: {result['solution'][:20]}...")
else:
    log_test("Sudoku solve", False, str(result))

print("\n10. Testing benchmark cases...")
result = make_request("/api/benchmarks/cases", method="GET")
if isinstance(result, list) and len(result) >= 5:
    log_test("Benchmark cases", True, f"{len(result)} cases available")
    
    print("   Running easy benchmark case...")
    sat_dimacs = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
    solve_result = make_request("/api/solve/cdcl", {"dimacs": sat_dimacs})
    if solve_result.get("sat") == True:
        log_test("  Easy benchmark", True,
                 f"SAT: {solve_result['sat']}, Time: {solve_result['time_seconds']:.4f}s")
    else:
        log_test("  Easy benchmark", False, str(solve_result))
else:
    log_test("Benchmark cases", False, str(result))

print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)

passed = sum(1 for r in results if r["status"] == "PASS")
total = len(results)
print(f"Passed: {passed}/{total}")

for r in results:
    if r["status"] == "FAIL":
        print(f"  FAILED: {r['name']} - {r['details']}")

if passed == total:
    print("\nAll tests passed!")
else:
    print(f"\n{total - passed} test(s) failed!")

with open("api_test_results.txt", "w", encoding="utf-8") as f:
    f.write(f"SAT Solver API Test Results\n")
    f.write(f"{'=' * 60}\n\n")
    for r in results:
        f.write(f"[{r['status']}] {r['name']}\n")
        if r['details']:
            f.write(f"       {r['details']}\n")
    f.write(f"\nPassed: {passed}/{total}\n")
