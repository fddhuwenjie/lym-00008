from typing import List, Dict, Optional, Tuple
from .dimacs import CNF


def _var_index(row: int, col: int, val: int, size: int = 9) -> int:
    return row * size * size + col * size + val + 1


def _decode_var(var: int, size: int = 9) -> Tuple[int, int, int]:
    var -= 1
    val = var % size
    col = (var // size) % size
    row = var // (size * size)
    return row, col, val


def encode_sudoku(
    puzzle: List[List[Optional[int]]], size: int = 9
) -> CNF:
    box_size = int(size ** 0.5)
    num_vars = size * size * size
    clauses: List[List[int]] = []

    for r in range(size):
        for c in range(size):
            cell_clause = [_var_index(r, c, v, size) for v in range(size)]
            clauses.append(cell_clause)
            for v1 in range(size):
                for v2 in range(v1 + 1, size):
                    clauses.append([
                        -_var_index(r, c, v1, size),
                        -_var_index(r, c, v2, size),
                    ])

    for r in range(size):
        for v in range(size):
            row_clause = [_var_index(r, c, v, size) for c in range(size)]
            clauses.append(row_clause)
            for c1 in range(size):
                for c2 in range(c1 + 1, size):
                    clauses.append([
                        -_var_index(r, c1, v, size),
                        -_var_index(r, c2, v, size),
                    ])

    for c in range(size):
        for v in range(size):
            col_clause = [_var_index(r, c, v, size) for r in range(size)]
            clauses.append(col_clause)
            for r1 in range(size):
                for r2 in range(r1 + 1, size):
                    clauses.append([
                        -_var_index(r1, c, v, size),
                        -_var_index(r2, c, v, size),
                    ])

    for br in range(box_size):
        for bc in range(box_size):
            for v in range(size):
                box_clause = []
                for dr in range(box_size):
                    for dc in range(box_size):
                        r = br * box_size + dr
                        c = bc * box_size + dc
                        box_clause.append(_var_index(r, c, v, size))
                clauses.append(box_clause)

                cells = []
                for dr in range(box_size):
                    for dc in range(box_size):
                        r = br * box_size + dr
                        c = bc * box_size + dc
                        cells.append((r, c))
                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        clauses.append([
                            -_var_index(r1, c1, v, size),
                            -_var_index(r2, c2, v, size),
                        ])

    for r in range(size):
        for c in range(size):
            val = puzzle[r][c]
            if val is not None and val > 0:
                v = val - 1
                clauses.append([_var_index(r, c, v, size)])

    comments = [
        f"Sudoku puzzle encoding",
        f"Size: {size}x{size}",
        f"Box size: {box_size}x{box_size}",
    ]

    return CNF(
        num_vars=num_vars,
        num_clauses=len(clauses),
        clauses=clauses,
        comments=comments,
    )


def decode_sudoku(
    assignment: Dict[int, bool],
    size: int = 9,
) -> List[List[int]]:
    grid = [[0 for _ in range(size)] for _ in range(size)]

    for var, value in assignment.items():
        if value:
            row, col, val = _decode_var(var, size)
            grid[row][col] = val + 1

    return grid


def parse_sudoku_string(s: str, size: int = 9) -> List[List[Optional[int]]]:
    puzzle: List[List[Optional[int]]] = []
    idx = 0
    for r in range(size):
        row = []
        for c in range(size):
            if idx < len(s):
                ch = s[idx]
                if ch.isdigit() and ch != '0':
                    row.append(int(ch))
                else:
                    row.append(None)
                idx += 1
            else:
                row.append(None)
        puzzle.append(row)
    return puzzle


def sudoku_to_string(grid: List[List[int]]) -> str:
    return "".join(str(val) for row in grid for val in row)


def format_sudoku(grid: List[List[int]], size: int = 9) -> str:
    box_size = int(size ** 0.5)
    lines = []
    for r in range(size):
        if r > 0 and r % box_size == 0:
            lines.append("-" * (size * 2 + box_size * 2 - 1))
        row_chars = []
        for c in range(size):
            if c > 0 and c % box_size == 0:
                row_chars.append("|")
            val = grid[r][c]
            row_chars.append(str(val) if val > 0 else ".")
        lines.append(" ".join(row_chars))
    return "\n".join(lines)


SUDOKU_PUZZLES = {
    "easy": "530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    "medium": "000000000009805100051907420290401065000000000140508093026709580005103600000000000",
    "hard": "800000000003600000070090200050007000000045700000100030001000068008500010090000400",
    "expert": "000000012000035000000600070700000300000400800100000000000120000080000040050000600",
}
