"""Independent joint replay validation; does not inspect planner reservations."""

from itertools import combinations

from .astar import manhattan


def position(path, tick):
    return path[min(tick, len(path) - 1)]


def conflicts(paths):
    """One record per unordered pair and tick (vertex) or interval (swap).

    Goals are padded through joint makespan. Thereafter positions are constant.
    """
    if not paths or any(not p for p in paths.values()):
        return []
    events = []
    for t in range(max(map(len, paths.values()))):
        for a, b in combinations(sorted(paths), 2):
            p, q = position(paths[a], t), position(paths[b], t)
            if p == q:
                events.append(
                    {"kind": "vertex", "tick": t, "robots": [a, b], "cells": [p]}
                )
            if (
                t
                and p != q
                and position(paths[a], t - 1) == q
                and position(paths[b], t - 1) == p
            ):
                events.append(
                    {"kind": "edge_swap", "tick": t, "robots": [a, b], "cells": [p, q]}
                )
    return events


def validate_plan(s, paths):
    errors = []
    if set(paths) != {r.id for r in s.robots}:
        errors.append("path IDs must match every robot exactly")
    for r in s.robots:
        path = paths.get(r.id, [])
        if not path:
            errors.append(f"{r.id}: missing or empty path")
            continue
        if path[0] != r.start or path[-1] != r.goal:
            errors.append(f"{r.id}: wrong endpoints")
        if any(
            not isinstance(p, tuple)
            or len(p) != 2
            or any(type(v) is not int for v in p)
            or not s.free(p)
            for p in path
        ):
            errors.append(f"{r.id}: blocked, invalid or out-of-bounds cell")
            continue
        if any(manhattan(p, q) > 1 for p, q in zip(path, path[1:])):
            errors.append(f"{r.id}: illegal transition")
        # Goal visits before terminal arrival may depart again. Once the last
        # departure has ended, trailing goal waits are display padding only.
    well_formed = all(
        isinstance(p, tuple) and len(p) == 2 and all(type(v) is int for v in p)
        for path in paths.values()
        for p in path
    )
    events = conflicts(paths) if well_formed else []
    return {
        "valid": not errors and not events,
        "errors": errors,
        "conflicts": events,
        "vertex_conflicts": sum(e["kind"] == "vertex" for e in events),
        "edge_swap_conflicts": sum(e["kind"] == "edge_swap" for e in events),
    }


def metrics(paths):
    costs, moves, waits = [], 0, 0
    for path in paths.values():
        terminal = len(path) - 1
        while terminal > 0 and path[terminal - 1] == path[-1]:
            terminal -= 1
        costs.append(terminal)
        for p, q in zip(path[:terminal], path[1 : terminal + 1]):
            moves += p != q
            waits += p == q
    return {
        "sum_cost": sum(costs),
        "makespan": max(costs, default=0),
        "moves": moves,
        "waits": waits,
    }
