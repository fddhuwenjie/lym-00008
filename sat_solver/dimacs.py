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
