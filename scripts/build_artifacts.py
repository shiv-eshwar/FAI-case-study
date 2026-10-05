"""Build editable report and slides directly from recorded solver evidence.

Local python-docx/python-pptx fallback: the prescribed artifact runtime was not
exposed in the execution environment. No algorithm or result is synthesized.
"""

import json
from pathlib import Path
from statistics import mean

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor as PC
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches as PI
from pptx.util import Pt as PP

from warehouse_ai.cooperative import plan
from warehouse_ai.io import load_plan
from warehouse_ai.models import Scenario
from warehouse_ai.validation import metrics
from warehouse_ai.visualization import export

ROOT = Path(__file__).resolve().parents[1]
STUDENT_NAME = "Shiveshwar Kumar Sah"
ROLL_NUMBER = "BL.EN.U4CSE23072"


def main():
    summary = json.loads((ROOT / "results/summary.json").read_text())
    meta = json.loads((ROOT / "results/metadata.json").read_text())
    hs = json.loads((ROOT / "results/heuristic.json").read_text())
    tests = (ROOT / "results/test_execution.txt").read_text().strip().splitlines()[-1]
    s, data = load_plan(ROOT / "results/default_plan.json")
    m = metrics(data["paths"])
    for name, tick in (
        ("default_tick10.png", 10),
        ("default_complete.png", m["makespan"]),
    ):
        export(s, data, ROOT / "assets" / name, tick=tick)
    b, bd = load_plan(ROOT / "results/baseline_plan.json")
    export(b, bd, ROOT / "assets/baseline_conflict.png", tick=1)
    inter = Scenario.load(ROOT / "configs/intersection.json")
    joint = plan(inter, "fixed", horizons=(10,))
    worked = {
        "algorithm": "fixed",
        "paths": joint.paths,
        "elapsed": joint.elapsed,
        "validation": __import__(
            "warehouse_ai.validation", fromlist=["validate_plan"]
        ).validate_plan(inter, joint.paths),
    }
    export(inter, worked, ROOT / "assets/intersection_safe.png", tick=1)
    (ROOT / "results/worked_example.json").write_text(
        json.dumps({"scenario": inter.to_dict(), "paths": joint.paths}, indent=2)
    )
    examples = [
        [
            str(t),
            str(joint.paths["A"][min(t, len(joint.paths["A"]) - 1)]),
            str(joint.paths["B"][min(t, len(joint.paths["B"]) - 1)]),
        ]
        for t in range(max(map(len, joint.paths.values())))
    ]
    results_table = [
        [
            str(r["robot_count"]),
            r["algorithm"],
            f"{r['valid_samples']}/{r['samples']}",
            f"{r['mean_elapsed'] * 1000:.3f}",
            "-" if r["mean_cost"] is None else f"{r['mean_cost']:.1f}",
            "-" if r["mean_makespan"] is None else f"{r['mean_makespan']:.1f}",
        ]
        for r in summary["aggregate"]
    ]
    hmeans = {
        h: mean(r["expanded"] for r in hs if r["heuristic"] == h)
        for h in ("Manhattan", "zero")
    }
    defaulttext = f"The default plan has sum of costs {m['sum_cost']}, makespan {m['makespan']}, {m['moves']} moves and {m['waits']} wait. Its independent validation reports zero vertex and edge-swap conflicts."
    references = [
        "[1] Hart, P. E., Nilsson, N. J., and Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Paths. IEEE Transactions on Systems Science and Cybernetics 4(2), 100-107. DOI 10.1109/TSSC.1968.300136. https://ieeexplore.ieee.org/document/4082128",
        "[2] Silver, D. (2005). Cooperative Pathfinding. Proceedings of the AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment 1(1), 117-122. DOI 10.1609/aiide.v1i1.18726. https://ojs.aaai.org/index.php/AIIDE/article/view/18726",
        "[3] Stern, R., Sturtevant, N., Felner, A., Koenig, S., Ma, H., Walker, T., Li, J., Atzmon, D., Cohen, L., Kumar, T. K. S., Boyarski, E., and Bartak, R. (2019). Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks. arXiv:1906.08291, accepted to SoCS 2019. https://arxiv.org/abs/1906.08291",
    ]
    pages = [
        {
            "title": "Multi Agent Warehouse Robot Coordination Using A Star Search",
            "paras": [
                f"Fundamentals of AI undergraduate case study\n{STUDENT_NAME}   {ROLL_NUMBER}\n[Institution]   [Faculty]   [Submission Date]",
                "Abstract",
                "This case study implements and evaluates robot coordination for a single delivery wave in a static warehouse grid. Spatial A* with Manhattan distance supplies an independent-routing baseline. A centralized coordinator then searches states containing position and time, using vertex reservations, directed edge checks, waiting actions and permanent terminal goal occupancy. Fixed priorities and a bounded portfolio of deterministic priority attempts share the same low-level search. An independent validator inspects legal transitions and simultaneous occupancy before any coordinated plan is accepted. Experiments use a fixed shelf layout, four robot counts and five fixed seeds, together with six diagnostic scenarios. Both coordinators completed all twenty aggregate instances safely, while independent routing was safe on ten. At six robots, portfolio planning had a higher paired mean travel cost than fixed order, illustrating that retries do not globally optimize the objective. The default six-robot plan completes in twenty-one ticks. Automated tests cover an independent BFS oracle, collision semantics, goal occupancy, order sensitivity, bounded failure, JSON replay and headless rendering. Editable artifacts, saved evidence and offline reproduction commands accompany the implementation.",
                "Scope and demonstrated outcome",
                "The implementation covers offline planning and synchronous replay for point robots with static shelves. It excludes task allocation, physical motion control and dynamic replanning. The results support safe execution on the tested instances, with explicit limits on generalization. The marking coverage guide in Section 11 relates the requested 3-mark problem component and 7-mark implementation component to concrete evidence.",
            ],
        },
        {
            "title": "1 Warehouse problem and formal formulation",
            "paras": [
                "Robots carry assigned loads from starting bays to unique dispatch destinations. A shelf blocks a cell permanently. Crossing aisles allow routes to interact, so independent shortest paths are insufficient to ensure a safe delivery wave. The default warehouse has 20 columns, 15 rows and six robots. The geometry is configurable through JSON rather than encoded into the search logic.",
                "Let V be the traversable cells and E connect orthogonally adjacent cells. Each robot i has start s_i and goal g_i. A full joint state at tick t is the tuple of robot positions. The decentralized low-level representation (x,y,t) belongs to the chosen algorithm, not the problem definition. Inputs are grid dimensions, blocked cells, assignments and the collision/occupancy rules.",
                "Coordinates use x eastward and y northward with origin at the bottom left. An array would address a cell as [y,x]. The program instead stores shelves as a set of (x,y) tuples. Robot starts are distinct traversable cells, and goals are distinct traversable cells. A start may equal its own goal or another robot's goal. All robots occupy their starts at tick zero.",
                "Every action advances one global tick and either moves north, south, east, west, or waits in place. Actions cost one. Transition legality requires bounds and shelf clearance, with no teleportation or diagonal moves. Robots are point agents occupying one cell, and there is no continuous geometry or load-dependent speed.",
                "The goal test requires every robot to reach an accepted terminal goal and remain there. An intermediate goal visit can depart if staying would conflict with a future reservation. Only the final suffix completes delivery. The primary objective is a valid plan that completes all deliveries. Travel cost and makespan are reported as performance objectives, without claiming the coordinator minimizes them globally.",
            ],
            "table": (
                ["Constraint", "Exact interpretation"],
                [
                    [
                        "Vertex safety",
                        "For every pair i,j and tick t, positions differ.",
                    ],
                    [
                        "Edge safety",
                        "Two robots cannot exchange their distinct cells in one interval.",
                    ],
                    [
                        "Following",
                        "Entering another robot's just-vacated cell is allowed.",
                    ],
                    [
                        "Terminal occupancy",
                        "Every final goal remains occupied for all later ticks.",
                    ],
                ],
                "Table 1  Hard constraints and modeling assumptions",
            ),
        },
        {
            "title": "2 Spatial A Star and the independent baseline",
            "paras": [
                "Spatial A* searches only cells. The priority f is the known path cost g plus heuristic h [1]. Manhattan distance is the sum of the absolute coordinate differences. With four-connected unit moves, one tick can reduce this distance by at most one. Waiting does not reduce it. Shelves can lengthen a route but cannot create a shorter route than this lower bound. Manhattan is therefore admissible and consistent for this model.",
                "The shared search implementation uses heapq, g_score and a parent dictionary. Each heap entry contains f, g, a monotonic insertion counter and the state. Lower g breaks equal-f ties, followed by insertion order. Neighbors follow a fixed order. A popped entry whose g differs from the current best value is stale and is skipped. This prevents an old improvement candidate from doing duplicate work.",
                "Setting h to zero produces Dijkstra's algorithm without duplicating the search. A success path is reconstructed by following parents from the accepted goal to the start. Blocked or invalid endpoints return invalid_input. Spatial heap exhaustion returns static_disconnection, while an expansion cap returns expansion_limit. Start equals goal returns a one-cell path with cost zero.",
                "The independent baseline runs spatial A* for each robot with no inter-robot constraints. The validator then replays the paths simultaneously and pads shorter paths at their goals. A conflicting joint plan is labeled unsafe. Its raw path costs remain informative as individual route lengths, but are not costs of a feasible joint solution.",
            ],
            "equation": "f(n) = g(n) + h(n)    h(x,y) = |x - goal_x| + |y - goal_y|",
            "code": "SPATIAL A STAR\nheap <- (h(start), 0, serial, start)\ng_score[start] <- 0\nwhile heap is nonempty:\n  pop smallest entry; skip if stale\n  stop if expansion limit reached\n  count processed pop; accept if goal\n  for each legal orthogonal neighbor:\n    if g + 1 improves its score:\n      set score and parent; push with g + 1 + h\nreturn static disconnection on heap exhaustion",
            "after": [
                f"The separate five-pair heuristic experiment kept path costs equal. Mean processed pops were {hmeans['Manhattan']:.1f} with Manhattan and {hmeans['zero']:.1f} with h=0. This isolates heuristic search effort, not coordination quality. Full records are in results/heuristic.json."
            ],
        },
        {
            "title": "3 Space time search and waiting",
            "paras": [
                "Space-time A* augments position with absolute tick t, as in cooperative pathfinding [2]. The root is (start_x,start_y,0). Every successor has time t+1. The spatial neighbor order stays deterministic and a wait successor is appended. A wait has the same unit cost as a move, allowing the algorithm to avoid conflicts by changing arrival times rather than merely changing spatial routes.",
                "Before insertion, each successor checks the destination vertex at tick t+1 and the reverse of its directed traversal during interval t to t+1. A reserved reverse edge forbids an opposite traversal even when the destination is free at the arrival tick. A following action can still be allowed because the destination has been vacated and the reverse edge is absent.",
                "A candidate goal is accepted only when it can remain occupied indefinitely. The search may reach the goal while this test fails and continue searching. A later terminal arrival or a detour can make the route safe. The time-independent Manhattan heuristic remains a lower bound under the additional constraints.",
                "The time horizon is an absolute maximum tick, not a number of extra waits. States at the horizon may be accepted but cannot expand successors. A processed-pop limit bounds work independently. Exhausting the finite state space returns bounded_search_exhausted. This describes a bounded attempt, not proof that every possible coordinated plan is impossible. The coordinator performs spatial preflight to distinguish static disconnection before attempting temporal searches.",
            ],
            "code": "SPACE TIME A STAR\nroot <- (start, 0); use f = elapsed ticks + Manhattan\nwhile frontier is nonempty:\n  pop non-stale state; enforce expansion cap\n  if position is goal and can_hold(goal, t): reconstruct\n  if t == horizon: continue\n  for legal move or wait to q:\n    reject vertex(q, t+1) reservation\n    reject reserved reverse edge(q, p, t)\n    relax state(q, t+1) with unit cost\nreturn bounded search exhausted",
            "after": [
                "For a fixed set of higher-priority reservations, the low-level search returns a shortest accepted route within the search bounds when it succeeds. This conditional claim says nothing about the global sum of costs: the reservations themselves depend on earlier priority decisions."
            ],
        },
        {
            "title": "4 Reservation semantics and checked example",
            "paras": [
                "The reservation table has four explicit structures. vertices stores (cell,tick) for every state of a committed route, including tick zero. edges stores (from,to,departure_tick). permanent maps a terminal goal to its arrival tick and blocks it from then onward. last_visit stores the latest finite reserved tick for each cell.",
                "A candidate terminal goal at tick a is safe only if it has no permanent reservation and its latest finite visit is strictly earlier than a. This condition includes conflicts after a short route would otherwise have ended. Merely testing the arrival tick can incorrectly accept a goal that a higher-priority robot visits later.",
                "The following intersection example is generated from the actual fixed-order solver in results/worked_example.json. Independent routes both occupy (1,1) at tick 1. With A reserved first, B waits at (1,0) for one tick, then enters the center after A leaves. At tick 2, A remains at (2,1), and B follows into the vacated center.",
            ],
            "table": (
                ["Tick", "Robot A", "Robot B"],
                examples,
                "Table 2  Validated fixed-order intersection replay",
            ),
            "image": (
                "baseline_conflict.png",
                "Figure 1  Actual independent intersection conflict at tick 1",
                4.4,
            ),
            "after": [
                "For the independent edge-swap diagnostic, A moves u to v while B moves v to u in the same interval. Reserving (u,v,t) forces the low-level search to reject (v,u,t). Waiting outside the edge or taking a bypass can resolve a feasible case; a one-cell corridor without a bypass cannot change the ordering of two robots."
            ],
        },
        {
            "title": "5 Priorities retries and bounded failure",
            "paras": [
                "The fixed mode plans in lexicographic robot ID order, giving a reproducible coordinator baseline. The cooperative mode first sorts by descending Manhattan start-to-goal distance, using robot ID to break ties. It next tries the reverse order and three seeded permutations. Duplicate orders are removed while preserving their first occurrence.",
                "The default horizon schedule is 40 then 80 ticks. For each horizon, every unique order is tried until one complete valid result succeeds. Each attempt receives a newly constructed reservation table and path dictionary. A failed attempt discards all tentative routes. The selection rule is the first validated complete plan, rather than the lowest-cost successful plan.",
                "Total planning time includes static preflight, priority construction, all failed low-level searches and the final validation. Expanded and generated counts include preflight and every attempt. Per-attempt logs record order, horizon, status, processed pops, heap insertions and elapsed time. They explain why a retry was needed without silently hiding failure effort.",
            ],
            "code": "PRIORITIZED COORDINATION\nvalidate scenario; spatial preflight every assignment\nif independent: validate independent paths and label safety\nconstruct fixed order or deduplicated priority portfolio\nfor horizon in configured schedule:\n  for order in priority orders:\n    create empty reservations and paths\n    plan each robot in order with space-time A*\n    on failure: discard attempt, retain effort log\n    on success: reserve whole route and permanent goal\n    if all planned: independently validate and return\nreturn final bounded failure with all attempt logs",
            "after": [
                "The bay-exit fixture has A from (0,0) to (1,0), and B from (1,1) to (2,0). Shelves at (0,1) and (2,1) make the center the only exit. A first occupies the center permanently, so B cannot leave. B first exits through the center and A can arrive afterward. This fixture demonstrates order sensitivity and successful fresh-table retry.",
                "Retries improve robustness on this fixture but do not make prioritized planning complete, globally optimal or deadlock-proof. The impossible no-bypass corridor terminates within the documented horizons. Its impossibility follows from the robots' invariant left-to-right ordering, not from a generic bounded solver failure.",
            ],
        },
        {
            "title": "6 Architecture implementation and result contract",
            "paras": [
                "Scenario loading checks dimensions, shelf coordinates, traversable endpoints and uniqueness. Planning returns typed search or joint results. Validation independently checks the route transitions and pairwise simultaneous occupancy. Serialization then stores the complete scenario and result. Replay reads the same paths for either an interactive view or a headless export.",
                "The saved-plan schema includes schema_version, map geometry and robot assignments, paths, algorithm, seed, configuration, status, attempt logs, node counts, planning time and independent validation. On replay, validation is recomputed. A plan claiming success with conflicts is rejected with an actionable error. Failed partial plans are recorded but cannot be replayed as completed deliveries.",
                "A processed pop means a non-stale heap entry handled after the expansion-cap check, including an accepted goal. Generated means heap insertions, including the root and improved entries. Maximum frontier is the physical heap length, including stale entries. These definitions make comparisons reproducible, while remaining different from unique discovered-state counts.",
            ],
            "table": (
                ["File", "Responsibility"],
                [
                    [
                        "models.py and grid.py",
                        "Input contracts, geometry and deterministic endpoint sampling",
                    ],
                    ["astar.py", "Shared spatial and space-time heap search"],
                    [
                        "reservations.py",
                        "Vertex ticks, directed edges, future visits, permanent goals",
                    ],
                    [
                        "cooperative.py",
                        "Static preflight, priorities, fresh retries, bounded results",
                    ],
                    [
                        "validation.py and io.py",
                        "Independent replay safety, metrics and JSON contracts",
                    ],
                    [
                        "simulation.py and visualization.py",
                        "Simultaneous state, controls, screenshots and GIF",
                    ],
                    [
                        "experiments.py and cli.py",
                        "Same-instance evaluation and command interfaces",
                    ],
                ],
                "Table 3  Files inside src/warehouse_ai",
            ),
            "after": [
                "All paths use explicit CLI arguments. Benchmarks resolve their output folder relative to the configuration file. Tests exercise CLI invocation from a different working directory. There are no hidden cloud services, paid APIs, GPU requirements or external pathfinding packages in the runtime."
            ],
        },
        {
            "title": "7 Simulation interface and demonstration",
            "paras": [
                "The warehouse view uses dark shelves and light traversable cells. Stable robot colors accompany text IDs. Dashed boxes mark starts, outlined squares and G labels mark destinations, translucent lines show planned routes, and solid trails show completed movement. A paths/trails checkbox can simplify the view. Red rings and labels highlight actual conflict events at the displayed tick.",
                "Replay maintains one global tick. It advances that tick before reading all robot positions, applying a simultaneous state transition. Rendering does not move one robot at a time, so opposite-edge swaps cannot be hidden by sequential updates. Shorter routes hold their goals for the rest of the replay.",
            ],
            "image": (
                "default_tick10.png",
                "Figure 2  Actual saved default plan at tick 10",
                6.1,
            ),
            "after": [
                "Play/pause, Reset, Step and the ticks/sec slider control local Matplotlib replay. Scenario and algorithm selection use documented CLI flags. The display shows the tick, arrivals, sum of costs, makespan, planning time and global safety label. Close one window before launching the next scenario.",
                defaulttext,
                "The same saved paths generated assets/demo.gif and the safe/unsafe PNGs with Agg. Export rendering is separate from planning timing. Native GUI checks, if performed, are recorded separately in docs/QA.md. The reliable fallback is the generated GIF rather than a claim that a headless test opened an interactive window.",
            ],
        },
        {
            "title": "8 Experimental setup environment and metrics",
            "paras": [
                "Aggregate evaluation uses one fixed 20 by 15 shelf layout with open cross aisles at y=6 and y=10. For each count 2, 4, 6 and 8, five seeds 11, 22, 33, 44 and 55 uniformly sample 2N distinct free cells in deterministic row-major enumeration. The first N are starts and the rest goals. Every assignment is checked for spatial connectivity. This check does not guarantee joint feasibility.",
                "Independent, fixed and cooperative algorithms receive the same 20 aggregate instances, giving 60 aggregate runs. Six named diagnostic configurations add 18 runs: open intersection, corridor with passing bay, default shelf warehouse, goal-blocks-bay order fixture, impossible corridor swap and a disconnected assignment. All 78 run records remain in CSV and JSON, including unsafe plans and solver failures.",
                "The configured horizons are 40 and 80, with at most 30,000 processed pops per low-level search and three seeded permutation proposals. Horizons iterate outside the priority-order loop. There is one high-resolution perf_counter measurement per solver per instance. Charts show means across seeds, not repeated timing trials. Sub-millisecond values depend on this machine and should not be read as portable performance guarantees.",
                "Collision-free completion requires solver success and independent validation. A vertex conflict count is one event per unordered robot pair and tick. An edge swap count is one event per pair and interval, identified by the arrival tick. Counting runs from tick zero through the joint makespan, padding goals. With unique final goals, later constant occupancy cannot introduce new conflicts.",
                "Sum of costs is the sum of terminal arrival ticks, including waits. Makespan is their maximum. Move and wait counts stop at terminal arrival and exclude trailing display padding. Rates use all instances. Cost and makespan means use explicitly identified valid runs only. Failed planning time and search work remain in effort means. Paired cost differences compare fixed and portfolio only where both succeed.",
            ],
            "table": (
                ["Runtime item", "Recorded value"],
                [
                    ["Python", meta["environment"]["python"].split(" (")[0]],
                    ["Platform", meta["environment"]["platform"]],
                    *[[k, v] for k, v in meta["environment"]["dependencies"].items()],
                ],
                "Table 4  Actual tested environment",
            ),
            "after": [
                "Dependencies are graphics, testing and document tools. Search uses only the standard library. Environment and configuration are saved in results/metadata.json. Installation needs package access once; subsequent planning and replay are offline."
            ],
        },
        {
            "title": "9 Measured completion and planning effort",
            "paras": [
                "Both coordinators safely completed all 20 aggregate assignments. Independent A* safely completed 5/5 at two robots, 4/5 at four, 1/5 at six and 0/5 at eight. The unsafe baseline therefore cannot serve as a feasible cost competitor on its ten conflicting cases. The diagnostic suite deliberately includes failures, so its outcomes are reported separately.",
                "The two coordinator methods have identical success rates on this aggregate sample. That does not establish equal robustness in general. The order-sensitive fixture shows a retry benefit outside the aggregate sample, while the default succeeds in its first portfolio attempt. Five seeds per count give little coverage of harder endpoint assignments.",
            ],
            "image": (
                "success.png",
                "Figure 3  Completion rates over five seeds per count",
                4.8,
            ),
            "second_image": (
                "runtime.png",
                "Figure 4  Planning time includes preflight and failed attempts",
                4.8,
            ),
            "after": [
                "Temporal coordination increases planning work because it explores time-indexed states and checks reservations. Rendering time is excluded. These measurements describe this implementation and machine; no confidence intervals or broad scalability claim are asserted."
            ],
        },
        {
            "title": "10 Costs makespan and measured trade offs",
            "paras": [
                "Table 5 lists all aggregate means. A dash denotes no valid samples, not a zero-cost route. Independent cost means condition on different success subsets, so a lower baseline mean is not evidence of a better feasible algorithm. Fixed-versus-portfolio comparisons are paired on five common-success instances at each count."
            ],
            "table": (
                ["N", "Algorithm", "Safe n", "Time ms", "Cost", "Span"],
                results_table,
                "Table 5  Means across all runs for time and valid runs for cost and span",
            ),
            "after": [
                "At six robots, fixed order has mean sum cost 75.4 and makespan 20.2, while portfolio has cost 77.8 and makespan 19.8. The paired portfolio-minus-fixed cost is +2.4 ticks on five cases. The portfolio finds its first valid plan rather than choosing the cheapest successful order, so it can trade travel cost for a different finish time.",
                "Both coordinators have mean sum cost 114.2 and makespan 23.8 at eight robots in this sample. Complete makespan curves are bundled in assets/makespan.png. The results support a safety benefit over conflicting independent routes, not universal cost superiority for portfolio planning.",
            ],
        },
        {
            "title": "10 Additional cost and makespan evidence",
            "paras": [
                "Figures 5 and 6 list the valid-run sample counts beneath each chart. Independent routing has no valid sample at eight robots, so its curves stop at six. Costs and makespans conditioned on different sample subsets should not be compared as if all methods solved the same cases.",
                "The passing-bay diagnostic exposes incompleteness more directly. Both priority coordinators exhaust their configured search despite a feasible joint route. A checked witness lets A wait at (1,0) while B enters the bay at (2,1), then A passes and B exits toward (0,0). The first prioritized route never makes this concession. This is separately tested, and does not change the twenty-instance aggregate rates.",
            ],
            "image": ("cost.png", "Figure 5  Sum of costs over valid runs only", 4.8),
            "second_image": (
                "makespan.png",
                "Figure 6  Makespan over valid runs only",
                4.8,
            ),
            "after": [
                "Diagnostic outcomes are retained in results/runs.json. The disconnected assignment returns static_disconnection. The no-bypass corridor fails bounded attempts and also has an independent impossibility argument. The goal-blocks-bay fixture fails fixed order but succeeds after a portfolio order change."
            ],
        },
        {
            "title": "11 Verification safety invariants and rubric coverage",
            "paras": [
                f"The captured test run reports {tests}. The search-oracle test evaluates 50 seeded small maps with an independent BFS neighbor loop and checks equal costs for A* and h=0. Successful reconstructed paths must have correct endpoints, shelf clearance and unit transitions. Tests do not infer correctness from a nonempty result alone.",
                "Other tests exercise blocked and fractional endpoints, invalid dimensions, duplicate IDs/starts/goals, a zero-cost start-at-goal case, unreachable goals, explicit wait states, absolute horizons and resource caps. Collision tests separate vertex sharing, opposite-edge swaps and allowed following. Goal tests cover early permanent occupancy and future finite visits.",
                "The corridor failure is bounded. The bay-exit fixture verifies fixed-order failure, reversed-order success and deterministic seeded attempts. Every retry owns a new table. Corrupted paths expose illegal transitions and conflicts that happen after a shorter path has ended. CLI smoke tests run from a separate directory and check genuine PNG and GIF signatures.",
                "The independent validator is a safety barrier, not a proof of planner completeness. It checks the complete returned plan using actual path transitions and simultaneous occupancy, without consulting the reservation table or trusting saved planner flags.",
            ],
            "table": (
                [
                    "Requested component",
                    "Report and code evidence",
                    "Tests and demo evidence",
                ],
                [
                    [
                        "Problem formulation 3 marks",
                        "Sections 1-4; models.py, validation.py",
                        "Constraint table, collision tests, checked time example",
                    ],
                    [
                        "Implementation and simulation 7 marks",
                        "Sections 2-11; astar.py, reservations.py, cooperative.py, visualization.py",
                        "BFS oracle, retry/goal tests, CLI export test, saved safe/unsafe replay",
                    ],
                ],
                "Table 6  Coverage guide for the user supplied mark split",
            ),
            "after": [
                "This table is a coverage guide, not an invented instructor rubric or grade prediction. results/test_execution.txt captures actual execution. Each final artifact is generated from saved records so numerical summaries in the report and slides share the same source."
            ],
        },
        {
            "title": "12 Complexity limitations and conclusion",
            "paras": [
                "For a spatial grid with V free cells, there are at most four outgoing actions per cell. With a consistent heuristic, useful expansions are bounded by reachable cells when limits do not intervene. Binary-heap insertions and pops cost logarithmic time in frontier size. g_score and parent need storage proportional to discovered states, with extra heap storage for stale entries.",
                "A horizon H gives at most V(H+1) space-time states and at most five outgoing actions each. A broad worst-case per-search bound is O(VH log(VH)) time and O(VH) memory, including state records and heap entries up to constant factors on this bounded grid. The expansion cap can terminate earlier. Vertex, reverse-edge and terminal-hold checks are constant-time dictionary/set operations because last_visit summarizes future finite reservations.",
                "If N robots, P unique priority orders and K horizons are tried, worst-case coordinator search effort can approach KPN bounded searches, plus spatial preflight. Within one attempt, finite reservations occupy O(NH) entries with O(N) permanent goals. Attempts reset these structures and run sequentially. Validation compares unordered pairs across the makespan, O(N^2 H), and inspects O(NH) path transitions. These are implementation bounds, not claims about optimal joint search.",
                "Prioritized planning remains incomplete and order-dependent. A higher-priority terminal goal can permanently close an aisle to another robot. The distance portfolio reduces some failures but cannot explore every joint solution. Finite horizons and expansion caps can reject feasible cases. Centralized offline planning assumes known assignments, synchronized ticks and static shelves. Point agents ignore size, turning radius, localization errors and physical braking distances.",
                "The tested default and all twenty aggregate assignments have independently validated safe coordinated plans. The conflicting independent routes demonstrate why spatial shortest paths alone do not ensure simultaneous safety. The portfolio succeeds on the selected order-sensitive diagnostic and can have higher cost on otherwise solvable assignments. These are the demonstrated findings.",
                "Future work could add bounded CBS on tiny cases, using real high-level conflict branching and dedicated tests, or continuous task allocation and physical movement constraints. No CBS module is included. Those extensions would change complexity, feasibility and optimality assumptions and require new evidence.",
            ],
        },
        {
            "title": "13 References and reproduction appendix",
            "paras": references
            + [
                "Reference verification",
                "The IEEE publisher page, AAAI proceedings page and arXiv author record were retrieved during execution. Titles, authors, publication years and identifiers were checked against their page content. The first historical AAAI PDF URL returned 404 and was replaced with the working proceedings record. The DOI redirect for [1] failed, but the IEEE record exposed the same DOI and bibliographic details. No claim of accessing the IEEE paywalled full text is made. Verification excerpts and URLs are retained in docs/references.md.",
                "Reproduction",
                "From the extracted directory, create a Python 3.11+ environment, install the project with its test extra, then use the following exact interfaces. Windows setup and optional document extras are in README.md. All limits and seeds are persisted in JSON, while wall-clock results naturally change between runs.",
            ],
            "code": "python -m pip install -e '.[test]'\npython -m warehouse_ai plan --scenario configs/default.json --algorithm cooperative --seed 42\npython -m warehouse_ai replay --plan results/default_plan.json\npython -m warehouse_ai benchmark --config configs/benchmark.json\npython -m warehouse_ai render --plan results/default_plan.json --output assets/demo.gif\npython -m pytest -q",
            "after": [
                "Use docs/demo_script.md for a short demonstration, docs/code_walkthrough.md for source-reading order and docs/viva_guide.md for explanations. Fill in the institution, faculty and submission date before submission. AI assisted the implementation, testing and artifact preparation; adapt any disclosure to course policy without inventing authorship declarations.",
                "The local document fallback uses python-docx and python-pptx because the prescribed bundled artifact runtime was unavailable. DOCX/PPTX are genuine editable Office packages. PDF and visual QA status are recorded honestly in docs/QA.md. The submission ZIP excludes environments, caches and large temporary renders.",
            ],
        },
    ]
    build_report(pages)
    build_slides(summary, meta, tests, m, examples, references)
    (ROOT / "docs/references.md").write_text(
        "# Verified references\n\n"
        + "\n\n".join(references)
        + "\n\nVerified against IEEE publisher page (year, authors, pages and DOI), AAAI OJS proceedings record (2005-06-01, David Silver, 117-122 and DOI), and arXiv abstract record (2019, all twelve authors, title and identifier). Metadata verification, not a claim of full-text access to every paper.\n"
    )


def build_report(pages):
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Caption"):
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.color.rgb = RGBColor(0, 0, 0)
        for border in style.element.xpath("./w:pPr/w:pBdr"):
            border.getparent().remove(border)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.05
    doc.styles["Heading 1"].font.size = Pt(20)
    doc.styles["Title"].font.size = Pt(28)
    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run("Warehouse robot coordination   ").font.size = Pt(9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    md = []
    for idx, page in enumerate(pages):
        heading = doc.add_paragraph(page["title"], "Title" if idx == 0 else "Heading 1")
        heading.paragraph_format.page_break_before = bool(idx)
        md.append("# " + page["title"])
        for text in page.get("paras", []):
            doc.add_paragraph(text)
            md.append(text)
        if "equation" in page:
            p = doc.add_paragraph()
            math = OxmlElement("m:oMath")
            r = OxmlElement("m:r")
            t = OxmlElement("m:t")
            t.text = page["equation"]
            r.append(t)
            math.append(r)
            p._p.append(math)
            md.append(page["equation"])
        if "code" in page:
            p = doc.add_paragraph()
            run = p.add_run(page["code"])
            run.font.name = "Courier New"
            run.font.size = Pt(9)
            p.paragraph_format.space_after = Pt(9)
            p.paragraph_format.line_spacing = 1
            md.append("```text\n" + page["code"] + "\n```")
        if "table" in page:
            headers, rows, caption = page["table"]
            doc.add_paragraph(caption, "Caption")
            table = doc.add_table(rows=1, cols=len(headers))
            table.autofit = False
            widths = (
                [2.2, 4.8]
                if len(headers) == 2
                else ([0.8, 3.1, 3.1] if headers[0] == "Tick" else [2.1, 2.6, 2.3])
                if len(headers) == 3
                else [0.45, 1.8, 0.9, 1.3, 1.25, 1.3]
            )
            for col, width in zip(table.columns, widths):
                col.width = Inches(width)
            for c, h in zip(table.rows[0].cells, headers):
                c.text = h
            for row in rows:
                for c, value in zip(table.add_row().cells, row):
                    c.text = str(value)
            for ri, row in enumerate(table.rows):
                for ci, cell in enumerate(row.cells):
                    cell.width = Inches(widths[ci])
                    props = cell._tc.get_or_add_tcPr()
                    shade = OxmlElement("w:shd")
                    shade.set(
                        qn("w:fill"),
                        "DEE7EF" if ri == 0 else ("F6F8FA" if ri % 2 else "FFFFFF"),
                    )
                    props.append(shade)
                    borders = OxmlElement("w:tcBorders")
                    for side in ("top", "left", "bottom", "right"):
                        e = OxmlElement("w:" + side)
                        e.set(qn("w:val"), "single")
                        e.set(qn("w:sz"), "4")
                        e.set(qn("w:color"), "D9D9D9")
                        borders.append(e)
                    props.append(borders)
                    margins = OxmlElement("w:tcMar")
                    for side in ("top", "left", "bottom", "right"):
                        e = OxmlElement("w:" + side)
                        e.set(qn("w:w"), "80")
                        e.set(qn("w:type"), "dxa")
                        margins.append(e)
                    props.append(margins)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(3)
                        p.paragraph_format.space_before = Pt(3)
                        for r in p.runs:
                            r.font.size = Pt(9)
                            r.bold = ri == 0
            repeat = OxmlElement("w:tblHeader")
            table.rows[0]._tr.get_or_add_trPr().append(repeat)
            md.append(
                caption
                + "\n\n"
                + " | ".join(headers)
                + "\n"
                + "\n".join(" | ".join(row) for row in rows)
            )
        for key in ("image", "second_image"):
            if key in page:
                name, caption, width = page[key]
                doc.add_picture(str(ROOT / "assets" / name), width=Inches(width))
                doc.add_paragraph(caption, "Caption")
                md.append(f"![{caption}](../assets/{name})")
        for ai, text in enumerate(page.get("after", [])):
            p = doc.add_paragraph(text)
            if ai == 0 and "table" in page and "image" not in page:
                p.paragraph_format.space_before = Pt(6)
            md.append(text)
    (ROOT / "docs").mkdir(exist_ok=True)
    doc.core_properties.title = (
        "Multi-Agent Warehouse Robot Coordination Using A* Search"
    )
    doc.core_properties.author = STUDENT_NAME
    doc.core_properties.identifier = ROLL_NUMBER
    doc.save(ROOT / "docs/report.docx")
    (ROOT / "docs/report.md").write_text("\n\n".join(md))


def build_slides(summary, meta, tests, m, examples, references):
    prs = Presentation()
    prs.slide_width = PI(13.333)
    prs.slide_height = PI(7.5)
    navy = PC(21, 41, 60)
    teal = PC(0, 115, 110)
    gray = PC(75, 90, 101)

    def text(slide, value, x, y, w, h, size=24, color=navy, bold=False):
        box = slide.shapes.add_textbox(PI(x), PI(y), PI(w), PI(h))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = PI(0.03)
        for i, line in enumerate(value.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.name = "Calibri"
            p.font.size = PP(size)
            p.font.bold = bold
            p.font.color.rgb = color
            p.space_after = PP(14)
        return box

    def slide(title, body=None, note=""):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = PC(255, 255, 255)
        text(s, title, 0.6, 0.35, 12.1, 0.85, 32, bold=True)
        text(s, str(len(prs.slides)), 12.3, 7.22, 0.45, 0.22, 10, color=gray)
        if body:
            text(s, body, 0.7, 1.6, 11.8, 5, 25)
        s.notes_slide.notes_text_frame.text = note
        return s

    def image(s, name, x, y, w):
        s.shapes.add_picture(str(ROOT / "assets" / name), PI(x), PI(y), width=PI(w))

    def table(s, headers, rows, x, y, w, h, size=20):
        obj = s.shapes.add_table(
            len(rows) + 1, len(headers), PI(x), PI(y), PI(w), PI(h)
        ).table
        for ri, row in enumerate([headers] + rows):
            for ci, v in enumerate(row):
                cell = obj.cell(ri, ci)
                cell.text = str(v)
                cell.fill.solid()
                cell.fill.fore_color.rgb = (
                    PC(222, 232, 239) if ri == 0 else PC(247, 249, 251)
                )
                for p in cell.text_frame.paragraphs:
                    p.font.name = "Calibri"
                    p.font.size = PP(size)
                    p.font.color.rgb = navy
                    p.font.bold = ri == 0
        return obj

    def chart(s, field, x, y, w, h, title):
        d = CategoryChartData()
        d.categories = ["2", "4", "6", "8"]
        for algorithm in ("independent", "fixed", "cooperative"):
            rows = [r for r in summary["aggregate"] if r["algorithm"] == algorithm]
            d.add_series(
                algorithm,
                [r[field] * (1000 if field == "mean_elapsed" else 1) for r in rows],
            )
        c = s.shapes.add_chart(
            XL_CHART_TYPE.LINE_MARKERS, PI(x), PI(y), PI(w), PI(h), d
        ).chart
        c.has_title = True
        c.chart_title.text_frame.text = title
        c.has_legend = True
        c.legend.position = XL_LEGEND_POSITION.BOTTOM
        c.legend.include_in_layout = False
        c.legend.font.size = PP(14)
        c.category_axis.tick_labels.font.size = PP(16)
        c.value_axis.tick_labels.font.size = PP(14)
        for p in c.chart_title.text_frame.paragraphs:
            p.font.size = PP(20)
            p.font.name = "Calibri"

    s = slide(
        "Warehouse robot coordination",
        note="Present the objective in about 30 seconds. This is a single delivery wave with static shelves, built with explicit A* and space-time A*. Do not claim physical deployment. Student metadata must be replaced.",
    )
    text(
        s,
        "A* search for a safe delivery wave",
        0.7,
        1.7,
        11.5,
        1.2,
        42,
        color=teal,
        bold=True,
    )
    text(
        s,
        f"Fundamentals of AI\n{STUDENT_NAME}   {ROLL_NUMBER}\n[Institution]   [Faculty]   [Submission Date]",
        0.75,
        4.05,
        11.5,
        2,
        24,
    )
    s = slide(
        "The warehouse problem",
        note="Explain the six assigned loads, static shelf geometry and interacting routes. Primary aim is safe completion. Costs and finish times are performance measures, not globally optimized promises.",
    )
    image(s, "default_complete.png", 6.3, 1.45, 6.25)
    text(
        s,
        "20 x 15 cells and six robots\nAssigned starts and unique destinations\nCrossing aisles connect shelf blocks\nSafe completion is the primary objective",
        0.7,
        1.65,
        5.3,
        4.8,
        26,
    )
    s = slide(
        "State actions and collision rules",
        note="Full state is all positions at a synchronous tick. Lower-level states add time. Following is permitted, vertex sharing and opposite-edge swaps are forbidden. Final goals persist indefinitely. A nonterminal goal visit can depart when holding is unsafe.",
    )
    table(
        s,
        ["Model", "Rule"],
        [
            ["Coordinates", "(x,y), east +x, north +y"],
            ["Actions", "N, S, E, W or wait, unit cost"],
            ["Vertex conflict", "Same cell at the same tick"],
            ["Edge swap", "Opposite traversal in one interval"],
            ["Goals", "Hold accepted terminal goals forever"],
            ["Following", "Allowed after another robot leaves"],
        ],
        0.7,
        1.5,
        11.9,
        4.9,
        22,
    )
    s = slide(
        "Spatial A* search",
        note="Source [1]: "
        + references[0]
        + " Explain g as known cost, h as lower bound. Each orthogonal move reduces Manhattan by at most one. A zero heuristic gives Dijkstra through the same function. Shared _search uses heapq and skips stale entries. In the worked no-obstacle example root (0,0) to (2,1) has g=0,h=3,f=3. After east, g=1,h=2,f=3.",
    )
    text(
        s,
        "f(n) = g(n) + h(n)\nManhattan h = |x - goal_x| + |y - goal_y|",
        0.7,
        1.5,
        11.8,
        1.4,
        30,
        color=teal,
    )
    table(
        s,
        ["Cell toward (2,1)", "g", "h", "f"],
        [["(0,0)", "0", "3", "3"], ["(1,0)", "1", "2", "3"], ["(2,0)", "2", "1", "3"]],
        0.8,
        3.15,
        7.8,
        2.25,
        23,
    )
    text(
        s,
        "heapq frontier\nDeterministic ties\nStale-entry check\nh = 0 comparison",
        9,
        3.1,
        3.4,
        2.8,
        23,
    )
    s = slide(
        "Independent routes can collide",
        note="Show actual intersection baseline at tick 1. Both robots independently choose length-two routes through (1,1), causing a real vertex conflict. The cost four is unsafe joint cost, not a feasible solution. Source: results/baseline_plan.json.",
    )
    image(s, "baseline_conflict.png", 0.75, 1.35, 6.9)
    text(
        s,
        "Tick 1 shares the center\nBoth individual routes are shortest\nJoint replay detects a vertex conflict\nThe saved plan is labeled UNSAFE",
        8,
        1.8,
        4.55,
        4.8,
        26,
    )
    s = slide(
        "Space-time A* includes waiting",
        note="Source [2]: "
        + references[1]
        + " Explain (x,y,t), a unit-cost wait successor and absolute horizon. The intersection is taken from results/worked_example.json, not hand-drawn hypothetical routes. Low-level search may reach a goal but must still check safe holding.",
    )
    text(
        s,
        "State (x,y,t)\nMove or wait advances to t+1\nReservations constrain successors\nGoal acceptance checks future occupancy",
        0.7,
        1.6,
        5.7,
        4.6,
        27,
    )
    table(s, ["Tick", "A", "B"], examples, 6.8, 1.65, 5.7, 3.5, 22)
    text(s, "B waits one tick before the crossing", 6.8, 5.55, 5.7, 0.7, 23, color=teal)
    slide(
        "Reservation table semantics",
        "Vertex (cell,t) includes tick zero\nEdge (u,v,t) represents interval t to t+1\nReject the reserved reverse traversal (v,u,t)\nPermanent goal reservations continue indefinitely\nFuture finite visits also prevent early terminal acceptance",
        note="Walk through the dictionary/set design in reservations.py. last_visit summarizes the latest finite tick at a cell. can_hold requires no permanent use and last_visit < arrival. A goal free at the present tick may be unsafe later. Following remains legal when destination and reverse-edge tests pass.",
    )
    slide(
        "Implementation and planning flow",
        "Scenario validation and spatial preflight\nFresh reservation table for each priority attempt\nSpace-time A* commits one route at a time\nIndependent joint validator checks complete paths\nSelf-contained plan JSON feeds replay and export",
        note="Files: models/grid, astar, reservations/cooperative, validation/io, simulation/visualization. Fixed order is lexicographic ID. Portfolio is descending distance, reverse, three seeded permutations, deduplicated. Horizon sequence 40,80, first valid selection. All failed effort counts.",
    )
    s = slide(
        "Simulation and live demo",
        note="Run python -m warehouse_ai replay --plan results/default_plan.json. Point out paths, stable IDs, shelves and goal labels. Pause, step and reset, then change speed. A global tick reads all robot positions simultaneously. The headless GIF is a reliable fallback. Distinguish export verification from actual GUI checks in docs/QA.md.",
    )
    image(s, "default_tick10.png", 0.75, 1.4, 7.5)
    text(
        s,
        f"Play/pause, Step and Reset\nPlayback speed and overlays\nCost {m['sum_cost']}, makespan {m['makespan']}\n{m['moves']} moves and {m['waits']} wait\nZero detected conflicts",
        8.65,
        1.7,
        4,
        4.8,
        24,
    )
    slide(
        "Experiment design and fair comparison",
        "Same 20 aggregate instances for all algorithms\nRobot counts 2, 4, 6, 8 with five seeds each\nSix separate diagnostic scenarios\nHorizons 40 and 80, expansion cap 30,000\nRates use all cases, costs use valid cases\nTiming includes failed attempts and excludes rendering",
        note="Seeds are 11,22,33,44,55. Fixed shelf layout, uniform 2N distinct free endpoints, static connectivity checked but joint feasibility not guaranteed. There are 78 total runs. One perf_counter timing per solver and instance; means across seeds. Environment: "
        + meta["environment"]["python"].split(" (")[0]
        + ", "
        + meta["environment"]["platform"],
    )
    s = slide(
        "Measured completion and planning time",
        note="Raw data: results/runs.json and summary.json. Both coordinators 20/20 aggregate safe completion; independent 10/20. Five cases per count, no confidence intervals. Timing is machine-specific and includes all planning effort. Equal rates here do not establish equal general robustness.",
    )
    chart(s, "success_rate", 0.6, 1.55, 6, 4.6, "Safe completion rate")
    chart(s, "mean_elapsed", 6.8, 1.55, 6, 4.6, "Mean planning time (ms)")
    text(
        s,
        "Five seeds per robot count. Both coordinators safely complete 20/20 sampled cases.",
        0.8,
        6.4,
        11.8,
        0.65,
        21,
    )
    s = slide(
        "Priority portfolios can increase travel cost",
        note="Report only same common-success samples. At six robots, five paired cases: portfolio cost 77.8 versus fixed 75.4, delta +2.4. Portfolio mean makespan is 19.8 versus 20.2. First valid order is not global optimization. Independent valid subsets differ and have no valid sample at eight, so no independent cost advantage claim.",
    )
    table(
        s,
        ["Robots", "Fixed cost", "Portfolio cost", "Paired delta"],
        [
            [
                r["robot_count"],
                next(
                    x["mean_cost"]
                    for x in summary["aggregate"]
                    if x["algorithm"] == "fixed"
                    and x["robot_count"] == r["robot_count"]
                ),
                next(
                    x["mean_cost"]
                    for x in summary["aggregate"]
                    if x["algorithm"] == "cooperative"
                    and x["robot_count"] == r["robot_count"]
                ),
                r["mean_portfolio_minus_fixed_cost"],
            ]
            for r in summary["paired"]
        ],
        0.8,
        1.7,
        11.7,
        3,
        24,
    )
    text(
        s,
        "Five common-success pairs per count\nAt six robots, higher mean cost accompanies a lower mean makespan\nThe solver returns the first valid priority attempt",
        0.85,
        5.05,
        11.6,
        1.8,
        25,
    )
    slide(
        "Tests safety validation and failures",
        f"{tests}\n50 seeded maps checked against an independent BFS oracle\nVertex, swap, following and permanent-goal tests\nOrder-sensitive retry and bounded impossible corridor\nCLI, JSON reload, PNG and GIF export checks",
        note="Do not confuse pytest item count with number of randomized maps. Each algorithmic safety case tests concrete assertions. Validator reads actual transitions and padded occupancy, not reservations. Horizon exhaustion is not an impossibility proof. Exact evidence: results/test_execution.txt. GUI verification scope is separately documented.",
    )
    slide(
        "Limits and future work",
        "Prioritized planning is incomplete and order-dependent\nThe coordinator does not globally optimize cost or makespan\nFinite horizons and expansion limits can reject feasible cases\nStatic shelves, point robots and centralized offline planning\nFuture work: tiny-instance CBS and physical movement constraints",
        note="Explain the bay-exit fixture: A first plugs center; B first exits and A arrives later. Bounded retries are not deadlock-proof. CBS is not implemented and no optimality claim is borrowed from it. Complexity expands from V cells to V(H+1) time states per low-level search.",
    )
    slide(
        "Demonstrated findings and references",
        f"Default six-robot wave safely finishes in {m['makespan']} ticks\nBoth coordinators solve all 20 aggregate samples safely\nIndependent validation protects every complete returned plan\n\nHart, Nilsson and Raphael (1968), DOI 10.1109/TSSC.1968.300136\nSilver (2005), DOI 10.1609/aiide.v1i1.18726\nStern et al. (2019), arXiv:1906.08291",
        note="Close in about 30 seconds. These findings are scoped to tested cases. The three references were checked against publisher/author metadata; not every full text was accessed. Full URLs and all authors are in docs/references.md. Total presentation target 8-10 minutes. AI-assisted implementation and preparation should be disclosed according to course policy.",
    )
    (ROOT / "slides").mkdir(exist_ok=True)
    prs.core_properties.title = (
        "Multi-Agent Warehouse Robot Coordination Using A* Search"
    )
    prs.core_properties.author = STUDENT_NAME
    prs.core_properties.identifier = ROLL_NUMBER
    prs.save(ROOT / "slides/presentation.pptx")


if __name__ == "__main__":
    main()
