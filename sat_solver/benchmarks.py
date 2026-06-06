from typing import List, Dict, Any
from dataclasses import dataclass, field
import time
from .dimacs import CNF, parse_dimacs
from .dpll import dpll_solve, DPLLResult
from .cdcl import cdcl_solve, CDCLResult
from .formula_generator import (
    generate_random_ksat,
    generate_pigeonhole,
    generate_chain_formula,
    generate_hard_3sat,
)


@dataclass
class BenchmarkCase:
    name: str
    cnf: CNF
    expected_sat: bool
    description: str = ""
    difficulty: str = "easy"


@dataclass
class BenchmarkResult:
    name: str
    expected_sat: bool
    solver: str
    actual_sat: bool
    correct: bool
    time_seconds: float
    decision_steps: int
    additional_stats: Dict[str, Any] = field(default_factory=dict)


PRESET_CASES: List[BenchmarkCase] = []


def _init_preset_cases() -> None:
    global PRESET_CASES
    if PRESET_CASES:
        return

    dimacs_sat1 = """c Simple satisfiable formula
p cnf 3 2
1 2 3 0
-1 -2 0
"""
    PRESET_CASES.append(
        BenchmarkCase(
            name="sat_simple_3vars",
            cnf=parse_dimacs(dimacs_sat1),
            expected_sat=True,
            description="Simple 3-variable SAT formula",
            difficulty="easy",
        )
    )

    dimacs_unsat1 = """c Simple unsatisfiable formula
p cnf 2 4
1 2 0
1 -2 0
-1 2 0
-1 -2 0
"""
    PRESET_CASES.append(
        BenchmarkCase(
            name="unsat_simple_2vars",
            cnf=parse_dimacs(dimacs_unsat1),
            expected_sat=False,
            description="Simple 2-variable UNSAT formula (all combinations)",
            difficulty="easy",
        )
    )

    PRESET_CASES.append(
        BenchmarkCase(
            name="sat_random_50var_3sat",
            cnf=generate_random_ksat(50, 200, k=3, seed=42, force_sat=True),
            expected_sat=True,
            description="Random 3-SAT with 50 variables, guaranteed SAT",
            difficulty="medium",
        )
    )

    PRESET_CASES.append(
        BenchmarkCase(
            name="unsat_pigeonhole_4p_3h",
            cnf=generate_pigeonhole(4, 3),
            expected_sat=False,
            description="Pigeonhole principle: 4 pigeons into 3 holes (UNSAT)",
            difficulty="medium",
        )
    )

    PRESET_CASES.append(
        BenchmarkCase(
            name="sat_medium_100var_3sat",
            cnf=generate_random_ksat(100, 427, k=3, seed=123, force_sat=True),
            expected_sat=True,
            description="Random 3-SAT with 100 variables at phase transition ratio",
            difficulty="hard",
        )
    )

    PRESET_CASES.append(
        BenchmarkCase(
            name="unsat_chain_10vars",
            cnf=generate_chain_formula(10),
            expected_sat=False,
            description="Implication chain that forces UNSAT",
            difficulty="easy",
        )
    )

    PRESET_CASES.append(
        BenchmarkCase(
            name="sat_hard_100var",
            cnf=generate_hard_3sat(100),
            expected_sat=True,
            description="Hard 3-SAT at phase transition (100 vars)",
            difficulty="hard",
        )
    )


def run_benchmark(
    case: BenchmarkCase,
    solver: str = "cdcl",
    enable_proof: bool = False,
) -> BenchmarkResult:
    start = time.time()

    if solver == "dpll":
        result: DPLLResult = dpll_solve(case.cnf)
        actual_sat = result.sat
        decision_steps = result.decision_steps
        additional = {
            "stats": result.stats,
        }
    elif solver == "cdcl":
        result: CDCLResult = cdcl_solve(case.cnf, enable_proof=enable_proof)
        actual_sat = result.sat
        decision_steps = result.decision_steps
        additional = {
            "conflicts": result.conflicts,
            "restarts": result.restarts,
            "learnt_clauses": result.learnt_clauses,
            "stats": result.stats,
            "has_proof": result.proof is not None,
        }
    else:
        raise ValueError(f"Unknown solver: {solver}")

    elapsed = time.time() - start
    correct = actual_sat == case.expected_sat

    return BenchmarkResult(
        name=case.name,
        expected_sat=case.expected_sat,
        solver=solver,
        actual_sat=actual_sat,
        correct=correct,
        time_seconds=elapsed,
        decision_steps=decision_steps,
        additional_stats=additional,
    )


def run_all_benchmarks(
    solvers: List[str] = None,
    difficulty_filter: str = None,
    enable_proof: bool = False,
) -> List[BenchmarkResult]:
    _init_preset_cases()
    if solvers is None:
        solvers = ["cdcl", "dpll"]

    results = []
    for case in PRESET_CASES:
        if difficulty_filter and case.difficulty != difficulty_filter:
            continue
        for solver in solvers:
            result = run_benchmark(case, solver, enable_proof=enable_proof)
            results.append(result)

    return results


def get_preset_cases() -> List[Dict]:
    _init_preset_cases()
    return [
        {
            "name": case.name,
            "num_vars": case.cnf.num_vars,
            "num_clauses": case.cnf.num_clauses,
            "expected_sat": case.expected_sat,
            "description": case.description,
            "difficulty": case.difficulty,
        }
        for case in PRESET_CASES
    ]


def get_case_by_name(name: str) -> BenchmarkCase:
    _init_preset_cases()
    for case in PRESET_CASES:
        if case.name == name:
            return case
    raise ValueError(f"Case not found: {name}")
