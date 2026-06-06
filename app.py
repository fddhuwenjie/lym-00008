import sys
sys.path.insert(0, '.')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import random

from sat_solver.dimacs import CNF, parse_dimacs
from sat_solver.dpll import dpll_solve
from sat_solver.cdcl import cdcl_solve
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


if __name__ == "__main__":
    import uvicorn
    print("Starting SAT Solver API on port 8008...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8008)
