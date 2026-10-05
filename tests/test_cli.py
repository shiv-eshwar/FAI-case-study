import json
import subprocess
import sys
from pathlib import Path

import pytest

from warehouse_ai.io import load_plan
from warehouse_ai.simulation import Replay

ROOT = Path(__file__).resolve().parents[1]


def test_cli_and_headless_replay(tmp_path):
    target = tmp_path / "plan.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "warehouse_ai",
            "plan",
            "--scenario",
            str(ROOT / "configs/intersection.json"),
            "--output",
            str(target),
        ],
        check=True,
        cwd=tmp_path,
    )
    s, data = load_plan(target)
    replay = Replay(data["paths"])
    before = replay.state
    after = replay.step()
    assert before != after and replay.tick == 1
    out = tmp_path / "frame.png"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "warehouse_ai",
            "render",
            "--plan",
            str(target),
            "--output",
            str(out),
        ],
        check=True,
        cwd=tmp_path,
    )
    assert out.read_bytes().startswith(b"\x89PNG")
    gif = tmp_path / "replay.gif"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "warehouse_ai",
            "render",
            "--plan",
            str(target),
            "--output",
            str(gif),
        ],
        check=True,
        cwd=tmp_path,
    )
    assert gif.read_bytes().startswith(b"GIF")


def test_malformed_plan_rejected(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"schema_version": 6}))
    with pytest.raises(ValueError, match="schema_version"):
        load_plan(p)
    p.write_text(json.dumps({"schema_version": 1}))
    with pytest.raises(ValueError, match="missing fields"):
        load_plan(p)
