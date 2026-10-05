"""Self-contained replay JSON with independent validation on load."""

import json
from dataclasses import asdict
from pathlib import Path

from .models import Scenario, Status
from .validation import validate_plan


def save_plan(path, scenario, result):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "scenario": scenario.to_dict(),
        **asdict(result),
        "validation": validate_plan(scenario, result.paths),
    }
    target.write_text(json.dumps(data, indent=2))
    return data


def load_plan(path):
    try:
        data = json.loads(Path(path).read_text())
        if data.get("schema_version") != 1:
            raise ValueError("expected schema_version 1")
        required = (
            "scenario",
            "paths",
            "algorithm",
            "seed",
            "config",
            "status",
            "attempts",
            "expanded",
            "generated",
            "elapsed",
        )
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError("missing fields: " + ", ".join(missing))
        if (
            not isinstance(data["paths"], dict)
            or not isinstance(data["config"], dict)
            or not isinstance(data["attempts"], list)
        ):
            raise ValueError("paths/config must be objects and attempts an array")
        if not isinstance(data["algorithm"], str) or type(data["seed"]) is not int:
            raise ValueError("algorithm must be a string and seed an integer")
        if (
            any(
                type(data[k]) is not int or data[k] < 0
                for k in ("expanded", "generated")
            )
            or type(data["elapsed"]) not in (int, float)
            or data["elapsed"] < 0
        ):
            raise ValueError("search counts and elapsed must be nonnegative numbers")
        s = Scenario.from_dict(data["scenario"])
        paths = {k: [tuple(p) for p in v] for k, v in data["paths"].items()}
        check = validate_plan(s, paths)
        if check["errors"]:
            raise ValueError("; ".join(check["errors"]))
        status = Status(data["status"])
        if status not in (Status.SUCCESS, Status.UNSAFE):
            raise ValueError("failed plans cannot be replayed")
        if status == Status.SUCCESS and not check["valid"]:
            raise ValueError("claimed safe plan contains conflicts")
        if status == Status.UNSAFE and check["valid"]:
            raise ValueError("unsafe status disagrees with validated paths")
        data["paths"], data["validation"] = paths, check
        return s, data
    except (KeyError, TypeError, ValueError, IndexError) as e:
        raise ValueError(f"malformed replay plan: {e}") from e
