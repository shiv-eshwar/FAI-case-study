"""Reservations use vertex ticks and directed edges indexed by departure tick."""

from dataclasses import dataclass, field

from .models import Cell


@dataclass
class Reservations:
    vertices: set[tuple[Cell, int]] = field(default_factory=set)
    edges: set[tuple[Cell, Cell, int]] = field(default_factory=set)
    permanent: dict[Cell, int] = field(default_factory=dict)
    last_visit: dict[Cell, int] = field(default_factory=dict)

    def vertex_blocked(self, p, t):
        return (p, t) in self.vertices or t >= self.permanent.get(p, float("inf"))

    def reverse_edge(self, p, q, t):
        return (q, p, t) in self.edges

    def can_hold(self, p, arrival):
        # Any permanent use, even starting later, prevents indefinite holding.
        return p not in self.permanent and self.last_visit.get(p, -1) < arrival

    def reserve(self, path):
        for t, p in enumerate(path):
            self.vertices.add((p, t))
            self.last_visit[p] = max(t, self.last_visit.get(p, -1))
            if t:
                self.edges.add((path[t - 1], p, t - 1))
        self.permanent[path[-1]] = len(path) - 1
