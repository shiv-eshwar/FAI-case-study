import argparse
import json
from pathlib import Path

from .cooperative import plan
from .io import load_plan, save_plan
from .models import Scenario


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Warehouse planning and simultaneous replay"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "demo"):
        p = sub.add_parser(name)
        p.add_argument("--scenario", required=True)
        p.add_argument(
            "--algorithm",
            choices=["independent", "fixed", "cooperative"],
            default="cooperative",
        )
        p.add_argument("--seed", type=int, default=42)
        p.add_argument("--horizons", type=int, nargs="+", default=[40, 80])
        p.add_argument("--limit", type=int, default=30000)
        p.add_argument("--permutations", type=int, default=3)
        p.add_argument("--output", default="results/default_plan.json")
    p = sub.add_parser("replay")
    p.add_argument("--plan", required=True)
    p = sub.add_parser("render")
    p.add_argument("--plan", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--tick", type=int, default=0)
    p.add_argument("--fps", type=int, default=5)
    p = sub.add_parser("benchmark")
    p.add_argument("--config", required=True)
    p.add_argument("--output", help="optional results directory override")
    args = parser.parse_args(argv)
    try:
        if args.command == "benchmark":
            from .experiments import benchmark

            benchmark(args.config, args.output)
            return 0
        if args.command in ("plan", "demo"):
            s = Scenario.load(args.scenario)
            result = plan(
                s,
                args.algorithm,
                seed=args.seed,
                horizons=args.horizons,
                limit=args.limit,
                permutations=args.permutations,
            )
            data = save_plan(args.output, s, result)
            print(
                json.dumps(
                    {
                        "status": result.status,
                        "validation": data["validation"]["valid"],
                        "attempts": len(result.attempts),
                        "output": str(Path(args.output).resolve()),
                    }
                )
            )
            if not result.paths:
                return 2
            if args.command == "plan":
                return 0
        else:
            s, data = load_plan(args.plan)
        if args.command == "render":
            import matplotlib

            matplotlib.use("Agg")
            from .visualization import export

            if args.tick < 0 or args.fps <= 0:
                raise ValueError("tick must be nonnegative and fps positive")
            export(s, data, args.output, tick=args.tick, fps=args.fps)
        else:
            from .visualization import interactive

            interactive(s, data)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as e:
        parser.exit(2, f"error: {e}\n")
