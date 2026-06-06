from typing import List, Tuple
import random
from .dimacs import CNF


def generate_random_ksat(
    num_vars: int,
    num_clauses: int,
    k: int = 3,
    seed: int = None,
    force_sat: bool = False,
) -> CNF:
    if seed is not None:
        random.seed(seed)

    clauses: List[List[int]] = []
    target_assignment = None

    if force_sat:
        target_assignment = [random.choice([True, False]) for _ in range(num_vars)]

    for _ in range(num_clauses):
        clause_vars = random.sample(range(1, num_vars + 1), min(k, num_vars))
        clause = []
        for var in clause_vars:
            polarity = random.choice([True, False])
            if force_sat and target_assignment is not None and var == clause_vars[0]:
                polarity = target_assignment[var - 1]
            lit = var if polarity else -var
            clause.append(lit)
        clauses.append(clause)

    comments = [
        f"Random {k}-SAT formula",
        f"Variables: {num_vars}, Clauses: {num_clauses}",
        f"Seed: {seed}",
    ]

    if force_sat:
        comments.append("Guaranteed satisfiable")

    return CNF(
        num_vars=num_vars,
        num_clauses=num_clauses,
        clauses=clauses,
        comments=comments,
    )


def generate_pigeonhole(num_pigeons: int, num_holes: int) -> CNF:
    var_index: Dict[Tuple[int, int], int] = {}
    idx = 1
    for p in range(num_pigeons):
        for h in range(num_holes):
            var_index[(p, h)] = idx
            idx += 1

    num_vars = idx - 1
    clauses: List[List[int]] = []

    for p in range(num_pigeons):
        clause = [var_index[(p, h)] for h in range(num_holes)]
        clauses.append(clause)

    for p in range(num_pigeons):
        for h1 in range(num_holes):
            for h2 in range(h1 + 1, num_holes):
                clause = [-var_index[(p, h1)], -var_index[(p, h2)]]
                clauses.append(clause)

    for h in range(num_holes):
        for p1 in range(num_pigeons):
            for p2 in range(p1 + 1, num_pigeons):
                clause = [-var_index[(p1, h)], -var_index[(p2, h)]]
                clauses.append(clause)

    comments = [
        f"Pigeonhole Principle: {num_pigeons} pigeons, {num_holes} holes",
        f"UNSAT: {num_pigeons > num_holes}",
    ]

    return CNF(
        num_vars=num_vars,
        num_clauses=len(clauses),
        clauses=clauses,
        comments=comments,
    )


def generate_chain_formula(num_vars: int) -> CNF:
    clauses: List[List[int]] = []

    for i in range(1, num_vars):
        clauses.append([-i, i + 1])

    clauses.append([1])
    clauses.append([-num_vars])

    comments = [
        f"Chain formula (implication chain that forces UNSAT)",
        f"Variables: {num_vars}",
    ]

    return CNF(
        num_vars=num_vars,
        num_clauses=len(clauses),
        clauses=clauses,
        comments=comments,
    )


def generate_2sat_phase_transition(num_vars: int, ratio: float = 1.0) -> CNF:
    num_clauses = int(num_vars * ratio)
    clauses: List[List[int]] = []

    for _ in range(num_clauses):
        vars_sample = random.sample(range(1, num_vars + 1), 2)
        clause = []
        for var in vars_sample:
            lit = var if random.random() < 0.5 else -var
            clause.append(lit)
        clauses.append(clause)

    comments = [
        f"2-SAT formula at ratio {ratio}",
        f"Variables: {num_vars}, Clauses: {num_clauses}",
    ]

    return CNF(
        num_vars=num_vars,
        num_clauses=num_clauses,
        clauses=clauses,
        comments=comments,
    )


def generate_hard_3sat(num_vars: int) -> CNF:
    ratio = 4.27
    num_clauses = int(num_vars * ratio)
    return generate_random_ksat(num_vars, num_clauses, k=3)
