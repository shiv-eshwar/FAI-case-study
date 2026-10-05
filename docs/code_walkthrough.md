# Code walkthrough

1. Read models.py: Scenario owns static geometry and Robots own assignments.
   SearchResult defines exactly what a node count means. JointResult combines
   paths with attempt logs and total effort.
2. Read grid.py and configs/default.json: coordinates are (x,y). Sets store shelf
   cells. neighbors in models.py yields east, north, west, south deterministically.
3. Read astar.py: _search maintains g_score and parent, rejects stale heap pops,
   and reconstructs a chain. spatial_astar selects Manhattan or zero heuristic.
   space_time_astar turns on the time component and wait successors.
4. Read reservations.py: vertices store (cell,tick), edges store departure tick,
   permanent stores terminal arrival, last_visit allows a constant-time future
   occupancy check. can_hold is stronger than testing the arrival tick alone.
5. Read validation.py before cooperative.py. It is a second implementation of
   safety checking. position holds shorter paths at their goals. conflicts counts
   unordered pairs at each tick, including opposite traversals. metrics excludes
   trailing display padding from costs.
6. Read cooperative.py: static preflight finds disconnected assignments. Each
   horizon and priority order creates a fresh table. Low-level failure discards
   all partial paths. A complete result must pass validate_plan before return.
7. Read io.py and cli.py: JSON contains the whole scenario, paths, limits, seed,
   status, work and logs. Replay reloads and validates it rather than trusting the
   stored validation flag. Paths are explicit CLI arguments.
8. Read simulation.py and visualization.py: Replay advances one global tick,
   then state reads every position at that tick. Matplotlib draws shelf cells,
   endpoints, trails and actual conflicts. Rendering is outside planner timing.
9. Read experiments.py: every algorithm sees the same seeded assignments.
   Failed/unsafe runs stay in rates and effort statistics. Cost means select only
   valid runs; paired coordinator differences use common-success cases.
10. Read tests/test_search.py: BFS uses its own neighbor loop. The order-sensitive
    bay is a minimal counterexample to any general completeness claim.

Main data flow: JSON scenario -> validation -> planner -> independent joint
validation -> self-contained plan JSON -> Replay -> GUI or headless export.
Benchmarking reuses the planner and validator, then aggregates saved run records.

The accepted terminal goal state ends a route and reserves it forever. A goal
may be visited before that terminal state and left again when a future higher
priority visit prevents holding it safely. Explain this distinction explicitly.
Space-time searches are bounded by absolute arrival horizon and expansion count.
Static preflight counts are included in total effort, not hidden setup work.
