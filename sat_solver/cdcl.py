from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import time
import random
from .dimacs import CNF


@dataclass
class VariableInfo:
    value: Optional[bool] = None
    decision_level: int = -1
    reason: Optional[List[int]] = None
    activity: float = 0.0


@dataclass
class CDCLResult:
    sat: bool
    assignment: Optional[Dict[int, bool]]
    decision_steps: int
    time_seconds: float
    conflicts: int
    restarts: int
    learnt_clauses: int
    proof: Optional[List[List[int]]] = None
    stats: Dict = field(default_factory=dict)


class CDCLSolver:
    def __init__(self, cnf: CNF, enable_proof: bool = False):
        self.num_vars = cnf.num_vars
        self.clauses: List[List[int]] = []
        self.original_clauses: List[List[int]] = []
        self.vars: Dict[int, VariableInfo] = {}
        self.trail: List[int] = []
        self.trail_lim: List[int] = []
        self.decision_level = 0
        self.decisions = 0
        self.conflicts = 0
        self.restarts = 0
        self.learnt_count = 0
        self.enable_proof = enable_proof
        self.proof: List[List[int]] = []
        self.learnt_set: Set[str] = set()

        for var in range(1, self.num_vars + 1):
            self.vars[var] = VariableInfo()

        for clause_lits in cnf.clauses:
            self.clauses.append(list(clause_lits))
            self.original_clauses.append(list(clause_lits))

        self.vsids_inc = 1.0
        self.vsids_decay = 0.95

    def _value(self, lit: int) -> Optional[bool]:
        var = abs(lit)
        val = self.vars[var].value
        if val is None:
            return None
        return val if lit > 0 else not val

    def _assign(self, lit: int, reason: Optional[List[int]] = None) -> None:
        var = abs(lit)
        if self.vars[var].value is not None:
            return
        self.vars[var].value = lit > 0
        self.vars[var].decision_level = self.decision_level
        self.vars[var].reason = reason
        self.trail.append(lit)
        self._bump_activity(var)

    def _unassign(self, var: int) -> None:
        self.vars[var].value = None
        self.vars[var].decision_level = -1
        self.vars[var].reason = None

    def _bump_activity(self, var: int) -> None:
        self.vars[var].activity += self.vsids_inc
        if self.vars[var].activity > 1e100:
            for v in range(1, self.num_vars + 1):
                self.vars[v].activity *= 1e-100
            self.vsids_inc *= 1e-100

    def _decay_activities(self) -> None:
        self.vsids_inc *= (1.0 / self.vsids_decay)

    def _pick_branching_variable(self) -> Optional[int]:
        best_var = None
        best_activity = -1.0
        for var in range(1, self.num_vars + 1):
            if self.vars[var].value is None:
                if self.vars[var].activity > best_activity:
                    best_activity = self.vars[var].activity
                    best_var = var
        return best_var

    def _clause_status(self, clause: List[int]) -> Tuple[Optional[bool], List[int], Optional[int]]:
        unassigned = []
        for lit in clause:
            val = self._value(lit)
            if val == True:
                return True, [], None
            elif val is None:
                unassigned.append(lit)
        if not unassigned:
            return False, [], None
        if len(unassigned) == 1:
            return None, unassigned, unassigned[0]
        return None, unassigned, None

    def _propagate(self) -> Optional[List[int]]:
        changed = True
        while changed:
            changed = False
            for clause in self.clauses:
                sat, unassigned, unit_lit = self._clause_status(clause)
                if sat:
                    continue
                if not unassigned:
                    self.conflicts += 1
                    return clause
                if unit_lit is not None:
                    var = abs(unit_lit)
                    if self.vars[var].value is None:
                        self._assign(unit_lit, reason=list(clause))
                        changed = True
                    elif self._value(unit_lit) == False:
                        self.conflicts += 1
                        return clause
        return None

    def _analyze_conflict(self, conflict_clause: List[int]) -> Tuple[List[int], int]:
        seen: Set[int] = set()
        learnt_clause: List[int] = list(conflict_clause)
        backtrack_level = 0

        def get_level(lit: int) -> int:
            return self.vars[abs(lit)].decision_level

        def count_current_level(clause: List[int]) -> int:
            return sum(1 for l in clause if get_level(l) == self.decision_level)

        while count_current_level(learnt_clause) > 1:
            found = False
            for i in range(len(self.trail) - 1, -1, -1):
                lit = self.trail[i]
                var = abs(lit)
                neg_lit = -lit
                if neg_lit in learnt_clause and get_level(lit) == self.decision_level:
                    reason = self.vars[var].reason
                    if reason is not None:
                        new_clause: List[int] = []
                        for l in learnt_clause:
                            if l != neg_lit:
                                new_clause.append(l)
                        for l in reason:
                            if l != lit and l not in new_clause:
                                new_clause.append(l)
                        learnt_clause = new_clause
                    else:
                        pass
                    found = True
                    break
            if not found:
                break

        if len(learnt_clause) >= 2:
            current_level_lits = [l for l in learnt_clause if get_level(l) == self.decision_level]
            if len(current_level_lits) > 0:
                last = current_level_lits[-1]
                learnt_clause.remove(last)
                learnt_clause.append(last)

        levels = [get_level(l) for l in learnt_clause]
        if not levels:
            return learnt_clause, -1

        max_level = max(levels)
        if max_level == 0:
            return learnt_clause, -1

        second_max_level = 0
        for l in learnt_clause[:-1]:
            level = get_level(l)
            if level > second_max_level and level < max_level:
                second_max_level = level

        if second_max_level == 0 and len(learnt_clause) > 1:
            for l in learnt_clause[:-1]:
                level = get_level(l)
                if level > second_max_level:
                    second_max_level = level

        backtrack_level = second_max_level if second_max_level > 0 else 0

        return learnt_clause, backtrack_level

    def _learn_clause(self, clause: List[int]) -> bool:
        if len(clause) == 0:
            return False

        key = str(sorted(clause, key=lambda x: (abs(x), x)))
        if key in self.learnt_set:
            return True

        self.learnt_set.add(key)
        self.clauses.append(list(clause))
        self.learnt_count += 1
        if self.enable_proof:
            self.proof.append(list(clause))

        for lit in clause:
            self._bump_activity(abs(lit))

        return True

    def _backtrack(self, level: int) -> None:
        if level < 0:
            level = 0

        while len(self.trail_lim) > level + 1:
            self.trail_lim.pop()

        target_len = self.trail_lim[-1] if self.trail_lim else 0
        while len(self.trail) > target_len:
            lit = self.trail.pop()
            self._unassign(abs(lit))

        self.decision_level = level

    def _check_restart(self) -> bool:
        if self.conflicts > 0 and self.conflicts % 500 == 0:
            return True
        return False

    def _restart(self) -> None:
        self.restarts += 1
        while len(self.trail) > 0:
            lit = self.trail.pop()
            self._unassign(abs(lit))
        self.trail_lim = []
        self.decision_level = 0

        if len(self.clauses) > len(self.original_clauses) + 2000:
            kept = self.original_clauses[:]
            new_learnt_set = set()
            for c in self.clauses[len(self.original_clauses):]:
                if len(c) <= 10:
                    key = str(sorted(c, key=lambda x: (abs(x), x)))
                    if key not in new_learnt_set:
                        new_learnt_set.add(key)
                        kept.append(c)
                if len(kept) >= len(self.original_clauses) + 1000:
                    break
            self.clauses = kept
            self.learnt_set = new_learnt_set
            self.learnt_count = len(self.clauses) - len(self.original_clauses)

    def solve(self, max_conflicts: int = 100000, max_time: float = 30.0) -> CDCLResult:
        start_time = time.time()
        self.trail_lim.append(0)

        for clause in self.clauses:
            if len(clause) == 1:
                lit = clause[0]
                if self._value(lit) == False:
                    if self.enable_proof:
                        self.proof.append(list(clause))
                        self.proof.append([])
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=0,
                        time_seconds=time.time() - start_time,
                        conflicts=1,
                        restarts=0,
                        learnt_clauses=0,
                        proof=self.proof if self.enable_proof else None,
                        stats={},
                    )

        conflict = self._propagate()
        if conflict is not None:
            if self.enable_proof:
                self.proof.append(list(conflict))
                self.proof.append([])
            return CDCLResult(
                sat=False,
                assignment=None,
                decision_steps=0,
                time_seconds=time.time() - start_time,
                conflicts=self.conflicts,
                restarts=0,
                learnt_clauses=0,
                proof=self.proof if self.enable_proof else None,
                stats={},
            )

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
                    proof=self.proof if self.enable_proof else None,
                    stats={"timeout": True},
                )

            if self._check_restart():
                self._restart()
                conflict = self._propagate()
                if conflict is not None:
                    if self.enable_proof:
                        self.proof.append(list(conflict))
                        self.proof.append([])
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=self.proof if self.enable_proof else None,
                        stats={},
                    )

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
                )

            self.decisions += 1
            self.decision_level += 1
            self.trail_lim.append(len(self.trail))

            value = True
            self._assign(var if value else -var, reason=None)

            while True:
                conflict = self._propagate()
                if conflict is None:
                    break

                learnt_clause, backtrack_level = self._analyze_conflict(conflict)

                if backtrack_level < 0:
                    if self.enable_proof:
                        self.proof.append(list(conflict))
                        self.proof.append([])
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=self.proof if self.enable_proof else None,
                        stats={},
                    )

                ok = self._learn_clause(learnt_clause)
                if not ok:
                    if self.enable_proof:
                        self.proof.append(list(conflict))
                        self.proof.append([])
                    return CDCLResult(
                        sat=False,
                        assignment=None,
                        decision_steps=self.decisions,
                        time_seconds=time.time() - start_time,
                        conflicts=self.conflicts,
                        restarts=self.restarts,
                        learnt_clauses=self.learnt_count,
                        proof=self.proof if self.enable_proof else None,
                        stats={},
                    )

                self._decay_activities()

                if backtrack_level < self.decision_level:
                    self._backtrack(backtrack_level)
                    if len(learnt_clause) > 0:
                        self._assign(learnt_clause[-1], reason=list(learnt_clause))
                    continue
                else:
                    self._backtrack(max(0, self.decision_level - 1))
                    break

        return CDCLResult(
            sat=False,
            assignment=None,
            decision_steps=self.decisions,
            time_seconds=time.time() - start_time,
            conflicts=self.conflicts,
            restarts=self.restarts,
            learnt_clauses=self.learnt_count,
            proof=self.proof if self.enable_proof else None,
            stats={"conflict_limit": True},
        )


def cdcl_solve(cnf: CNF, enable_proof: bool = False) -> CDCLResult:
    solver = CDCLSolver(cnf, enable_proof=enable_proof)
    return solver.solve()
