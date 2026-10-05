"""Order-dependent prioritized planning: bounded, incomplete, not globally optimal."""

import random
from time import perf_counter

from .astar import space_time_astar, spatial_astar
from .models import JointResult, Status
from .reservations import Reservations
from .validation import validate_plan


def priority_orders(s, seed, permutations):
    fixed = sorted(s.robots, key=lambda r: r.id)
    distance = sorted(
        fixed,
        key=lambda r: (
            -abs(r.start[0] - r.goal[0]) - abs(r.start[1] - r.goal[1]),
            r.id,
        ),
    )
    candidates = [distance, list(reversed(distance))]
    rng = random.Random(seed)
    for _ in range(permutations):
        order = fixed.copy()
        rng.shuffle(order)
        candidates.append(order)
    unique = []
    for order in candidates:
        if [r.id for r in order] not in [[r.id for r in o] for o in unique]:
            unique.append(order)
    return unique


def plan(
    s,
    algorithm="cooperative",
    *,
    seed=42,
    horizons=(40, 80),
    limit=30000,
    permutations=3,
):
    s.validate()
    if algorithm not in ("independent", "fixed", "cooperative"):
        raise ValueError("algorithm must be independent, fixed or cooperative")
    if (
        not horizons
        or any(type(h) is not int or h < 0 for h in horizons)
        or type(limit) is not int
        or limit < 1
        or type(permutations) is not int
        or permutations < 0
    ):
        raise ValueError(
            "horizons must be nonnegative integers, limit positive, permutations nonnegative"
        )
    clock = perf_counter()
    config = {
        "horizons": list(horizons),
        "expansion_limit": limit,
        "permutations": permutations,
    }
    out = JointResult({}, Status.HORIZON, algorithm, seed, config)
    # Static preflight is timed and counted. No search package supplies routes.
    spatial = {}
    for r in s.robots:
        res = spatial_astar(s, r.start, r.goal, limit=limit)
        out.expanded += res.expanded
        out.generated += res.generated
        spatial[r.id] = res.path
        if res.status != Status.SUCCESS:
            out.status = res.status
            out.attempts.append(
                {
                    "phase": "static_preflight",
                    "robot": r.id,
                    "status": str(res.status),
                    "expanded": out.expanded,
                    "generated": out.generated,
                    "elapsed": perf_counter() - clock,
                }
            )
            out.elapsed = perf_counter() - clock
            return out
    if algorithm == "independent":
        out.paths = spatial
        out.status = (
            Status.SUCCESS if validate_plan(s, spatial)["valid"] else Status.UNSAFE
        )
        out.elapsed = perf_counter() - clock
        return out
    orders = (
        [sorted(s.robots, key=lambda r: r.id)]
        if algorithm == "fixed"
        else priority_orders(s, seed, permutations)
    )
    for horizon in horizons:
        for order in orders:
            # Reset all state on every attempt, including failed attempts.
            table, paths = Reservations(), {}
            start_time, expanded, generated = perf_counter(), 0, 0
            status = Status.SUCCESS
            for r in order:
                res = space_time_astar(
                    s, r.start, r.goal, table, horizon=horizon, limit=limit
                )
                expanded += res.expanded
                generated += res.generated
                if res.status != Status.SUCCESS:
                    status = res.status
                    break
                paths[r.id] = res.path
                table.reserve(res.path)
            out.attempts.append(
                {
                    "order": [r.id for r in order],
                    "horizon": horizon,
                    "status": str(status),
                    "expanded": expanded,
                    "generated": generated,
                    "elapsed": perf_counter() - start_time,
                }
            )
            out.expanded += expanded
            out.generated += generated
            if status == Status.SUCCESS:
                check = validate_plan(s, paths)
                if not check["valid"]:
                    # A future robot's start was not reserved by earlier ones.
                    # This only affects tick zero, since starts are distinct;
                    # validation still protects against any implementation bug.
                    raise RuntimeError(f"planner safety invariant failed: {check}")
                out.paths, out.status = paths, status
                out.elapsed = perf_counter() - clock
                return out
            out.status = status
    out.elapsed = perf_counter() - clock
    return out
