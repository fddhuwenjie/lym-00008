import sys
import json
import urllib.request

BASE_URL = "http://localhost:8008"

out = open("api_test_output.txt", "w", buffering=1)

def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log("Testing SAT Solver API")
log("=" * 50)

try:
    log("\n1. Root endpoint")
    with urllib.request.urlopen(BASE_URL + "/") as resp:
        data = json.loads(resp.read().decode())
        log(f"   OK: {data}")

    log("\n2. DIMACS parse")
    dimacs = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
    req = urllib.request.Request(
        BASE_URL + "/api/dimacs/parse",
        data=json.dumps({"dimacs": dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   OK: {data['num_vars']} vars, {data['num_clauses']} clauses")

    log("\n3. DPLL SAT solve")
    req = urllib.request.Request(
        BASE_URL + "/api/solve/dpll",
        data=json.dumps({"dimacs": dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']}, valid: {data['assignment_valid']}, time: {data['time_seconds']:.4f}s")

    log("\n4. CDCL SAT solve")
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']}, valid: {data['assignment_valid']}, time: {data['time_seconds']:.4f}s")
        log(f"   conflicts: {data['conflicts']}, restarts: {data['restarts']}")

    log("\n5. CDCL UNSAT solve")
    unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": unsat, "enable_proof": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']}")
        log(f"   conflicts: {data['conflicts']}, time: {data['time_seconds']:.4f}s")
        proof = data.get("proof")
        if proof:
            log(f"   proof length: {len(proof)}")
            for i, p in enumerate(proof[:5]):
                log(f"     {i+1}: {p}")

    log("\n6. Generate random 3-SAT (50 vars)")
    req = urllib.request.Request(
        BASE_URL + "/api/generate/random",
        data=json.dumps({
            "num_vars": 50, "num_clauses": 200, "k": 3, "seed": 42, "force_sat": True
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   Generated: {data['num_vars']} vars, {data['num_clauses']} clauses")
        new_dimacs = data["dimacs"]

    log("   Solving...")
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": new_dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']}, time: {data['time_seconds']:.4f}s")
        log(f"   conflicts: {data['conflicts']}, learnt: {data['learnt_clauses']}")

    log("\n7. Pigeonhole (4, 3) - UNSAT")
    req = urllib.request.Request(
        BASE_URL + "/api/generate/pigeonhole",
        data=json.dumps({"num_pigeons": 4, "num_holes": 3}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   Generated: {data['num_vars']} vars, {data['num_clauses']} clauses")
        php_dimacs = data["dimacs"]

    log("   Solving...")
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": php_dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']} (expected: False)")
        log(f"   time: {data['time_seconds']:.4f}s, conflicts: {data['conflicts']}")

    log("\n8. 100-var 3-SAT performance test")
    req = urllib.request.Request(
        BASE_URL + "/api/generate/random",
        data=json.dumps({
            "num_vars": 100, "num_clauses": 427, "k": 3, "seed": 123, "force_sat": True
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        log(f"   Generated: {data['num_vars']} vars, {data['num_clauses']} clauses")
        perf_dimacs = data["dimacs"]

    log("   Solving (should be < 10s)...")
    import time
    start = time.time()
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": perf_dimacs}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        elapsed = time.time() - start
        log(f"   SAT: {data['sat']}, time: {elapsed:.4f}s")
        log(f"   conflicts: {data['conflicts']}, restarts: {data['restarts']}")
        log(f"   learnt clauses: {data['learnt_clauses']}")
        if elapsed < 10:
            log("   PERFORMANCE OK (< 10s")
        else:
            log("   PERFORMANCE WARNING (> 10s)")

    log("\n9. Sudoku solve")
    puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
    req = urllib.request.Request(
        BASE_URL + "/api/sudoku/solve",
        data=json.dumps({"puzzle": puzzle, "size": 9, "solver": "cdcl"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data['sat']}, time: {data['time_seconds']:.4f}s")
        if data.get("solution"):
            log(f"   Solution: {data['solution'][:30}...")
            log(f"   Formatted:\n{data['solution_formatted']}")

    log("\n10. Benchmark cases")
    with urllib.request.urlopen(BASE_URL + "/api/benchmarks/cases") as resp:
        data = json.loads(resp.read().decode())
        log(f"   {len(data)} benchmark cases available:")
        for c in data:
            log(f"     - {c['name']} ({c['difficulty']}): {c['num_vars']} vars, expected: {c['expected_sat']}")

    log("\n" + "=" * 50)
    log("ALL TESTS COMPLETED SUCCESSFULLY!")
    log("=" * 50)

except Exception as e:
    log(f"\nERROR: {e}")
    import traceback
    log(traceback.format_exc())

finally:
    out.close()
