import sys
import json
import urllib.request

BASE_URL = "http://localhost:8008"

results = []

def log(msg):
    print(msg, flush=True)
    results.append(msg)

def test_endpoint(name, endpoint, data, method="POST"):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            response_data = json.loads(resp.read().decode())
            return response_data, None
    except Exception as e:
        return None, str(e)

log("=" * 60)
log("SAT Solver API Comprehensive Tests")
log("=" * 60)

# Test 1: Root endpoint
log("\n1. Testing root endpoint...")
data, err = test_endpoint("root", "/", None, method="GET")
if err is None:
    log(f"   PASS: {data.get('message', 'OK')}")
else:
    log(f"   FAIL: {err}")

# Test 2: DIMACS parse
log("\n2. Testing DIMACS parse...")
dimacs_sat = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
data, err = test_endpoint("parse", "/api/dimacs/parse", {"dimacs": dimacs_sat})
if err is None and data.get("success"):
    log(f"   PASS: {data['num_vars']} vars, {data['num_clauses']} clauses")
else:
    log(f"   FAIL: {err or data}")

# Test 3: DPLL SAT solve
log("\n3. Testing DPLL SAT solve...")
data, err = test_endpoint("dpll", "/api/solve/dpll", {"dimacs": dimacs_sat})
if err is None and data.get("sat") == True and data.get("assignment_valid") == True:
    log(f"   PASS: SAT, steps={data['decision_steps']}, time={data['time_seconds']:.4f}s")
else:
    log(f"   FAIL: {err or data}")

# Test 4: CDCL SAT solve
log("\n4. Testing CDCL SAT solve...")
data, err = test_endpoint("cdcl_sat", "/api/solve/cdcl", {"dimacs": dimacs_sat})
if err is None and data.get("sat") == True and data.get("assignment_valid") == True:
    log(f"   PASS: SAT, steps={data['decision_steps']}, conflicts={data['conflicts']}, time={data['time_seconds']:.4f}s")
else:
    log(f"   FAIL: {err or data}")

# Test 5: CDCL UNSAT solve
log("\n5. Testing CDCL UNSAT solve...")
dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
data, err = test_endpoint("cdcl_unsat", "/api/solve/cdcl", {"dimacs": dimacs_unsat, "enable_proof": True})
if err is None and data.get("sat") == False:
    proof_len = len(data.get("proof", [])) if data.get("proof") else 0
    log(f"   PASS: UNSAT, conflicts={data['conflicts']}, proof_len={proof_len}, time={data['time_seconds']:.4f}s")
else:
    log(f"   FAIL: {err or data}")

# Test 6: Random formula generation
log("\n6. Testing random 3-SAT generation (50 vars)...")
data, err = test_endpoint("gen_random", "/api/generate/random", {
    "num_vars": 50, "num_clauses": 200, "k": 3, "seed": 42, "force_sat": True
})
if err is None and data.get("num_vars") == 50:
    log(f"   PASS: {data['num_vars']} vars, {data['num_clauses']} clauses")
    
    log("   Solving generated formula...")
    solve_data, solve_err = test_endpoint("solve_gen", "/api/solve/cdcl", {"dimacs": data["dimacs"]})
    if solve_err is None and solve_data.get("sat") == True:
        log(f"   PASS: Solved in {solve_data['time_seconds']:.4f}s, conflicts={solve_data['conflicts']}")
    else:
        log(f"   FAIL: {solve_err or solve_data}")
else:
    log(f"   FAIL: {err or data}")

# Test 7: Pigeonhole formula generation
log("\n7. Testing pigeonhole formula generation (4, 3)...")
data, err = test_endpoint("gen_php", "/api/generate/pigeonhole", {"num_pigeons": 4, "num_holes": 3})
if err is None and data.get("num_vars") == 12:
    log(f"   PASS: {data['num_vars']} vars, {data['num_clauses']} clauses")
    
    log("   Solving pigeonhole formula (should be UNSAT)...")
    solve_data, solve_err = test_endpoint("solve_php", "/api/solve/cdcl", {"dimacs": data["dimacs"]})
    if solve_err is None and solve_data.get("sat") == False:
        log(f"   PASS: UNSAT in {solve_data['time_seconds']:.4f}s, conflicts={solve_data['conflicts']}")
    else:
        log(f"   FAIL: {solve_err or solve_data}")
else:
    log(f"   FAIL: {err or data}")

# Test 8: 100-var 3-SAT performance
log("\n8. Testing 100-var 3-SAT performance...")
data, err = test_endpoint("gen_100", "/api/generate/random", {
    "num_vars": 100, "num_clauses": 427, "k": 3, "seed": 123, "force_sat": True
})
if err is None:
    log(f"   Generated: {data['num_vars']} vars, {data['num_clauses']} clauses")
    
    log("   Solving (should be < 10s)...")
    import time
    start = time.time()
    solve_data, solve_err = test_endpoint("solve_100", "/api/solve/cdcl", {"dimacs": data["dimacs"]})
    elapsed = time.time() - start
    
    if solve_err is None and solve_data.get("sat") == True:
        log(f"   SAT in {elapsed:.4f}s")
        log(f"   Conflicts: {solve_data['conflicts']}, Restarts: {solve_data['restarts']}")
        log(f"   Learnt clauses: {solve_data['learnt_clauses']}")
        if elapsed < 10:
            log("   PERFORMANCE PASS (< 10s)")
        else:
            log("   PERFORMANCE WARNING (> 10s)")
    else:
        log(f"   FAIL: {solve_err or solve_data}")
else:
    log(f"   FAIL: {err or data}")

# Test 9: Sudoku solve
log("\n9. Testing Sudoku solve...")
puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
data, err = test_endpoint("sudoku", "/api/sudoku/solve", {
    "puzzle": puzzle, "size": 9, "solver": "cdcl"
})
if err is None and data.get("sat") == True:
    log(f"   PASS: Solved in {data['time_seconds']:.4f}s")
    log(f"   Solution: {data['solution'][:30]}...")
    log(f"   CNF: {data['cnf_vars']} vars, {data['cnf_clauses']} clauses")
else:
    log(f"   FAIL: {err or data}")

# Test 10: Benchmark cases
log("\n10. Testing benchmark cases...")
data, err = test_endpoint("benchmarks", "/api/benchmarks/cases", None, method="GET")
if err is None and isinstance(data, list) and len(data) >= 5:
    log(f"   PASS: {len(data)} benchmark cases available")
    for c in data[:5]:
        log(f"     - {c['name']}: {c['num_vars']} vars, expected={c['expected_sat']}")
else:
    log(f"   FAIL: {err or data}")

# Test 11: Chain formula UNSAT
log("\n11. Testing chain formula UNSAT...")
chain_dimacs = "p cnf 10 11\n-1 2 0\n-2 3 0\n-3 4 0\n-4 5 0\n-5 6 0\n-6 7 0\n-7 8 0\n-8 9 0\n-9 10 0\n1 0\n-10 0"
data, err = test_endpoint("chain", "/api/solve/cdcl", {"dimacs": chain_dimacs})
if err is None and data.get("sat") == False:
    log(f"   PASS: UNSAT in {data['time_seconds']:.4f}s")
else:
    log(f"   FAIL: {err or data}")

log("\n" + "=" * 60)
log("All tests completed!")
log("=" * 60)

# Write results to file
with open("comprehensive_test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
