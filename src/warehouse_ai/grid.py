"""Fixed shelf geometry and seeded endpoint sampling for aggregate evaluation."""

import random

from .astar import spatial_astar
from .models import Robot, Scenario


def warehouse(robots=()):
    shelves = {
        (x, y)
        for x in (3, 4, 7, 8, 11, 12, 15, 16)
        for y in range(2, 13)
        if y not in (6, 10)
    }
    return Scenario("shelf warehouse", 20, 15, frozenset(shelves), tuple(robots))


def sampled_instance(count, seed):
    s = warehouse()
    cells = [(x, y) for y in range(s.height) for x in range(s.width) if s.free((x, y))]
    rng = random.Random(seed)
    # Distinct starts and goals; sampling 2N also keeps these sets disjoint.
    endpoints = rng.sample(cells, 2 * count)
    robots = tuple(
        Robot(f"R{i + 1}", endpoints[i], endpoints[count + i]) for i in range(count)
    )
    out = Scenario(
        f"shelves n={count} seed={seed}", s.width, s.height, s.obstacles, robots
    )
    out.validate()
    if any(spatial_astar(out, r.start, r.goal).cost is None for r in robots):
        raise ValueError(
            "sampled endpoints disconnected; do not count as a feasible joint instance"
        )
    return out
