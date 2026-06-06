import sys
sys.path.insert(0, '.')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
import time
import random

from sat_solver.dimacs import CNF, WCNF, parse_dimacs, parse_wcnf
from sat_solver.dpll import dpll_solve
from sat_solver.cdcl import cdcl_solve
from sat_solver.maxsat import (
    oll_maxsat_solve,
    maxsat_solve_from_wcnf,
    maxsat_solve_from_clauses,
    brute_force_maxsat,
    MaxSATResult,
)
from sat_solver.vertex_cover import (
    WeightedGraph,
    encode_weighted_vertex_cover,
    decode_vertex_cover,
    is_valid_vertex_cover,
    brute_force_min_vertex_cover,
)
from sat_solver.formula_generator import (
    generate_random_ksat,
    generate_pigeonhole,
    generate_chain_formula,
    generate_hard_3sat,
)
from sat_solver.sudoku import (
    encode_sudoku,
    decode_sudoku,
    parse_sudoku_string,
    format_sudoku,
    SUDOKU_PUZZLES,
)
from sat_solver.proof import verify_proof, check_assignment, format_proof

app = FastAPI(
    title="SAT Solver API",
    description="SAT Solver API with DPLL, CDCL, formula generation, and Sudoku encoding.",
    version="1.0.0",
)


def create_test_instances() -> Dict[str, Tuple[str, WCNF]]:
    instances = {}

    hard_soft_clauses = []
    top1 = 1000
    hard_soft_clauses.append((top1, [1, 2]))
    hard_soft_clauses.append((top1, [3, 4]))
    hard_soft_clauses.append((top1, [5, 6]))
    hard_soft_clauses.append((top1, [7, 8]))
    hard_soft_clauses.append((top1, [9, 10]))
    hard_soft_clauses.append((top1, [-1, -3]))
    hard_soft_clauses.append((top1, [-2, -4]))
    hard_soft_clauses.append((top1, [-5, -7]))
    hard_soft_clauses.append((top1, [-6, -8]))
    hard_soft_clauses.append((top1, [-9, -10]))
    hard_soft_clauses.append((10, [1]))
    hard_soft_clauses.append((20, [2]))
    hard_soft_clauses.append((30, [3]))
    hard_soft_clauses.append((40, [4]))
    hard_soft_clauses.append((50, [5]))
    hard_soft_clauses.append((60, [6]))
    hard_soft_clauses.append((70, [7]))
    hard_soft_clauses.append((80, [8]))
    hard_soft_clauses.append((90, [9]))
    hard_soft_clauses.append((100, [10]))

    wcnf1 = WCNF(
        num_vars=10,
        num_clauses=len(hard_soft_clauses),
        top=top1,
        clauses=hard_soft_clauses,
        comments=["Test instance 1: Hard + soft mixed (10 vars, 20 clauses)"],
    )
    instances["mixed_hard_soft_10var"] = (
        "10 variables with hard constraints and weighted soft clauses",
        wcnf1,
    )

    soft_only_clauses = []
    num_vars_soft = 8
    top2 = 1000
    for i in range(1, num_vars_soft + 1):
        soft_only_clauses.append((i * 5, [i]))
    soft_only_clauses.append((50, [1, 2]))
    soft_only_clauses.append((60, [3, 4]))
    soft_only_clauses.append((70, [5, 6]))
    soft_only_clauses.append((80, [7, 8]))
    soft_only_clauses.append((25, [-1, -2]))
    soft_only_clauses.append((35, [-3, -4]))
    soft_only_clauses.append((45, [-5, -6]))
    soft_only_clauses.append((55, [-7, -8]))

    wcnf2 = WCNF(
        num_vars=num_vars_soft,
        num_clauses=len(soft_only_clauses),
        top=top2,
        clauses=soft_only_clauses,
        comments=["Test instance 2: Pure soft clauses (8 vars, 16 clauses)"],
    )
    instances["pure_soft_8var"] = (
        "8 variables with only soft clauses (no hard constraints)",
        wcnf2,
    )

    graph = WeightedGraph(
        num_vertices=6,
        edges=[(1, 2), (1, 3), (2, 3), (2, 4), (3, 5), (4, 5), (4, 6), (5, 6)],
        vertex_weights={1: 10, 2: 20, 3: 30, 4: 15, 5: 25, 6: 35},
    )
    wcnf3 = encode_weighted_vertex_cover(graph)
    instances["vertex_cover_6node"] = (
        "Weighted vertex cover on 6-node graph",
        wcnf3,
    )

    num_vars_mixed50 = 50
    top_mixed50 = 100000
    mixed50_clauses = []

    for i in range(1, 26):
        mixed50_clauses.append((top_mixed50, [2 * i - 1, 2 * i]))
        mixed50_clauses.append((top_mixed50, [-(2 * i - 1), -(2 * i)]))

    for i in range(1, 11):
        v1 = i
        v2 = (i % 25) + 1
        mixed50_clauses.append((top_mixed50, [v1, v2, (v1 + v2) % 50 + 1]))

    for i in range(1, num_vars_mixed50 + 1):
        mixed50_clauses.append((i * 10, [i]))

    wcnf4 = WCNF(
        num_vars=num_vars_mixed50,
        num_clauses=len(mixed50_clauses),
        top=top_mixed50,
        clauses=mixed50_clauses,
        comments=["Test instance 4: Mixed hard+soft (50 vars, ~120 clauses)"],
    )
    instances["mixed_hard_soft_50var"] = (
        "50 variables with hard constraints and weighted soft clauses for performance test",
        wcnf4,
    )

    return instances


class ParseRequest(BaseModel):
    dimacs: str


class ParseResponse(BaseModel):
    num_vars: int
    num_clauses: int
    clauses: List[List[int]]
    comments: List[str]
    success: bool


class SolveRequest(BaseModel):
    dimacs: Optional[str] = None
    clauses: Optional[List[List[int]]] = None
    num_vars: Optional[int] = None
    enable_proof: bool = False


class SolveResponse(BaseModel):
    sat: bool
    assignment: Optional[Dict[str, bool]]
    decision_steps: int
    time_seconds: float
    conflicts: Optional[int] = None
    restarts: Optional[int] = None
    learnt_clauses: Optional[int] = None
    proof: Optional[List[List[int]]] = None
    proof_formatted: Optional[str] = None
    assignment_valid: Optional[bool] = None


class GenerateRandomRequest(BaseModel):
    num_vars: int
    num_clauses: int
    k: int = 3
    seed: Optional[int] = None
    force_sat: bool = False


class GeneratePigeonholeRequest(BaseModel):
    num_pigeons: int
    num_holes: int


class GenerateResponse(BaseModel):
    dimacs: str
    num_vars: int
    num_clauses: int
    clauses: List[List[int]]


class SudokuSolveRequest(BaseModel):
    puzzle: str
    size: int = 9
    solver: str = "cdcl"


class SudokuResponse(BaseModel):
    solution: Optional[str] = None
    solution_formatted: Optional[str] = None
    sat: bool
    time_seconds: float
    cnf_vars: Optional[int] = None
    cnf_clauses: Optional[int] = None


class ProofVerifyRequest(BaseModel):
    dimacs: str
    proof: List[List[int]]


class ProofVerifyResponse(BaseModel):
    valid: bool
    step_results: List[bool]
    error_message: str = ""


def _cnf_from_request(request):
    if request.dimacs:
        try:
            return parse_dimacs(request.dimacs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse DIMACS: {e}")
    elif request.clauses and request.num_vars:
        return CNF(
            num_vars=request.num_vars,
            num_clauses=len(request.clauses),
            clauses=request.clauses,
            comments=[],
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'dimacs' or both 'clauses' and 'num_vars' must be provided",
        )


def _assignment_to_str_dict(assignment):
    return {str(k): v for k, v in assignment.items()}


def _str_dict_to_assignment(data):
    return {int(k): v for k, v in data.items()}


@app.get("/")
async def root():
    return {
        "message": "SAT Solver API",
        "version": "1.0.0",
        "port": 8008,
    }


@app.post("/api/dimacs/parse", response_model=ParseResponse)
async def parse_dimacs_endpoint(request: ParseRequest):
    try:
        cnf = parse_dimacs(request.dimacs)
        return ParseResponse(
            num_vars=cnf.num_vars,
            num_clauses=cnf.num_clauses,
            clauses=cnf.clauses,
            comments=cnf.comments,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/solve/dpll", response_model=SolveResponse)
async def solve_dpll(request: SolveRequest):
    cnf = _cnf_from_request(request)
    result = dpll_solve(cnf)

    assignment_dict = None
    assignment_valid = None
    if result.assignment:
        assignment_dict = _assignment_to_str_dict(result.assignment)
        valid, _ = check_assignment(cnf, result.assignment)
        assignment_valid = valid

    return SolveResponse(
        sat=result.sat,
        assignment=assignment_dict,
        decision_steps=result.decision_steps,
        time_seconds=result.time_seconds,
        assignment_valid=assignment_valid,
    )


@app.post("/api/solve/cdcl", response_model=SolveResponse)
async def solve_cdcl_endpoint(request: SolveRequest):
    cnf = _cnf_from_request(request)
    result = cdcl_solve(cnf, enable_proof=request.enable_proof)

    assignment_dict = None
    assignment_valid = None
    if result.assignment:
        assignment_dict = _assignment_to_str_dict(result.assignment)
        valid, _ = check_assignment(cnf, result.assignment)
        assignment_valid = valid

    proof_formatted = None
    if result.proof:
        proof_formatted = format_proof(result.proof)

    return SolveResponse(
        sat=result.sat,
        assignment=assignment_dict,
        decision_steps=result.decision_steps,
        time_seconds=result.time_seconds,
        conflicts=result.conflicts,
        restarts=result.restarts,
        learnt_clauses=result.learnt_clauses,
        proof=result.proof,
        proof_formatted=proof_formatted,
        assignment_valid=assignment_valid,
    )


@app.post("/api/generate/random", response_model=GenerateResponse)
async def generate_random(request: GenerateRandomRequest):
    cnf = generate_random_ksat(
        num_vars=request.num_vars,
        num_clauses=request.num_clauses,
        k=request.k,
        seed=request.seed,
        force_sat=request.force_sat,
    )
    return GenerateResponse(
        dimacs=cnf.to_dimacs(),
        num_vars=cnf.num_vars,
        num_clauses=cnf.num_clauses,
        clauses=cnf.clauses,
    )


@app.post("/api/generate/pigeonhole", response_model=GenerateResponse)
async def generate_pigeonhole_endpoint(request: GeneratePigeonholeRequest):
    cnf = generate_pigeonhole(request.num_pigeons, request.num_holes)
    return GenerateResponse(
        dimacs=cnf.to_dimacs(),
        num_vars=cnf.num_vars,
        num_clauses=cnf.num_clauses,
        clauses=cnf.clauses,
    )


@app.post("/api/sudoku/encode", response_model=GenerateResponse)
async def sudoku_encode(request: SudokuSolveRequest):
    puzzle = parse_sudoku_string(request.puzzle, request.size)
    cnf = encode_sudoku(puzzle, request.size)
    return GenerateResponse(
        dimacs=cnf.to_dimacs(),
        num_vars=cnf.num_vars,
        num_clauses=cnf.num_clauses,
        clauses=cnf.clauses,
    )


@app.post("/api/sudoku/solve", response_model=SudokuResponse)
async def sudoku_solve(request: SudokuSolveRequest):
    start = time.time()
    puzzle = parse_sudoku_string(request.puzzle, request.size)
    cnf = encode_sudoku(puzzle, request.size)

    if request.solver == "dpll":
        result = dpll_solve(cnf)
    else:
        result = cdcl_solve(cnf)

    elapsed = time.time() - start

    if result.sat and result.assignment:
        grid = decode_sudoku(result.assignment, request.size)
        solution_str = "".join(str(v) for row in grid for v in row)
        return SudokuResponse(
            solution=solution_str,
            solution_formatted=format_sudoku(grid, request.size),
            sat=True,
            time_seconds=elapsed,
            cnf_vars=cnf.num_vars,
            cnf_clauses=cnf.num_clauses,
        )
    else:
        return SudokuResponse(
            solution=None,
            solution_formatted=None,
            sat=False,
            time_seconds=elapsed,
            cnf_vars=cnf.num_vars,
            cnf_clauses=cnf.num_clauses,
        )


@app.get("/api/sudoku/puzzles")
async def get_sudoku_puzzles():
    return {k: v for k, v in SUDOKU_PUZZLES.items()}


@app.post("/api/proof/verify", response_model=ProofVerifyResponse)
async def proof_verify(request: ProofVerifyRequest):
    try:
        cnf = parse_dimacs(request.dimacs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse DIMACS: {e}")

    result = verify_proof(cnf, request.proof)
    return ProofVerifyResponse(
        valid=result.valid,
        step_results=result.step_results,
        error_message=result.error_message,
    )


@app.get("/api/benchmarks/cases")
async def get_benchmark_cases():
    cases = [
        {
            "name": "sat_simple_3vars",
            "num_vars": 3,
            "num_clauses": 2,
            "expected_sat": True,
            "description": "Simple 3-variable SAT formula",
            "difficulty": "easy",
        },
        {
            "name": "unsat_simple_2vars",
            "num_vars": 2,
            "num_clauses": 4,
            "expected_sat": False,
            "description": "Simple 2-variable UNSAT formula",
            "difficulty": "easy",
        },
        {
            "name": "sat_random_50var_3sat",
            "num_vars": 50,
            "num_clauses": 200,
            "expected_sat": True,
            "description": "Random 3-SAT with 50 variables",
            "difficulty": "medium",
        },
        {
            "name": "unsat_pigeonhole_4p_3h",
            "num_vars": 12,
            "num_clauses": 58,
            "expected_sat": False,
            "description": "Pigeonhole: 4 pigeons into 3 holes",
            "difficulty": "medium",
        },
        {
            "name": "sat_medium_100var_3sat",
            "num_vars": 100,
            "num_clauses": 427,
            "expected_sat": True,
            "description": "Random 3-SAT with 100 variables at phase transition",
            "difficulty": "hard",
        },
        {
            "name": "unsat_chain_10vars",
            "num_vars": 10,
            "num_clauses": 11,
            "expected_sat": False,
            "description": "Implication chain UNSAT",
            "difficulty": "easy",
        },
        {
            "name": "sat_hard_100var",
            "num_vars": 100,
            "num_clauses": 427,
            "expected_sat": True,
            "description": "Hard 3-SAT at phase transition",
            "difficulty": "hard",
        },
    ]
    return cases


class WCNFParseRequest(BaseModel):
    wcnf: str


class WCNFParseResponse(BaseModel):
    num_vars: int
    num_clauses: int
    top: int
    clauses: List[Tuple[int, List[int]]]
    comments: List[str]
    success: bool


class MaxSATSolveRequest(BaseModel):
    wcnf: Optional[str] = None
    weighted_clauses: Optional[List[Tuple[int, List[int]]]] = None
    num_vars: Optional[int] = None
    top: Optional[int] = None
    max_time: float = 60.0


class MaxSATSolveResponse(BaseModel):
    optimal_weight: int
    assignment: Dict[str, bool]
    unsatisfied_soft_indices: List[int]
    time_seconds: float
    cores_found: int
    iterations: int
    status: str
    assignment_valid: Optional[bool] = None
    brute_force_match: Optional[bool] = None


class VertexCoverEncodeRequest(BaseModel):
    num_vertices: int
    edges: List[Tuple[int, int]]
    vertex_weights: Dict[int, int]


class VertexCoverSolveRequest(BaseModel):
    num_vertices: int
    edges: List[Tuple[int, int]]
    vertex_weights: Dict[int, int]
    max_time: float = 60.0


class VertexCoverSolveResponse(BaseModel):
    cover: List[int]
    total_weight: int
    valid: bool
    time_seconds: float
    wcnf_num_vars: int
    wcnf_num_clauses: int
    maxsat_optimal_weight: int
    maxsat_status: str
    brute_force_weight: Optional[int] = None
    brute_force_match: Optional[bool] = None


class MaxSATVerifyRequest(BaseModel):
    wcnf: str


class MaxSATVerifyResponse(BaseModel):
    oll_optimal_weight: int
    brute_force_optimal_weight: int
    match: bool
    oll_time_seconds: float
    brute_force_time_seconds: float


def _wcnf_from_request(request: MaxSATSolveRequest) -> WCNF:
    if request.wcnf:
        try:
            return parse_wcnf(request.wcnf)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse WCNF: {e}")
    elif request.weighted_clauses and request.num_vars is not None:
        if request.top is None:
            weights = [w for w, _ in request.weighted_clauses]
            if weights:
                max_weight = max(weights)
                top = sum(w for w in weights if w < max_weight * 1000) + 1
            else:
                top = 1
        else:
            top = request.top
        return WCNF(
            num_vars=request.num_vars,
            num_clauses=len(request.weighted_clauses),
            top=top,
            clauses=request.weighted_clauses,
            comments=[],
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'wcnf' or both 'weighted_clauses' and 'num_vars' must be provided",
        )


def _check_wcnf_assignment(wcnf: WCNF, assignment: Dict[int, bool]) -> Tuple[bool, int, List[int]]:
    soft_weight = 0
    unsatisfied = []
    hard_satisfied = True

    for idx, (weight, literals) in enumerate(wcnf.clauses):
        clause_sat = False
        for lit in literals:
            var = abs(lit)
            val = assignment.get(var, False)
            if (lit > 0) == val:
                clause_sat = True
                break

        if weight >= wcnf.top:
            if not clause_sat:
                hard_satisfied = False
        else:
            if clause_sat:
                soft_weight += weight
            else:
                unsatisfied.append(idx)

    return hard_satisfied, soft_weight, sorted(unsatisfied)


@app.post("/api/wcnf/parse", response_model=WCNFParseResponse)
async def parse_wcnf_endpoint(request: WCNFParseRequest):
    try:
        wcnf = parse_wcnf(request.wcnf)
        return WCNFParseResponse(
            num_vars=wcnf.num_vars,
            num_clauses=wcnf.num_clauses,
            top=wcnf.top,
            clauses=wcnf.clauses,
            comments=wcnf.comments,
            success=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/maxsat/solve", response_model=MaxSATSolveResponse)
async def maxsat_solve_endpoint(request: MaxSATSolveRequest):
    wcnf = _wcnf_from_request(request)
    result = oll_maxsat_solve(wcnf, max_time=request.max_time)

    assignment_valid = None
    if result.assignment:
        hard_ok, calc_weight, calc_unsat = _check_wcnf_assignment(wcnf, result.assignment)
        assignment_valid = hard_ok and calc_weight == result.optimal_weight and calc_unsat == result.unsatisfied_soft_indices

    brute_force_match = None
    if wcnf.num_vars <= 15 and result.assignment:
        try:
            bf_weight, bf_assign, bf_unsat = brute_force_maxsat(wcnf)
            brute_force_match = bf_weight == result.optimal_weight
        except:
            pass

    assignment_dict = _assignment_to_str_dict(result.assignment) if result.assignment else {}

    return MaxSATSolveResponse(
        optimal_weight=result.optimal_weight,
        assignment=assignment_dict,
        unsatisfied_soft_indices=result.unsatisfied_soft_indices,
        time_seconds=result.time_seconds,
        cores_found=result.cores_found,
        iterations=result.iterations,
        status=result.status,
        assignment_valid=assignment_valid,
        brute_force_match=brute_force_match,
    )


@app.post("/api/vertexcover/encode", response_model=GenerateResponse)
async def vertexcover_encode_endpoint(request: VertexCoverEncodeRequest):
    graph = WeightedGraph(
        num_vertices=request.num_vertices,
        edges=request.edges,
        vertex_weights=request.vertex_weights,
    )
    wcnf = encode_weighted_vertex_cover(graph)
    return GenerateResponse(
        dimacs=wcnf.to_wcnf(),
        num_vars=wcnf.num_vars,
        num_clauses=wcnf.num_clauses,
        clauses=[list(c) for _, c in wcnf.clauses],
    )


@app.post("/api/vertexcover/solve", response_model=VertexCoverSolveResponse)
async def vertexcover_solve_endpoint(request: VertexCoverSolveRequest):
    start = time.time()

    graph = WeightedGraph(
        num_vertices=request.num_vertices,
        edges=request.edges,
        vertex_weights=request.vertex_weights,
    )

    wcnf = encode_weighted_vertex_cover(graph)
    maxsat_result = oll_maxsat_solve(wcnf, max_time=request.max_time)

    cover: List[int] = []
    total_weight = 0
    valid = False

    if maxsat_result.assignment:
        cover_set, total_weight = decode_vertex_cover(maxsat_result.assignment, graph)
        cover = sorted(list(cover_set))
        valid = is_valid_vertex_cover(cover_set, graph)

    elapsed = time.time() - start

    brute_force_weight = None
    brute_force_match = None
    if graph.num_vertices <= 15:
        try:
            bf_cover, bf_weight = brute_force_min_vertex_cover(graph)
            brute_force_weight = bf_weight
            brute_force_match = bf_weight == total_weight
        except:
            pass

    return VertexCoverSolveResponse(
        cover=cover,
        total_weight=total_weight,
        valid=valid,
        time_seconds=elapsed,
        wcnf_num_vars=wcnf.num_vars,
        wcnf_num_clauses=wcnf.num_clauses,
        maxsat_optimal_weight=maxsat_result.optimal_weight,
        maxsat_status=maxsat_result.status,
        brute_force_weight=brute_force_weight,
        brute_force_match=brute_force_match,
    )


@app.post("/api/maxsat/verify", response_model=MaxSATVerifyResponse)
async def maxsat_verify_endpoint(request: MaxSATVerifyRequest):
    wcnf = parse_wcnf(request.wcnf)

    if wcnf.num_vars > 15:
        raise HTTPException(
            status_code=400,
            detail=f"Too many variables for brute force verification: {wcnf.num_vars} (max 15)",
        )

    t1 = time.time()
    oll_result = oll_maxsat_solve(wcnf, max_time=60.0)
    oll_time = time.time() - t1

    t2 = time.time()
    bf_weight, bf_assign, bf_unsat = brute_force_maxsat(wcnf)
    bf_time = time.time() - t2

    return MaxSATVerifyResponse(
        oll_optimal_weight=oll_result.optimal_weight,
        brute_force_optimal_weight=bf_weight,
        match=oll_result.optimal_weight == bf_weight,
        oll_time_seconds=oll_time,
        brute_force_time_seconds=bf_time,
    )


@app.get("/api/maxsat/test-instances")
async def get_maxsat_test_instances():
    instances = create_test_instances()
    return {
        name: {
            "description": desc,
            "num_vars": wcnf.num_vars,
            "num_clauses": wcnf.num_clauses,
            "top": wcnf.top,
            "wcnf": wcnf.to_wcnf(),
        }
        for name, (desc, wcnf) in instances.items()
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting SAT Solver API on port 8008...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8008)
