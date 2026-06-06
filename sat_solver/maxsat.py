from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import time
from .dimacs import WCNF, CNF, parse_wcnf
from .cdcl import CDCLSolver, CDCLResult


@dataclass
class MaxSATResult:
    optimal_weight: int
    assignment: Dict[int, bool]
    unsatisfied_soft_indices: List[int]
    time_seconds: float
    cores_found: int
    iterations: int
    status: str


class AssumptionCDCLSolver(CDCLSolver):
    def __init__(self, cnf: CNF, assumptions: List[int]):
        super().__init__(cnf, enable_proof=False)
        self.assumptions = assumptions
        self.assumption_set = set(abs(a) for a in assumptions)
        self.core: Set[int] = set()

    def _assign(self, lit: int, reason: Optional[List[int]] = None) -> None:
        super()._assign(lit, reason)

    def _analyze_conflict_with_core(self, conflict_clause: List[int]) -> Tuple[List[int], int, Set[int]]:
        current_clause = list(conflict_clause)
        core_lits: Set[int] = set()

        def get_level(lit: int) -> int:
            return self.vars[abs(lit)].decision_level

        def count_current_level(clause: List[int]) -> int:
            return sum(1 for l in clause if get_level(l) == self.decision_level)

        max_iterations = 1000
        iteration = 0
        while count_current_level(current_clause) > 1 and iteration < max_iterations:
            iteration += 1
            found = False
            for i in range(len(self.trail) - 1, -1, -1):
                lit = self.trail[i]
                var = abs(lit)
                neg_lit = -lit
                if neg_lit in current_clause and get_level(lit) == self.decision_level:
                    reason = self.vars[var].reason
                    if reason is not None:
                        resolvent = self._resolution(current_clause, reason, var)
                        current_clause = resolvent
                    found = True
                    break
            if not found:
                break

        for lit in current_clause:
            var = abs(lit)
            if var in self.assumption_set:
                core_lits.add(-lit)

        levels = [get_level(l) for l in current_clause]
        if not levels:
            return current_clause, -1, core_lits

        max_level = max(levels)
        if max_level == 0:
            return current_clause, -1, core_lits

        if len(current_clause) == 1:
            backtrack_level = 0
        else:
            other_levels = [get_level(l) for l in current_clause[:-1]]
            if other_levels:
                backtrack_level = max(other_levels)
            else:
                backtrack_level = 0

        return current_clause, backtrack_level, core_lits

    def solve_with_assumptions(self, max_conflicts: int = 100000, max_time: float = 30.0) -> Tuple[CDCLResult, Set[int]]:
        start_time = time.time()
        self.trail_lim.append(0)
        self.decision_level = 0

        for assumption in self.assumptions:
            var = abs(assumption)
            if self.vars[var].value is not None:
                if self._value(assumption) == False:
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=0,
                        time_seconds=time.time() - start_time,
                        conflicts=1,
                        restarts=0,
                        learnt_clauses=0,
                        proof=None,
                        stats={},
                    ), {assumption}
            else:
                self.trail_lim.append(len(self.trail))
                self.decision_level += 1
                self._assign(assumption, reason=None)

        for clause in self.clauses:
            if len(clause) == 1:
                lit = clause[0]
                if self._value(lit) == False:
                    _, _, core = self._analyze_conflict_with_core(clause)
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=0,
                        time_seconds=time.time() - start_time,
                        conflicts=1,
                        restarts=0,
                        learnt_clauses=0,
                        proof=None,
                        stats={},
                    ), core

        conflict = self._propagate()
        if conflict is not None:
            _, _, core = self._analyze_conflict_with_core(conflict)
            return CDCLResult(
                sat=False,
                assignment=None,
                decision_steps=0,
                time_seconds=time.time() - start_time,
                conflicts=self.conflicts,
                restarts=0,
                learnt_clauses=0,
                proof=None,
                stats={},
            ), core

        while self.conflicts < max_conflicts:
            elapsed = time.time() - start_time
            if elapsed > max_time:
                return CDCLResult(
                    sat=False,
                    assignment=None,
                    decision_steps=self.decisions,
                    time_seconds=elapsed,
                    conflicts=self.conflicts,
                    restarts=self.restarts,
                    learnt_clauses=self.learnt_count,
                    proof=None,
                    stats={"timeout": True},
                ), set()

            if self._check_restart():
                self._restart()
                for assumption in self.assumptions:
                    var = abs(assumption)
                    if self.vars[var].value is None:
                        self.trail_lim.append(len(self.trail))
                        self.decision_level += 1
                        self._assign(assumption, reason=None)
                conflict = self._propagate()
                if conflict is not None:
                    _, _, core = self._analyze_conflict_with_core(conflict)
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=None,
                        stats={},
                    ), core

            var = self._pick_branching_variable()
            if var is None:
                assignment = {}
                for v in range(1, self.num_vars + 1):
                    val = self.vars[v].value
                    assignment[v] = val if val is not None else True
                return CDCLResult(
                    sat=True,
                    assignment=assignment,
                    decision_steps=self.decisions,
                    time_seconds=time.time() - start_time,
                    conflicts=self.conflicts,
                    restarts=self.restarts,
                    learnt_clauses=self.learnt_count,
                    proof=None,
                    stats={},
                ), set()

            self.decisions += 1
            self.decision_level += 1
            self.trail_lim.append(len(self.trail))

            value = True
            self._assign(var if value else -var, reason=None)

            conflict_loop_count = 0
            max_conflict_loops = 1000

            while conflict_loop_count < max_conflict_loops:
                conflict_loop_count += 1
                conflict = self._propagate()
                if conflict is None:
                    break

                learnt_clause, backtrack_level, core = self._analyze_conflict_with_core(conflict)

                if backtrack_level < 0:
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=None,
                        stats={},
                    ), core

                ok = self._learn_clause(learnt_clause)
                if not ok:
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=None,
                        stats={},
                    ), core

                self._decay_activities()

                if backtrack_level < self.decision_level:
                    self._backtrack(backtrack_level)
                    if len(learnt_clause) > 0:
                        self._assign(learnt_clause[-1], reason=list(learnt_clause))
                    continue
                else:
                    target_level = max(0, backtrack_level)
                    self._backtrack(target_level)
                    if len(learnt_clause) > 0:
                        self._assign(learnt_clause[-1], reason=list(learnt_clause))
                    if self.decision_level > 0:
                        continue
                    else:
                        conflict = self._propagate()
                        if conflict is not None:
                            _, _, core = self._analyze_conflict_with_core(conflict)
                            return CDCLResult(
                                sat=False,
                                assignment=None,
                                decision_steps=self.decisions,
                                time_seconds=time.time() - start_time,
                                conflicts=self.conflicts,
                                restarts=self.restarts,
                                learnt_clauses=self.learnt_count,
                                proof=None,
                                stats={},
                            ), core
                        break

            if conflict_loop_count >= max_conflict_loops:
                return CDCLResult(
                    sat=False,
                    assignment=None,
                    decision_steps=self.decisions,
                    time_seconds=time.time() - start_time,
                    conflicts=self.conflicts,
                    restarts=self.restarts,
                    learnt_clauses=self.learnt_count,
                    proof=None,
                    stats={"conflict_loop_limit": True},
                ), set()

        return CDCLResult(
            sat=False,
            assignment=None,
            decision_steps=self.decisions,
            time_seconds=time.time() - start_time,
            conflicts=self.conflicts,
            restarts=self.restarts,
            learnt_clauses=self.learnt_count,
            proof=None,
            stats={"conflict_limit": True},
        ), set()


def oll_maxsat_solve(wcnf: WCNF, max_time: float = 60.0) -> MaxSATResult:
    start_time = time.time()

    cnf, assumption_vars, soft_indices = wcnf.to_cnf_with_assumptions()

    soft_weights = {}
    for i, idx in enumerate(soft_indices):
        soft_weights[assumption_vars[i]] = wcnf.clauses[idx][0]

    soft_var_to_clause_idx = {}
    for i, idx in enumerate(soft_indices):
        soft_var_to_clause_idx[assumption_vars[i]] = idx

    original_to_current = {}
    for var in assumption_vars:
        original_to_current[var] = var

    current_to_original = {}
    for var in assumption_vars:
        current_to_original[var] = var

    working_cnf = CNF(
        num_vars=cnf.num_vars,
        num_clauses=cnf.num_clauses,
        clauses=[list(c) for c in cnf.clauses],
        comments=cnf.comments,
    )

    current_assumptions = set(assumption_vars)
    next_var = working_cnf.num_vars + 1

    cores_found = 0
    iterations = 0
    max_iterations = 10000

    while iterations < max_iterations:
        iterations += 1
        elapsed = time.time() - start_time
        if elapsed > max_time:
            return MaxSATResult(
                optimal_weight=0,
                assignment={},
                unsatisfied_soft_indices=[],
                time_seconds=elapsed,
                cores_found=cores_found,
                iterations=iterations,
                status="timeout",
            )

        assumptions_list = sorted(list(current_assumptions))
        solver = AssumptionCDCLSolver(working_cnf, assumptions_list)
        result, core = solver.solve_with_assumptions(max_time=max_time - elapsed)

        if result.sat and result.assignment:
            optimal_weight = 0
            unsatisfied = []

            for orig_var in assumption_vars:
                clause_idx = soft_var_to_clause_idx[orig_var]
                current_var = original_to_current[orig_var]
                if result.assignment.get(current_var, False):
                    optimal_weight += soft_weights[orig_var]
                else:
                    unsatisfied.append(clause_idx)

            original_assignment = {}
            for v in range(1, wcnf.num_vars + 1):
                original_assignment[v] = result.assignment.get(v, True)

            return MaxSATResult(
                optimal_weight=optimal_weight,
                assignment=original_assignment,
                unsatisfied_soft_indices=sorted(unsatisfied),
                time_seconds=time.time() - start_time,
                cores_found=cores_found,
                iterations=iterations,
                status="optimal",
            )

        if not core:
            return MaxSATResult(
                optimal_weight=0,
                assignment={},
                unsatisfied_soft_indices=[],
                time_seconds=time.time() - start_time,
                cores_found=cores_found,
                iterations=iterations,
                status="unknown",
            )

        cores_found += 1

        core_vars = sorted(list(core))
        relaxation_vars = []

        for core_var in core_vars:
            r_var = next_var
            next_var += 1
            relaxation_vars.append(r_var)

            working_cnf.clauses.append([-core_var, r_var])
            working_cnf.clauses.append([-r_var, core_var])

            orig_var = current_to_original[core_var]
            original_to_current[orig_var] = r_var
            current_to_original[r_var] = orig_var

            current_assumptions.discard(core_var)

        at_least_one_false = [-r for r in relaxation_vars]
        working_cnf.clauses.append(at_least_one_false)

        working_cnf.num_vars = next_var - 1
        working_cnf.num_clauses = len(working_cnf.clauses)

        for r_var in relaxation_vars:
            current_assumptions.add(r_var)

    return MaxSATResult(
        optimal_weight=0,
        assignment={},
        unsatisfied_soft_indices=[],
        time_seconds=time.time() - start_time,
        cores_found=cores_found,
        iterations=iterations,
        status="iteration_limit",
    )


def maxsat_solve_from_wcnf(wcnf_text: str, max_time: float = 60.0) -> MaxSATResult:
    wcnf = parse_wcnf(wcnf_text)
    return oll_maxsat_solve(wcnf, max_time=max_time)


def maxsat_solve_from_clauses(
    weighted_clauses: List[Tuple[int, List[int]]],
    num_vars: int,
    top: Optional[int] = None,
    max_time: float = 60.0,
) -> MaxSATResult:
    if top is None:
        max_weight = max(w for w, _ in weighted_clauses)
        top = sum(w for w, _ in weighted_clauses if w < max_weight * 1000) + 1

    wcnf = WCNF(
        num_vars=num_vars,
        num_clauses=len(weighted_clauses),
        top=top,
        clauses=weighted_clauses,
        comments=[],
    )
    return oll_maxsat_solve(wcnf, max_time=max_time)


def brute_force_maxsat(wcnf: WCNF) -> Tuple[int, Dict[int, bool], List[int]]:
    if wcnf.num_vars > 20:
        raise ValueError("Too many variables for brute force (max 20)")

    best_weight = -1
    best_assignment: Dict[int, bool] = {}
    best_unsatisfied: List[int] = []

    for mask in range(0, 1 << wcnf.num_vars):
        assignment = {}
        for v in range(wcnf.num_vars):
            assignment[v + 1] = bool(mask & (1 << v))

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
                    break
            else:
                if clause_sat:
                    soft_weight += weight
                else:
                    unsatisfied.append(idx)

        if not hard_satisfied:
            continue

        if soft_weight > best_weight:
            best_weight = soft_weight
            best_assignment = dict(assignment)
            best_unsatisfied = list(unsatisfied)

    return best_weight, best_assignment, sorted(best_unsatisfied)
