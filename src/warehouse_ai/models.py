"""Typed input and result contracts. Coordinates are (x, y), y increases north."""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

Cell = tuple[int, int]


class Status(StrEnum):
    SUCCESS = "success"
    INVALID = "invalid_input"
    DISCONNECTED = "static_disconnection"
    HORIZON = "bounded_search_exhausted"
    LIMIT = "expansion_limit"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class Robot:
    id: str
    start: Cell
    goal: Cell


@dataclass(frozen=True)
class Scenario:
    name: str
    width: int
    height: int
    obstacles: frozenset[Cell]
    robots: tuple[Robot, ...]

    def free(self, p: Cell) -> bool:
        return (
            0 <= p[0] < self.width
            and 0 <= p[1] < self.height
            and p not in self.obstacles
        )

    def neighbors(self, p: Cell, wait: bool = False):
        # Deterministic east, north, west, south, then wait.
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)) + (((0, 0),) if wait else ()):
            q = (p[0] + dx, p[1] + dy)
            if self.free(q):
                yield q

    def validate(self):
        if (
            type(self.width) is not int
            or type(self.height) is not int
            or self.width < 1
            or self.height < 1
        ):
            raise ValueError("width and height must be positive integers")

        def cell(p):
            return len(p) == 2 and all(type(v) is int for v in p)

        if any(
            not cell(p) or not (0 <= p[0] < self.width and 0 <= p[1] < self.height)
            for p in self.obstacles
        ):
            raise ValueError("obstacles must be integer cells inside the map")
        if not self.robots:
            raise ValueError("at least one robot is required")
        for r in self.robots:
            if (
                not isinstance(r.id, str)
                or not r.id
                or not cell(r.start)
                or not cell(r.goal)
                or not self.free(r.start)
                or not self.free(r.goal)
            ):
                raise ValueError(
                    "robot IDs must be nonempty strings and endpoints traversable integer cells"
                )
        for attr in ("id", "start", "goal"):
            values = [getattr(r, attr) for r in self.robots]
            if len(set(values)) != len(values):
                raise ValueError(f"duplicate robot {attr}")

    def to_dict(self):
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "obstacles": sorted(self.obstacles),
            "robots": [
                {"id": r.id, "start": r.start, "goal": r.goal} for r in self.robots
            ],
        }

    @classmethod
    def from_dict(cls, data):
        try:
            s = cls(
                data["name"],
                data["width"],
                data["height"],
                frozenset(tuple(p) for p in data.get("obstacles", [])),
                tuple(
                    Robot(r["id"], tuple(r["start"]), tuple(r["goal"]))
                    for r in data["robots"]
                ),
            )
            s.validate()
            return s
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"invalid scenario: {e}") from e

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))


@dataclass
class SearchResult:
    path: list[Cell]
    status: Status
    cost: int | None
    expanded: int = 0  # Non-stale pops processed, including accepted goal.
    generated: int = 0  # Heap insertions, including root and improved entries.
    max_frontier: int = 0  # Physical heap length, including stale entries.
    elapsed: float = 0.0


@dataclass
class JointResult:
    paths: dict[str, list[Cell]]
    status: Status
    algorithm: str
    seed: int
    config: dict
    attempts: list[dict] = field(default_factory=list)
    expanded: int = 0
    generated: int = 0
    elapsed: float = 0.0
