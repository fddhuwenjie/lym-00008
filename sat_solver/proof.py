from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from .dimacs import CNF


@dataclass
class ProofVerificationResult:
    valid: bool
    step_results: List[bool]
    error_message: str = ""


def _clause_satisfied(clause: List[int], assignment: Dict[int, bool]) -> bool:
    for lit in clause:
        var = abs(lit)
        val = assignment.get(var)
        if val is None:
            continue
        if (lit > 0) == val:
            return True
    return False


def _resolution(
    clause1: List[int], clause2: List[int], pivot_var: int
) -> List[int]:
    lits1 = set(clause1)
    lits2 = set(clause2)

    lits1.discard(pivot_var)
    lits1.discard(-pivot_var)
    lits2.discard(pivot_var)
    lits2.discard(-pivot_var)

    result = lits1.union(lits2)
    return list(result)


def verify_proof(
    cnf: CNF, proof: List[List[int]]
) -> ProofVerificationResult:
    if not proof:
        return ProofVerificationResult(
            valid=False,
            step_results=[],
            error_message="Empty proof",
        )

    step_results = []
    known_clauses: List[List[int]] = [list(c) for c in cnf.clauses]
    known_clause_sets: List[Set[int]] = [set(c) for c in cnf.clauses]

    for step_idx, proof_clause in enumerate(proof):
        proof_set = set(proof_clause)
        found = False

        for known_set in known_clause_sets:
            if proof_set.issubset(known_set):
                found = True
                break

        if not found:
            for i, c1 in enumerate(known_clauses):
                for j, c2 in enumerate(known_clauses):
                    if i >= j:
                        continue
                    vars1 = {abs(l) for l in c1}
                    vars2 = {abs(l) for l in c2}
                    common_vars = vars1.intersection(vars2)

                    for pivot in common_vars:
                        if (pivot in c1 and -pivot in c2) or (-pivot in c1 and pivot in c2):
                            resolvent = _resolution(c1, c2, pivot)
                            if set(resolvent) == proof_set:
                                found = True
                                break
                    if found:
                        break
                if found:
                    break

        if found:
            step_results.append(True)
            known_clauses.append(list(proof_clause))
            known_clause_sets.append(set(proof_clause))
        else:
            step_results.append(False)
            return ProofVerificationResult(
                valid=False,
                step_results=step_results,
                error_message=f"Step {step_idx}: Cannot derive clause {proof_clause}",
            )

    has_empty = any(len(c) == 0 for c in proof)
    if not has_empty:
        return ProofVerificationResult(
            valid=False,
            step_results=step_results,
            error_message="Proof does not derive empty clause",
        )

    return ProofVerificationResult(
        valid=True,
        step_results=step_results,
        error_message="",
    )


def check_assignment(cnf: CNF, assignment: Dict[int, bool]) -> Tuple[bool, List[int]]:
    unsatisfied = []
    for idx, clause in enumerate(cnf.clauses):
        if not _clause_satisfied(clause, assignment):
            unsatisfied.append(idx)
    return len(unsatisfied) == 0, unsatisfied


def format_proof(proof: List[List[int]]) -> str:
    lines = []
    for i, clause in enumerate(proof):
        clause_str = " ".join(map(str, clause)) if clause else "0"
        lines.append(f"{i + 1}. {clause_str}")
    return "\n".join(lines)
