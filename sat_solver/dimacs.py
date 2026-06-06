from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CNF:
    num_vars: int
    num_clauses: int
    clauses: List[List[int]]
    comments: List[str]

    def to_dimacs(self) -> str:
        lines = []
        for comment in self.comments:
            lines.append(f"c {comment}")
        lines.append(f"p cnf {self.num_vars} {self.num_clauses}")
        for clause in self.clauses:
            lines.append(" ".join(map(str, clause)) + " 0")
        return "\n".join(lines) + "\n"


@dataclass
class WCNF:
    num_vars: int
    num_clauses: int
    top: int
    clauses: List[Tuple[int, List[int]]]
    comments: List[str]

    def is_hard(self, idx: int) -> bool:
        return self.clauses[idx][0] >= self.top

    def to_wcnf(self) -> str:
        lines = []
        for comment in self.comments:
            lines.append(f"c {comment}")
        lines.append(f"p wcnf {self.num_vars} {self.num_clauses} {self.top}")
        for weight, literals in self.clauses:
            lines.append(f"{weight} {' '.join(map(str, literals))} 0")
        return "\n".join(lines) + "\n"

    def to_cnf_with_assumptions(self) -> Tuple[CNF, List[int], List[int]]:
        new_clauses = []
        assumption_vars = []
        var_counter = self.num_vars + 1
        soft_clause_indices = []

        for idx, (weight, literals) in enumerate(self.clauses):
            if weight >= self.top:
                new_clauses.append(list(literals))
            else:
                new_assumption = var_counter
                var_counter += 1
                new_clause = [-new_assumption] + list(literals)
                new_clauses.append(new_clause)
                assumption_vars.append(new_assumption)
                soft_clause_indices.append(idx)

        return (
            CNF(
                num_vars=var_counter - 1,
                num_clauses=len(new_clauses),
                clauses=new_clauses,
                comments=self.comments,
            ),
            assumption_vars,
            soft_clause_indices,
        )


def parse_dimacs(input_str: str) -> CNF:
    lines = input_str.strip().split("\n")
    comments = []
    clauses = []
    num_vars = 0
    num_clauses = 0
    header_found = False
    current_clause = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("c"):
            comments.append(line[1:].strip())
            continue

        if line.startswith("p"):
            if header_found:
                raise ValueError("Multiple header lines found")
            parts = line.split()
            if len(parts) != 4 or parts[1] != "cnf":
                raise ValueError(f"Invalid header: {line}")
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            header_found = True
            continue

        if not header_found:
            continue

        parts = line.split()
        for part in parts:
            lit = int(part)
            if lit == 0:
                if current_clause:
                    clauses.append(current_clause)
                    current_clause = []
            else:
                current_clause.append(lit)

    if current_clause:
        clauses.append(current_clause)

    if len(clauses) != num_clauses:
        raise ValueError(
            f"Clause count mismatch: expected {num_clauses}, got {len(clauses)}"
        )

    return CNF(
        num_vars=num_vars,
        num_clauses=num_clauses,
        clauses=clauses,
        comments=comments,
    )


def parse_dimacs_file(filepath: str) -> CNF:
    with open(filepath, "r") as f:
        return parse_dimacs(f.read())


def parse_wcnf(input_str: str) -> WCNF:
    lines = input_str.strip().split("\n")
    comments = []
    clauses = []
    num_vars = 0
    num_clauses = 0
    top = 0
    header_found = False
    current_weight = None
    current_clause = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("c"):
            comments.append(line[1:].strip())
            continue

        if line.startswith("p"):
            if header_found:
                raise ValueError("Multiple header lines found")
            parts = line.split()
            if len(parts) != 5 or parts[1] != "wcnf":
                raise ValueError(f"Invalid WCNF header: {line}")
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            top = int(parts[4])
            header_found = True
            continue

        if not header_found:
            continue

        parts = line.split()
        for part in parts:
            lit = int(part)
            if current_weight is None:
                current_weight = lit
            elif lit == 0:
                if current_clause:
                    clauses.append((current_weight, current_clause))
                    current_clause = []
                current_weight = None
            else:
                current_clause.append(lit)

    if current_weight is not None and current_clause:
        clauses.append((current_weight, current_clause))

    if len(clauses) != num_clauses:
        raise ValueError(
            f"Clause count mismatch: expected {num_clauses}, got {len(clauses)}"
        )

    return WCNF(
        num_vars=num_vars,
        num_clauses=num_clauses,
        top=top,
        clauses=clauses,
        comments=comments,
    )


def parse_wcnf_file(filepath: str) -> WCNF:
    with open(filepath, "r") as f:
        return parse_wcnf(f.read())
