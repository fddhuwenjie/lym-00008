from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sat_solver import (
    CNF,
    parse_dimacs,
    dpll_solve,
    cdcl_solve,
    generate_random_ksat,
    generate_pigeonhole,
    generate_chain_formula,
    generate_hard_3sat,
    encode_sudoku,
    decode_sudoku,
    parse_sudoku_string,
    format_sudoku,
    SUDOKU_PUZZLES,
    verify_proof,
    check_assignment,
    format_proof,
    run_all_benchmarks,
    get_preset_cases,
    get_case_by_name,
    run_benchmark,
)

app = FastAPI(
    title="SAT Solver API",
    description="A complete SAT solver API with DPLL, CDCL, formula generation, Sudoku encoding, and proof verification.",
    version="1.0.0",
)


class ParseRequest(BaseModel):
    dimacs: str = Field(..., description="DIMACS CNF format string")


class ParseResponse(BaseModel):
    num_vars: int
    num_clauses: int
    clauses: List[List[int]]
    comments: List[str]
    success: bool


class SolveRequest(BaseModel):
    dimacs: Optional[str] = Field(None, description="DIMACS CNF format string")
    clauses: Optional[List[List[int]]] = Field(None, description="List of clauses")
    num_vars: Optional[int] = Field(None, description="Number of variables (required if using clauses)")
    enable_proof: bool = Field(False, description="Enable UNSAT proof generation")


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
    stats: Optional[Dict[str, Any]] = None


class GenerateRandomRequest(BaseModel):
    num_vars: int = Field(..., ge=1, description="Number of variables")
    num_clauses: int = Field(..., ge=1, description="Number of clauses")
    k: int = Field(3, ge=1, description="k value for k-SAT")
    seed: Optional[int] = Field(None, description="Random seed")
    force_sat: bool = Field(False, description="Force formula to be satisfiable")


class GeneratePigeonholeRequest(BaseModel):
    num_pigeons: int = Field(..., ge=1, description="Number of pigeons")
    num_holes: int = Field(..., ge=1, description="Number of holes")


class GenerateResponse(BaseModel):
    dimacs: str
    num_vars: int
    num_clauses: int
    clauses: List[List[int]]


class SudokuEncodeRequest(BaseModel):
    puzzle: str = Field(..., description="Sudoku puzzle string (81 chars, 0 or . for empty)")
    size: int = Field(9, description="Sudoku size")


class SudokuDecodeRequest(BaseModel):
    assignment: Dict[str, bool] = Field(..., description="Variable assignment from SAT solver")
    size: int = Field(9, description="Sudoku size")


class SudokuSolveRequest(BaseModel):
    puzzle: str = Field(..., description="Sudoku puzzle string")
    size: int = Field(9, description="Sudoku size")
    solver: str = Field("cdcl", description="Solver to use: 'dpll' or 'cdcl'")


class SudokuResponse(BaseModel):
    solution: Optional[str] = None
    solution_formatted: Optional[str] = None
    sat: bool
    time_seconds: float
    cnf_vars: Optional[int] = None
    cnf_clauses: Optional[int] = None


class ProofVerifyRequest(BaseModel):
    dimacs: str = Field(..., description="Original DIMACS CNF")
    proof: List[List[int]] = Field(..., description="Proof clauses")


class ProofVerifyResponse(BaseModel):
    valid: bool
    step_results: List[bool]
    error_message: str = ""


class BenchmarkRunRequest(BaseModel):
    solvers: Optional[List[str]] = Field(None, description="Solvers to run")
    difficulty: Optional[str] = Field(None, description="Filter by difficulty: easy, medium, hard")
    enable_proof: bool = Field(False, description="Enable proof generation")


class BenchmarkCaseInfo(BaseModel):
    name: str
    num_vars: int
    num_clauses: int
    expected_sat: bool
    description: str
    difficulty: str


class BenchmarkResultResponse(BaseModel):
    name: str
    expected_sat: bool
    solver: str
    actual_sat: bool
    correct: bool
    time_seconds: float
    decision_steps: int
    additional_stats: Dict[str, Any]


@app.get("/")
async def root():
    return {
        "message": "SAT Solver API",
        "version": "1.0.0",
        "endpoints": {
            "parse": "POST /api/dimacs/parse",
            "solve_dpll": "POST /api/solve/dpll",
            "solve_cdcl": "POST /api/solve/cdcl",
            "generate_random": "POST /api/generate/random",
            "generate_pigeonhole": "POST /api/generate/pigeonhole",
            "sudoku_encode": "POST /api/sudoku/encode",
            "sudoku_decode": "POST /api/sudoku/decode",
            "sudoku_solve": "POST /api/sudoku/solve",
            "proof_verify": "POST /api/proof/verify",
            "benchmarks_cases": "GET /api/benchmarks/cases",
            "benchmarks_run": "POST /api/benchmarks/run",
            "benchmarks_run_case": "GET /api/benchmarks/run/{name}",
        },
    }


def _cnf_from_request(request: SolveRequest) -> CNF:
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


def _assignment_to_str_dict(assignment: Dict[int, bool]) -> Dict[str, bool]:
    return {str(k): v for k, v in assignment.items()}


def _str_dict_to_assignment(data: Dict[str, bool]) -> Dict[int, bool]:
    return {int(k): v for k, v in data.items()}


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
        stats=result.stats,
    )


@app.post("/api/solve/cdcl", response_model=SolveResponse)
async def solve_cdcl(request: SolveRequest):
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
        stats=result.stats,
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
async def sudoku_encode(request: SudokuEncodeRequest):
    puzzle = parse_sudoku_string(request.puzzle, request.size)
    cnf = encode_sudoku(puzzle, request.size)
    return GenerateResponse(
        dimacs=cnf.to_dimacs(),
        num_vars=cnf.num_vars,
        num_clauses=cnf.num_clauses,
        clauses=cnf.clauses,
    )


@app.post("/api/sudoku/decode")
async def sudoku_decode(request: SudokuDecodeRequest):
    assignment = _str_dict_to_assignment(request.assignment)
    grid = decode_sudoku(assignment, request.size)
    solution_str = "".join(str(v) for row in grid for v in row)
    return {
        "solution": solution_str,
        "solution_formatted": format_sudoku(grid, request.size),
        "grid": grid,
    }


@app.post("/api/sudoku/solve", response_model=SudokuResponse)
async def sudoku_solve(request: SudokuSolveRequest):
    import time

    start = time.time()
    puzzle = parse_sudoku_string(request.puzzle, request.size)
    cnf = encode_sudoku(puzzle, request.size)

    if request.solver == "dpll":
        result = dpll_solve(cnf)
    elif request.solver == "cdcl":
        result = cdcl_solve(cnf)
    else:
        raise HTTPException(status_code=400, detail="Solver must be 'dpll' or 'cdcl'")

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


@app.get("/api/benchmarks/cases", response_model=List[BenchmarkCaseInfo])
async def get_benchmark_cases():
    cases = get_preset_cases()
    return [BenchmarkCaseInfo(**case) for case in cases]


@app.post("/api/benchmarks/run", response_model=List[BenchmarkResultResponse])
async def run_benchmarks(request: BenchmarkRunRequest):
    results = run_all_benchmarks(
        solvers=request.solvers,
        difficulty_filter=request.difficulty,
        enable_proof=request.enable_proof,
    )
    return [
        BenchmarkResultResponse(
            name=r.name,
            expected_sat=r.expected_sat,
            solver=r.solver,
            actual_sat=r.actual_sat,
            correct=r.correct,
            time_seconds=r.time_seconds,
            decision_steps=r.decision_steps,
            additional_stats=r.additional_stats,
        )
        for r in results
    ]


@app.get("/api/benchmarks/run/{name}", response_model=List[BenchmarkResultResponse])
async def run_benchmark_case(name: str, solver: str = "cdcl", enable_proof: bool = False):
    try:
        case = get_case_by_name(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Benchmark case not found: {name}")

    result = run_benchmark(case, solver=solver, enable_proof=enable_proof)
    return [
        BenchmarkResultResponse(
            name=result.name,
            expected_sat=result.expected_sat,
            solver=result.solver,
            actual_sat=result.actual_sat,
            correct=result.correct,
            time_seconds=result.time_seconds,
            decision_steps=result.decision_steps,
            additional_stats=result.additional_stats,
        )
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)
