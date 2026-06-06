from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import time
from .dimacs import CNF


@dataclass
class DPLLResult:
    sat: bool
    assignment: Optional[Dict[int, bool]]
    decision_steps: int
    time_seconds: float
    stats: Dict


def _unit_propagation(
    clauses: List[List[int]], assignment: Dict[int, bool]
) -> Tuple[bool, Dict[int, bool], List[List[int]]]:
    changed = True
    while changed:
        changed = False
        new_clauses = []
        for clause in clauses:
            simplified = []
            clause_sat = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0) == assignment[var]:
                        clause_sat = True
                        break
                else:
                    simplified.append(lit)
            if clause_sat:
                continue
            if not simplified:
                return False, assignment, clauses
            if len(simplified) == 1:
                unit_lit = simplified[0]
                var = abs(unit_lit)
                value = unit_lit > 0
                if var in assignment:
                    if assignment[var] != value:
                        return False, assignment, clauses
                else:
                    assignment[var] = value
                    changed = True
            else:
                new_clauses.append(simplified)
        clauses = new_clauses
    return True, assignment, clauses


def _pure_literal_elimination(
    clauses: List[List[int]], assignment: Dict[int, bool], num_vars: int
) -> Tuple[Dict[int, bool], List[List[int]]]:
    literal_polarity: Dict[int, set] = {}
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            if var not in literal_polarity:
                literal_polarity[var] = set()
            literal_polarity[var].add(lit > 0)

    for var, polarities in literal_polarity.items():
        if len(polarities) == 1 and var not in assignment:
            value = next(iter(polarities))
            assignment[var] = value

    new_clauses = []
    for clause in clauses:
        clause_sat = False
        simplified = []
        for lit in clause:
            var = abs(lit)
            if var in assignment:
                if (lit > 0) == assignment[var]:
                    clause_sat = True
                    break
            else:
                simplified.append(lit)
        if not clause_sat:
            new_clauses.append(simplified)

    return assignment, new_clauses


def _dpll_recursive(
    clauses: List[List[int]],
    assignment: Dict[int, bool],
    num_vars: int,
    decision_steps: List[int],
) -> Tuple[bool, Dict[int, bool]]:
    success, assignment, clauses = _unit_propagation(clauses, assignment)
    if not success:
        return False, assignment

    assignment, clauses = _pure_literal_elimination(clauses, assignment, num_vars)

    if not clauses:
        for var in range(1, num_vars + 1):
            if var not in assignment:
                assignment[var] = True
        return True, assignment

    for clause in clauses:
        if not clause:
            return False, assignment

    chosen_var = None
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            if var not in assignment:
                chosen_var = var
                break
        if chosen_var:
            break

    if chosen_var is None:
        return True, assignment

    decision_steps[0] += 1

    for value in [True, False]:
        new_assignment = assignment.copy()
        new_assignment[chosen_var] = value
        new_clauses = [list(c) for c in clauses]
        success, final_assignment = _dpll_recursive(
            new_clauses, new_assignment, num_vars, decision_steps
        )
        if success:
            return True, final_assignment

    return False, assignment


def dpll_solve(cnf: CNF) -> DPLLResult:
    start_time = time.time()
    clauses = [list(c) for c in cnf.clauses]
    assignment: Dict[int, bool] = {}
    decision_steps = [0]

    sat, final_assignment = _dpll_recursive(
        clauses, assignment, cnf.num_vars, decision_steps
    )

    elapsed = time.time() - start_time

    if sat:
        for var in range(1, cnf.num_vars + 1):
            if var not in final_assignment:
                final_assignment[var] = True

    return DPLLResult(
        sat=sat,
        assignment=final_assignment if sat else None,
        decision_steps=decision_steps[0],
        time_seconds=elapsed,
        stats={"unit_propagations": decision_steps[0] * 2},
    )
