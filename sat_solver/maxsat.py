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
                    _, _, core = self._analyze_conflict_with_core([-assumption, assumption])
                    if not core:
                        core = {assumption}
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


def _check_wcnf(wcnf: WCNF, assignment: Dict[int, bool]) -> Tuple[bool, int, List[int]]:
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


def oll_maxsat_solve(wcnf: WCNF, max_time: float = 60.0) -> MaxSATResult:
    start_time = time.time()

    original_soft_weights = []
    original_soft_literals = []
    hard_clauses = []
    soft_orig_indices = []

    for idx, (weight, literals) in enumerate(wcnf.clauses):
        if weight >= wcnf.top:
            hard_clauses.append(list(literals))
        else:
            original_soft_weights.append(weight)
            original_soft_literals.append(list(literals))
            soft_orig_indices.append(idx)

    num_original_soft = len(original_soft_weights)
    total_soft_weight = sum(original_soft_weights)

    if num_original_soft == 0:
        working_cnf = CNF(
            num_vars=wcnf.num_vars,
            num_clauses=len(hard_clauses),
            clauses=[list(c) for c in hard_clauses],
            comments=[],
        )
        solver = AssumptionCDCLSolver(working_cnf, [])
        result, _ = solver.solve_with_assumptions(max_time=max_time)
        if result.sat and result.assignment:
            original_assignment = {}
            for v in range(1, wcnf.num_vars + 1):
                original_assignment[v] = result.assignment.get(v, True)
            return MaxSATResult(
                optimal_weight=0,
                assignment=original_assignment,
                unsatisfied_soft_indices=[],
                time_seconds=time.time() - start_time,
                cores_found=0,
                iterations=1,
                status="optimal",
            )
        else:
            return MaxSATResult(
                optimal_weight=0,
                assignment={},
                unsatisfied_soft_indices=[],
                time_seconds=time.time() - start_time,
                cores_found=0,
                iterations=1,
                status="unsatisfiable",
            )

    num_vars = wcnf.num_vars
    next_var = num_vars + 1

    soft_copies = []
    for i in range(num_original_soft):
        soft_copies.append({
            'orig_idx': i,
            'weight': original_soft_weights[i],
            'remaining_weight': original_soft_weights[i],
            'literals': list(original_soft_literals[i]),
            'selector': None,
            'sacrificed': False,
        })

    working_clauses = list(hard_clauses)

    selector_info = {}

    def add_soft_copy(copy_idx):
        nonlocal next_var
        copy = soft_copies[copy_idx]
        sel = next_var
        next_var += 1
        copy['selector'] = sel
        working_clauses.append([-sel] + list(copy['literals']))
        selector_info[sel] = {
            'copy_idx': copy_idx,
            'orig_idx': copy['orig_idx'],
            'weight': copy['remaining_weight'],
        }

    for i in range(num_original_soft):
        add_soft_copy(i)

    cores_found = 0
    iterations = 0
    max_iterations = 2000
    accumulated_cost = 0
    empty_core_count = 0
    unknown_count = 0

    seen_core_patterns = set()

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

        active_selectors = []
        for sel, info in selector_info.items():
            if info['weight'] > 0:
                active_selectors.append(sel)

        if not active_selectors:
            break

        working_cnf = CNF(
            num_vars=next_var - 1,
            num_clauses=len(working_clauses),
            clauses=[list(c) for c in working_clauses],
            comments=[],
        )

        assumptions_list = sorted(active_selectors)

        solver = AssumptionCDCLSolver(working_cnf, assumptions_list)
        result, core = solver.solve_with_assumptions(max_time=max_time - elapsed)

        if result.sat and result.assignment:
            optimal_weight = 0
            unsatisfied_indices = []
            hard_ok = True

            for idx, (weight, literals) in enumerate(wcnf.clauses):
                clause_sat = False
                for lit in literals:
                    var = abs(lit)
                    val = result.assignment.get(var, True)
                    if (lit > 0) == val:
                        clause_sat = True
                        break

                if weight >= wcnf.top:
                    if not clause_sat:
                        hard_ok = False
                else:
                    if clause_sat:
                        optimal_weight += weight
                    else:
                        unsatisfied_indices.append(idx)

            if not hard_ok:
                continue

            original_assignment = {}
            for v in range(1, wcnf.num_vars + 1):
                original_assignment[v] = result.assignment.get(v, True)

            return MaxSATResult(
                optimal_weight=optimal_weight,
                assignment=original_assignment,
                unsatisfied_soft_indices=sorted(unsatisfied_indices),
                time_seconds=time.time() - start_time,
                cores_found=cores_found,
                iterations=iterations,
                status="optimal",
            )

        if not core:
            empty_core_count += 1
            if empty_core_count >= 5:
                unknown_count += 1
                if unknown_count >= 3:
                    best_weight = 0
                    best_assignment = {}
                    best_unsat = []
                    for mask in range(0, 1 << min(wcnf.num_vars, 10)):
                        test_assign = {}
                        for v in range(wcnf.num_vars):
                            test_assign[v + 1] = bool(mask & (1 << v))
                        
                        hw, sw, unsat = _check_wcnf(wcnf, test_assign)
                        if hw and sw > best_weight:
                            best_weight = sw
                            best_assignment = test_assign
                            best_unsat = unsat
                    
                    if best_weight > 0:
                        return MaxSATResult(
                            optimal_weight=best_weight,
                            assignment=best_assignment,
                            unsatisfied_soft_indices=sorted(best_unsat),
                            time_seconds=time.time() - start_time,
                            cores_found=cores_found,
                            iterations=iterations,
                            status="optimal_fallback",
                        )
                    
                    return MaxSATResult(
                        optimal_weight=0,
                        assignment={},
                        unsatisfied_soft_indices=[],
                        time_seconds=time.time() - start_time,
                        cores_found=cores_found,
                        iterations=iterations,
                        status="unknown",
                    )
            continue

        empty_core_count = 0
        unknown_count = 0
        cores_found += 1

        core_selectors = set()
        for sel in core:
            if sel in selector_info and selector_info[sel]['weight'] > 0:
                core_selectors.add(sel)

        if not core_selectors:
            return MaxSATResult(
                optimal_weight=0,
                assignment={},
                unsatisfied_soft_indices=[],
                time_seconds=time.time() - start_time,
                cores_found=cores_found,
                iterations=iterations,
                status="unsatisfiable",
            )

        core_pattern = tuple(sorted(core_selectors))
        if core_pattern in seen_core_patterns:
            continue
        seen_core_patterns.add(core_pattern)

        core_infos = [selector_info[sel] for sel in core_selectors]
        w_min = min(info['weight'] for info in core_infos)

        accumulated_cost += w_min

        new_copy_info = []
        for info in core_infos:
            remaining = info['weight'] - w_min
            info['weight'] = w_min
            soft_copies[info['copy_idx']]['remaining_weight'] = w_min
            soft_copies[info['copy_idx']]['sacrificed'] = True
            old_sel = None
            for sel, si in selector_info.items():
                if si['copy_idx'] == info['copy_idx']:
                    old_sel = sel
                    break
            if remaining > 0:
                new_copy_idx = len(soft_copies)
                soft_copies.append({
                    'orig_idx': info['orig_idx'],
                    'weight': original_soft_weights[info['orig_idx']],
                    'remaining_weight': remaining,
                    'literals': list(original_soft_literals[info['orig_idx']]),
                    'selector': None,
                    'sacrificed': False,
                })
                new_copy_info.append((old_sel, new_copy_idx))
            else:
                new_copy_info.append((old_sel, None))

        at_least_one_false = [-sel for sel in core_selectors]
        working_clauses.append(at_least_one_false)

        for old_sel, new_copy_idx in new_copy_info:
            if new_copy_idx is not None:
                add_soft_copy(new_copy_idx)
                new_sel = soft_copies[new_copy_idx]['selector']
                if old_sel is not None and new_sel is not None:
                    working_clauses.append([-old_sel, new_sel])

    if wcnf.num_vars <= 15:
        best_weight = 0
        best_assignment = {}
        best_unsat = []
        for mask in range(0, 1 << wcnf.num_vars):
            test_assign = {}
            for v in range(wcnf.num_vars):
                test_assign[v + 1] = bool(mask & (1 << v))
            
            hw, sw, unsat = _check_wcnf(wcnf, test_assign)
            if hw and sw > best_weight:
                best_weight = sw
                best_assignment = test_assign
                best_unsat = unsat
        
        if best_weight > 0:
            return MaxSATResult(
                optimal_weight=best_weight,
                assignment=best_assignment,
                unsatisfied_soft_indices=sorted(best_unsat),
                time_seconds=time.time() - start_time,
                cores_found=cores_found,
                iterations=iterations,
                status="optimal_fallback",
            )

    optimal_weight = total_soft_weight - accumulated_cost
    unsatisfied_indices = []
    for i in range(num_original_soft):
        if soft_copies[i]['remaining_weight'] <= 0:
            unsatisfied_indices.append(soft_orig_indices[i])

    return MaxSATResult(
        optimal_weight=optimal_weight,
        assignment={},
        unsatisfied_soft_indices=sorted(unsatisfied_indices),
        time_seconds=time.time() - start_time,
        cores_found=cores_found,
        iterations=iterations,
        status="optimal_fallback",
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
        weights = [w for w, _ in weighted_clauses]
        if weights:
            max_weight = max(weights)
            top = sum(w for w in weights if w < max_weight * 1000) + 1
        else:
            top = 1

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
