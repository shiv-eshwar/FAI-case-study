import random
from collections import deque

import pytest

from warehouse_ai.astar import space_time_astar, spatial_astar
from warehouse_ai.cooperative import plan
from warehouse_ai.models import Robot, Scenario, Status
from warehouse_ai.reservations import Reservations
from warehouse_ai.validation import conflicts, validate_plan


def scene(w=5, h=5, blocks=(), robots=None):
    return Scenario(
        "test",
        w,
        h,
        frozenset(blocks),
        tuple(robots or [Robot("R1", (0, 0), (w - 1, h - 1))]),
    )


def bfs(s, start, goal):
    q = deque([(start, 0)])
    seen = {start}
    while q:
        p, d = q.popleft()
        if p == goal:
            return d
        # Independent neighbor calculation, not the search implementation.
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            n = (p[0] + dx, p[1] + dy)
            if s.free(n) and n not in seen:
                seen.add(n)
                q.append((n, d + 1))
    return None


def test_astar_bfs_oracle():
    rng = random.Random(701)
    for _ in range(50):
        blocks = {(x, y) for x in range(6) for y in range(5) if rng.random() < 0.27} - {
            (0, 0),
            (5, 4),
        }
        s = scene(6, 5, blocks)
        a = spatial_astar(s, (0, 0), (5, 4))
        d = spatial_astar(s, (0, 0), (5, 4), zero_heuristic=True)
        assert a.cost == d.cost == bfs(s, (0, 0), (5, 4))
        if a.path:
            assert validate_plan(s, {"R1": a.path})["valid"]


def test_endpoints_and_limits():
    s = scene(blocks=[(1, 0)])
    assert spatial_astar(s, (0, 0), (0, 0)).cost == 0
    assert spatial_astar(s, (1, 0), (4, 4)).status == Status.INVALID
    assert spatial_astar(s, (-1, 0), (4, 4)).status == Status.INVALID
    assert spatial_astar(s, (0.5, 0), (4, 4)).status == Status.INVALID
    assert spatial_astar(s, (True, 0), (4, 4)).status == Status.INVALID
    assert spatial_astar(s, (0, 0), (4, 4), limit=1).status == Status.LIMIT
    assert (
        spatial_astar(scene(3, 1, [(1, 0)]), (0, 0), (2, 0)).status
        == Status.DISCONNECTED
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("width", 0),
        ("width", 2.5),
        ("obstacles", [[20, 1]]),
        (
            "robots",
            [
                {"id": "a", "start": [0, 0], "goal": [1, 1]},
                {"id": "b", "start": [0, 0], "goal": [2, 2]},
            ],
        ),
        (
            "robots",
            [
                {"id": "a", "start": [0, 0], "goal": [1, 1]},
                {"id": "b", "start": [2, 0], "goal": [1, 1]},
            ],
        ),
    ],
)
def test_bad_configuration(field, value):
    data = scene().to_dict()
    data[field] = value
    with pytest.raises(ValueError):
        Scenario.from_dict(data)


def test_reservation_ticks_reverse_and_following():
    t = Reservations()
    t.reserve([(0, 0), (1, 0), (2, 0)])
    assert t.vertex_blocked((0, 0), 0) and not t.vertex_blocked((0, 0), 1)
    assert t.reverse_edge((1, 0), (0, 0), 0)
    assert not t.reverse_edge((1, 0), (0, 0), 1)
    assert t.vertex_blocked((2, 0), 1000000)
    assert not t.vertex_blocked((1, 0), 2)  # Following is allowed.


def test_future_goal_visit_requires_later_terminal_arrival():
    s = scene(3, 2)
    t = Reservations()
    t.reserve([(2, 0), (2, 1), (1, 1), (0, 1)])
    assert not t.can_hold((1, 1), 1)
    r = space_time_astar(s, (1, 0), (1, 1), t, horizon=10)
    assert r.status == Status.SUCCESS and r.cost >= 3
    assert t.can_hold(r.path[-1], r.cost)


def test_early_goal_blocks_later_robot():
    t = Reservations()
    t.reserve([(1, 0)])
    r = space_time_astar(scene(3, 1), (0, 0), (2, 0), t, horizon=8)
    assert r.status == Status.HORIZON


def test_intersection_wait_or_detour():
    s = scene(3, 3, robots=[Robot("A", (0, 1), (2, 1)), Robot("B", (1, 0), (1, 2))])
    base = plan(s, "independent")
    safe = plan(s, "fixed", horizons=(10,))
    assert base.status == Status.UNSAFE
    assert safe.status == Status.SUCCESS and validate_plan(s, safe.paths)["valid"]
    assert sum(len(p) - 1 for p in safe.paths.values()) > 4


def test_conflicts_and_corrupted_paths():
    assert (
        conflicts({"a": [(0, 0), (1, 0)], "b": [(2, 0), (1, 0)]})[0]["kind"] == "vertex"
    )
    assert (
        conflicts({"a": [(0, 0), (1, 0)], "b": [(1, 0), (0, 0)]})[0]["kind"]
        == "edge_swap"
    )
    s = scene(4, 1, robots=[Robot("a", (0, 0), (1, 0)), Robot("b", (3, 0), (0, 0))])
    assert not validate_plan(
        s, {"a": [(0, 0), (1, 0)], "b": [(3, 0), (2, 0), (1, 0), (0, 0)]}
    )["valid"]
    assert not validate_plan(s, {"a": [(0, 0), (1, 0)], "b": [(3, 0), (0, 0)]})["valid"]


def test_valid_following():
    s = scene(4, 1, robots=[Robot("a", (1, 0), (3, 0)), Robot("b", (0, 0), (2, 0))])
    assert validate_plan(
        s, {"a": [(1, 0), (2, 0), (3, 0)], "b": [(0, 0), (1, 0), (2, 0)]}
    )["valid"]


def test_impossible_corridor_bounded():
    s = scene(3, 1, robots=[Robot("a", (0, 0), (2, 0)), Robot("b", (2, 0), (0, 0))])
    out = plan(s, horizons=(6, 10), limit=200, permutations=2)
    assert out.status != Status.SUCCESS and not out.paths
    assert len(out.attempts) <= 8


def order_sensitive():
    # A's goal plugs the only access to the bay; B must leave the bay first.
    return scene(
        3,
        2,
        blocks=[(0, 1), (2, 1)],
        robots=[Robot("A", (0, 0), (1, 0)), Robot("B", (1, 1), (2, 0))],
    )


def test_priority_retry_and_seed_determinism():
    s = order_sensitive()
    assert plan(s, "fixed", horizons=(8,)).status != Status.SUCCESS
    a = plan(s, horizons=(8,), seed=42)
    b = plan(s, horizons=(8,), seed=42)
    assert a.status == b.status == Status.SUCCESS and a.paths == b.paths
    assert validate_plan(s, a.paths)["valid"]
    assert [{k: v for k, v in x.items() if k != "elapsed"} for x in a.attempts] == [
        {k: v for k, v in x.items() if k != "elapsed"} for x in b.attempts
    ]
    assert a.attempts[-1]["order"] == ["B", "A"]
    # Two distance orders tried on a reset table; no failed state leaks.


def test_bad_limits():
    with pytest.raises(ValueError):
        plan(scene(), horizons=())
    with pytest.raises(ValueError):
        plan(scene(), limit=0)


def test_wait_state_and_absolute_horizon():
    t = Reservations()
    t.vertices.add(((1, 0), 1))
    t.last_visit[(1, 0)] = 1
    r = space_time_astar(scene(2, 1), (0, 0), (1, 0), t, horizon=2)
    assert r.path == [(0, 0), (0, 0), (1, 0)]
    assert (
        space_time_astar(scene(2, 1), (0, 0), (1, 0), t, horizon=1).status
        == Status.HORIZON
    )
    assert (
        space_time_astar(scene(2, 1), (0, 0), (1, 0), t, horizon=10, limit=1).status
        == Status.LIMIT
    )


def test_future_permanent_goal_rejects_early_hold():
    t = Reservations()
    t.reserve([(2, 0), (1, 0)])
    assert not t.can_hold((1, 0), 0)
    assert not t.vertex_blocked((1, 0), 0)


def test_duplicate_id_blocked_and_fractional_config():
    for robots in (
        [Robot("a", (0, 0), (1, 0)), Robot("a", (2, 0), (2, 1))],
        [Robot("a", (0.5, 0), (1, 0))],
        [Robot("a", (1, 1), (0, 0))],
    ):
        with pytest.raises(ValueError):
            scene(blocks=[(1, 1)], robots=robots).validate()


def test_feasible_passing_bay_exposes_priority_incompleteness():
    s = scene(
        5,
        2,
        blocks=[(0, 1), (1, 1), (3, 1), (4, 1)],
        robots=[Robot("A", (0, 0), (4, 0)), Robot("B", (4, 0), (0, 0))],
    )
    witness = {
        "A": [(0, 0), (1, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
        "B": [(4, 0), (3, 0), (2, 0), (2, 1), (2, 0), (1, 0), (0, 0)],
    }
    assert validate_plan(s, witness)["valid"]
    # Every first robot greedily takes its shortest corridor route, preventing
    # the concession that this feasible witness makes.
    assert plan(s, horizons=(10, 20)).status != Status.SUCCESS
