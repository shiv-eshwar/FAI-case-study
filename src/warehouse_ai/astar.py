"""Spatial A* and bounded space-time A*, implemented with heapq."""

import heapq
from itertools import count
from time import perf_counter

from .models import Cell, Scenario, SearchResult, Status


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _search(s, start, goal, heuristic, horizon, limit, reservations):
    clock = perf_counter()
    timed = horizon is not None
    root = (*start, 0) if timed else start
    serial = count()
    heap = [(heuristic(start, goal), 0, next(serial), root)]
    g_score, parent = {root: 0}, {}
    expanded, generated, peak = 0, 1, 1

    def result(path, status):
        return SearchResult(
            path,
            status,
            len(path) - 1 if path else None,
            expanded,
            generated,
            peak,
            perf_counter() - clock,
        )

    if reservations and reservations.vertex_blocked(start, 0):
        return result([], Status.HORIZON)
    while heap:
        _, g, _, state = heapq.heappop(heap)
        if g != g_score.get(state):
            continue  # An earlier, worse heap entry must never expand again.
        if expanded >= limit:
            return result([], Status.LIMIT)
        expanded += 1
        p = state[:2]
        t = state[2] if timed else g
        if p == goal and (not reservations or reservations.can_hold(goal, t)):
            chain = [state]
            while chain[-1] in parent:
                chain.append(parent[chain[-1]])
            return result([n[:2] for n in reversed(chain)], Status.SUCCESS)
        if timed and t >= horizon:
            continue
        for q in s.neighbors(p, wait=timed):
            if reservations and (
                reservations.vertex_blocked(q, t + 1)
                or reservations.reverse_edge(p, q, t)
            ):
                continue
            nxt = (*q, t + 1) if timed else q
            ng = g + 1
            if ng < g_score.get(nxt, float("inf")):
                g_score[nxt], parent[nxt] = ng, state
                heapq.heappush(heap, (ng + heuristic(q, goal), ng, next(serial), nxt))
                generated += 1
                peak = max(peak, len(heap))
    return result([], Status.HORIZON if timed else Status.DISCONNECTED)


def spatial_astar(
    s: Scenario, start: Cell, goal: Cell, *, zero_heuristic=False, limit=100000
) -> SearchResult:
    if (
        type(limit) is not int
        or limit < 1
        or not _valid_cell(s, start)
        or not _valid_cell(s, goal)
    ):
        return SearchResult([], Status.INVALID, None)
    return _search(
        s,
        start,
        goal,
        (lambda a, b: 0) if zero_heuristic else manhattan,
        None,
        limit,
        None,
    )


def space_time_astar(
    s: Scenario, start: Cell, goal: Cell, reservations, *, horizon=80, limit=30000
) -> SearchResult:
    if (
        type(horizon) is not int
        or horizon < 0
        or type(limit) is not int
        or limit < 1
        or not _valid_cell(s, start)
        or not _valid_cell(s, goal)
    ):
        return SearchResult([], Status.INVALID, None)
    return _search(s, start, goal, manhattan, horizon, limit, reservations)


def _valid_cell(s, p):
    return (
        isinstance(p, tuple)
        and len(p) == 2
        and all(type(v) is int for v in p)
        and s.free(p)
    )
