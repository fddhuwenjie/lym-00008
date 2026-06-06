import sys
import json
import urllib.request

BASE_URL = "http://localhost:8008"

out = open("simple_unsat_test.txt", "w", buffering=1)

def log(msg):
    print(msg, flush=True)
    out.write(msg + "\n")
    out.flush()

log("Testing simple UNSAT formula...")

# Test 1: Root endpoint
log("\n1. Checking if service is alive...")
try:
    with urllib.request.urlopen(BASE_URL + "/", timeout=5) as resp:
        data = json.loads(resp.read().decode())
        log(f"   OK: {data}")
except Exception as e:
    log(f"   ERROR: {e}")
    out.close()
    sys.exit(1)

# Test 2: Simple SAT
log("\n2. Testing simple SAT formula...")
dimacs_sat = "p cnf 3 2\n1 2 3 0\n-1 -2 0"
try:
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": dimacs_sat}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data.get('sat')}")
        log(f"   Time: {data.get('time_seconds'):.4f}s")
        log(f"   Assignment valid: {data.get('assignment_valid')}")
except Exception as e:
    log(f"   ERROR: {e}")

# Test 3: Simple UNSAT
log("\n3. Testing simple UNSAT formula (2 vars, 4 clauses)...")
dimacs_unsat = "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0"
try:
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": dimacs_unsat, "enable_proof": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    log("   Sending request...")
    with urllib.request.urlopen(req, timeout=30) as resp:
        log("   Got response!")
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data.get('sat')}")
        log(f"   Time: {data.get('time_seconds'):.4f}s")
        log(f"   Conflicts: {data.get('conflicts')}")
        proof = data.get("proof")
        if proof:
            log(f"   Proof length: {len(proof)}")
            for i, p in enumerate(proof[:3]):
                log(f"     {i+1}: {p}")
except Exception as e:
    log(f"   ERROR: {e}")
    import traceback
    log(traceback.format_exc())

# Test 4: Chain formula UNSAT
log("\n4. Testing chain formula UNSAT (10 vars)...")
chain = "p cnf 10 11\n-1 2 0\n-2 3 0\n-3 4 0\n-4 5 0\n-5 6 0\n-6 7 0\n-7 8 0\n-8 9 0\n-9 10 0\n1 0\n-10 0"
try:
    req = urllib.request.Request(
        BASE_URL + "/api/solve/cdcl",
        data=json.dumps({"dimacs": chain}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    log("   Sending request...")
    with urllib.request.urlopen(req, timeout=30) as resp:
        log("   Got response!")
        data = json.loads(resp.read().decode())
        log(f"   SAT: {data.get('sat')}")
        log(f"   Time: {data.get('time_seconds'):.4f}s")
        log(f"   Conflicts: {data.get('conflicts')}")
except Exception as e:
    log(f"   ERROR: {e}")

log("\nDone!")
out.close()
