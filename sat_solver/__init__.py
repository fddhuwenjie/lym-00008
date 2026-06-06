from .dimacs import CNF, parse_dimacs, parse_dimacs_file
from .dpll import dpll_solve, DPLLResult
from .cdcl import cdcl_solve, CDCLResult
from .formula_generator import (
    generate_random_ksat,
    generate_pigeonhole,
    generate_chain_formula,
    generate_2sat_phase_transition,
    generate_hard_3sat,
)
from .sudoku import (
    encode_sudoku,
    decode_sudoku,
    parse_sudoku_string,
    sudoku_to_string,
    format_sudoku,
    SUDOKU_PUZZLES,
)
from .proof import verify_proof, check_assignment, format_proof
from .benchmarks import (
    BenchmarkCase,
    BenchmarkResult,
    run_benchmark,
    run_all_benchmarks,
    get_preset_cases,
    get_case_by_name,
)

__all__ = [
    "CNF",
    "parse_dimacs",
    "parse_dimacs_file",
    "dpll_solve",
    "DPLLResult",
    "cdcl_solve",
    "CDCLResult",
    "generate_random_ksat",
    "generate_pigeonhole",
    "generate_chain_formula",
    "generate_2sat_phase_transition",
    "generate_hard_3sat",
    "encode_sudoku",
    "decode_sudoku",
    "parse_sudoku_string",
    "sudoku_to_string",
    "format_sudoku",
    "SUDOKU_PUZZLES",
    "verify_proof",
    "check_assignment",
    "format_proof",
    "BenchmarkCase",
    "BenchmarkResult",
    "run_benchmark",
    "run_all_benchmarks",
    "get_preset_cases",
    "get_case_by_name",
]
