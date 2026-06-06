from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from .dimacs import WCNF


@dataclass
class WeightedGraph:
    num_vertices: int
    edges: List[Tuple[int, int]]
    vertex_weights: Dict[int, int]

    def validate(self) -> None:
        for v in range(1, self.num_vertices + 1):
            if v not in self.vertex_weights:
                raise ValueError(f"Vertex {v} missing weight")
            if self.vertex_weights[v] <= 0:
                raise ValueError(f"Vertex {v} has non-positive weight")
        for u, v in self.edges:
            if u < 1 or u > self.num_vertices or v < 1 or v > self.num_vertices:
                raise ValueError(f"Edge ({u}, {v}) references invalid vertex")


def encode_weighted_vertex_cover(graph: WeightedGraph) -> WCNF:
    graph.validate()

    total_soft_weight = sum(graph.vertex_weights.values())
    top = total_soft_weight + 1

    clauses: List[Tuple[int, List[int]]] = []

    for u, v in graph.edges:
        clauses.append((top, [u, v]))

    for vertex in range(1, graph.num_vertices + 1):
        weight = graph.vertex_weights[vertex]
        clauses.append((weight, [-vertex]))

    return WCNF(
        num_vars=graph.num_vertices,
        num_clauses=len(clauses),
        top=top,
        clauses=clauses,
        comments=[f"Weighted vertex cover: {graph.num_vertices} vertices, {len(graph.edges)} edges"],
    )


def decode_vertex_cover(assignment: Dict[int, bool], graph: WeightedGraph) -> Tuple[Set[int], int]:
    cover: Set[int] = set()
    total_weight = 0

    for vertex in range(1, graph.num_vertices + 1):
        if assignment.get(vertex, False):
            cover.add(vertex)
            total_weight += graph.vertex_weights[vertex]

    return cover, total_weight


def is_valid_vertex_cover(cover: Set[int], graph: WeightedGraph) -> bool:
    for u, v in graph.edges:
        if u not in cover and v not in cover:
            return False
    return True


def brute_force_min_vertex_cover(graph: WeightedGraph) -> Tuple[Set[int], int]:
    graph.validate()
    if graph.num_vertices > 20:
        raise ValueError("Graph too large for brute force (max 20 vertices)")

    best_cover: Optional[Set[int]] = None
    best_weight = float('inf')

    for mask in range(0, 1 << graph.num_vertices):
        cover: Set[int] = set()
        weight = 0
        for v in range(graph.num_vertices):
            if mask & (1 << v):
                vertex = v + 1
                cover.add(vertex)
                weight += graph.vertex_weights[vertex]

        if weight >= best_weight:
            continue

        if is_valid_vertex_cover(cover, graph):
            best_weight = weight
            best_cover = cover

    if best_cover is None:
        raise ValueError("No valid vertex cover found")

    return best_cover, best_weight
