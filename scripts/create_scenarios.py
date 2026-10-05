"""Deterministic, transparent scenario generation. Run from any directory."""

import json
from pathlib import Path

from warehouse_ai.grid import warehouse
from warehouse_ai.models import Robot, Scenario

ROOT = Path(__file__).resolve().parents[1]


def main():
    robots = [
        Robot(f"R{i + 1}", a, b)
        for i, (a, b) in enumerate(
            [
                ((0, 6), (19, 6)),
                ((19, 6), (0, 6)),
                ((6, 0), (6, 14)),
                ((6, 14), (6, 0)),
                ((0, 10), (19, 10)),
                ((19, 10), (0, 10)),
            ]
        )
    ]
    configs = {
        "default": warehouse(robots),
        "intersection": Scenario(
            "open intersection",
            3,
            3,
            frozenset(),
            (Robot("A", (0, 1), (2, 1)), Robot("B", (1, 0), (1, 2))),
        ),
        "bottleneck": Scenario(
            "corridor with passing bay",
            5,
            2,
            frozenset({(0, 1), (1, 1), (3, 1), (4, 1)}),
            (Robot("A", (0, 0), (4, 0)), Robot("B", (4, 0), (0, 0))),
        ),
        "order_sensitive": Scenario(
            "goal blocks bay exit",
            3,
            2,
            frozenset({(0, 1), (2, 1)}),
            (Robot("A", (0, 0), (1, 0)), Robot("B", (1, 1), (2, 0))),
        ),
        "impossible": Scenario(
            "corridor swap no bypass",
            3,
            1,
            frozenset(),
            (Robot("A", (0, 0), (2, 0)), Robot("B", (2, 0), (0, 0))),
        ),
        "disconnected": Scenario(
            "shelf separates endpoints",
            3,
            1,
            frozenset({(1, 0)}),
            (Robot("A", (0, 0), (2, 0)),),
        ),
    }
    folder = ROOT / "configs"
    folder.mkdir(exist_ok=True)
    for name, s in configs.items():
        s.validate()
        (folder / f"{name}.json").write_text(json.dumps(s.to_dict(), indent=2))
    (folder / "benchmark.json").write_text(
        json.dumps(
            {
                "counts": [2, 4, 6, 8],
                "seeds": [11, 22, 33, 44, 55],
                "horizons": [40, 80],
                "limit": 30000,
                "permutations": 3,
                "output": "../results",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
