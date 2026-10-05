"""Bounded same-instance evaluation. Failures remain in denominators and effort."""

import csv
import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from statistics import mean

from .astar import spatial_astar
from .cooperative import plan
from .grid import sampled_instance
from .io import save_plan
from .models import Scenario, Status
from .validation import metrics, validate_plan


def environment():
    dependencies = {}
    for package in (
        "numpy",
        "matplotlib",
        "pillow",
        "pytest",
        "python-docx",
        "python-pptx",
        "reportlab",
    ):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            pass  # Document extras are optional for benchmarks.
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "dependencies": dependencies,
    }


def benchmark(config_path, output=None):
    file = Path(config_path).resolve()
    config = json.loads(file.read_text())
    folder = (
        Path(output).resolve()
        if output
        else (file.parent / config.get("output", "../results")).resolve()
    )
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    instances = []
    for count in config["counts"]:
        for seed in config["seeds"]:
            instances.append(("aggregate", sampled_instance(count, seed), seed))
    for name in (
        "intersection",
        "bottleneck",
        "default",
        "order_sensitive",
        "impossible",
        "disconnected",
    ):
        instances.append(
            ("diagnostic", Scenario.load(file.parent / f"{name}.json"), 42)
        )
    for group, s, seed in instances:
        for algorithm in ("independent", "fixed", "cooperative"):
            result = plan(
                s,
                algorithm,
                seed=seed,
                horizons=config["horizons"],
                limit=config["limit"],
                permutations=config["permutations"],
            )
            validation = validate_plan(s, result.paths)
            success = result.status == Status.SUCCESS and validation["valid"]
            row = {
                "group": group,
                "scenario": s.name,
                "seed": seed,
                "robot_count": len(s.robots),
                "algorithm": algorithm,
                "status": str(result.status),
                "valid": success,
                "vertex_conflicts": validation["vertex_conflicts"],
                "edge_swap_conflicts": validation["edge_swap_conflicts"],
                "elapsed": result.elapsed,
                "expanded": result.expanded,
                "generated": result.generated,
                "attempt_count": len(result.attempts),
                "selected_order": result.attempts[-1].get("order", [])
                if success and result.attempts
                else [],
                "limits": result.config,
                "attempts": result.attempts,
                **(
                    metrics(result.paths)
                    if result.paths
                    else {k: None for k in ("sum_cost", "makespan", "moves", "waits")}
                ),
            }
            records.append(row)
            if group == "diagnostic":
                save_plan(
                    folder / f"{s.name.replace(' ', '_')}_{algorithm}.json", s, result
                )
                if s.name == "shelf warehouse" and algorithm == "cooperative":
                    save_plan(folder / "default_plan.json", s, result)
                if s.name == "open intersection" and algorithm == "independent":
                    save_plan(folder / "baseline_plan.json", s, result)
    (folder / "runs.json").write_text(json.dumps(records, indent=2))
    flat = [
        {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in r.items()}
        for r in records
    ]
    with (folder / "runs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    summaries = []
    for n in config["counts"]:
        for a in ("independent", "fixed", "cooperative"):
            runs = [
                r
                for r in records
                if r["group"] == "aggregate"
                and r["robot_count"] == n
                and r["algorithm"] == a
            ]
            valid = [r for r in runs if r["valid"]]
            summaries.append(
                {
                    "robot_count": n,
                    "algorithm": a,
                    "samples": len(runs),
                    "valid_samples": len(valid),
                    "success_rate": len(valid) / len(runs),
                    "mean_elapsed": mean(r["elapsed"] for r in runs),
                    "mean_expanded": mean(r["expanded"] for r in runs),
                    "mean_cost": mean(r["sum_cost"] for r in valid) if valid else None,
                    "mean_makespan": mean(r["makespan"] for r in valid)
                    if valid
                    else None,
                }
            )
    paired = []
    for n in config["counts"]:
        pairs = []
        for seed in config["seeds"]:
            subset = {
                r["algorithm"]: r
                for r in records
                if r["group"] == "aggregate"
                and r["robot_count"] == n
                and r["seed"] == seed
            }
            if subset["fixed"]["valid"] and subset["cooperative"]["valid"]:
                pairs.append(subset)
        paired.append(
            {
                "robot_count": n,
                "samples": len(pairs),
                "mean_portfolio_minus_fixed_cost": mean(
                    p["cooperative"]["sum_cost"] - p["fixed"]["sum_cost"] for p in pairs
                )
                if pairs
                else None,
            }
        )
    (folder / "summary.json").write_text(
        json.dumps({"aggregate": summaries, "paired": paired}, indent=2)
    )
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "environment": environment(),
                "config": config,
                "timing": "one perf_counter timing per solver per instance, rendering excluded; means across seeds",
                "sampling": "fixed shelf map, uniform seeded sample of 2N distinct free cells; static connectivity checked; joint feasibility not guaranteed",
            },
            indent=2,
        )
    )
    heuristics = []
    for seed in config["seeds"]:
        s = sampled_instance(2, seed)
        r = s.robots[0]
        for zero in (False, True):
            res = spatial_astar(s, r.start, r.goal, zero_heuristic=zero)
            heuristics.append(
                {
                    "seed": seed,
                    "heuristic": "zero" if zero else "Manhattan",
                    "cost": res.cost,
                    "expanded": res.expanded,
                    "generated": res.generated,
                    "max_frontier": res.max_frontier,
                    "elapsed": res.elapsed,
                }
            )
    (folder / "heuristic.json").write_text(json.dumps(heuristics, indent=2))
    plots(folder, summaries)
    print(
        json.dumps(
            {
                "runs": len(records),
                "aggregate_instances": len(config["counts"]) * len(config["seeds"]),
                "output": str(folder),
            }
        )
    )


def plots(folder, summaries):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    assets = folder.parent / "assets"
    assets.mkdir(exist_ok=True)
    for field, label, name in (
        ("success_rate", "Collision-free completion rate", "success"),
        ("mean_elapsed", "Mean planning time (ms), all runs", "runtime"),
        ("mean_cost", "Mean sum of costs, valid runs only", "cost"),
        ("mean_makespan", "Mean makespan, valid runs only", "makespan"),
    ):
        fig, ax = plt.subplots(figsize=(7.5, 4.3))
        for a, color in zip(
            ("independent", "fixed", "cooperative"), ("#D55E00", "#0072B2", "#009E73")
        ):
            rows = [
                r for r in summaries if r["algorithm"] == a and r[field] is not None
            ]
            ax.plot(
                [r["robot_count"] for r in rows],
                [r[field] * (1000 if field == "mean_elapsed" else 1) for r in rows],
                "o-",
                label=a,
                color=color,
            )
        ax.set_xticks([2, 4, 6, 8])
        ax.set_xlabel("Robots (five fixed seeds per count)")
        ax.set_ylabel(label)
        if field == "success_rate":
            ax.set_ylim(-0.05, 1.1)
        ax.grid(alpha=0.2)
        ax.legend()
        if field in ("mean_cost", "mean_makespan"):
            labels = []
            for a in ("independent", "fixed", "cooperative"):
                ns = [str(r["valid_samples"]) for r in summaries if r["algorithm"] == a]
                labels.append(a + " " + ",".join(ns))
            fig.text(
                0.11,
                0.015,
                "Valid n at 2,4,6,8 robots: " + "; ".join(labels),
                fontsize=9,
            )
            fig.tight_layout(rect=(0, 0.065, 1, 1))
        else:
            fig.tight_layout()
        fig.savefig(assets / f"{name}.png", dpi=180)
        plt.close(fig)
