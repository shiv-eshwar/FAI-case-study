# Viva guide

1. **What is the problem?** Find legal simultaneous paths for assigned robots in
   a static grid, with unique destinations and permanent goal occupancy.
2. **What is the state?** Spatial A* uses (x,y). The coordinated low-level search
   uses (x,y,t). The full joint state is the tuple of all robot positions at t.
3. **Why Manhattan distance?** Four-connected moves can reduce its value by at
   most one per tick. Shelves and waits can increase actual cost, not reduce the
   lower bound. It is also consistent for unit moves and waits.
4. **What does f=g+h mean?** g is the cost already incurred. h estimates the
   minimum remaining cost. Their sum orders the frontier.
5. **Why not spatial A* alone?** Individually shortest routes may occupy an
   intersection together or traverse the same edge in opposite directions.
6. **What are the collision rules?** A vertex conflict shares a cell at a tick.
   A swap conflict exchanges two cells in one interval. Following is allowed.
7. **How does waiting work?** It is a real successor (x,y,t+1), charged one unit.
   It is selected during search rather than inserted into paths afterward.
8. **Why reserve time zero?** Every robot occupies its starting cell before the
   first action. Reserved paths include their initial states.
9. **How are edge times indexed?** (u,v,t) means a traversal from tick t to t+1.
   A candidate (v,u,t) is rejected.
10. **Why hold goals forever?** Delivered robots remain physically present.
    The permanent dictionary represents occupancy from arrival to infinity.
11. **Why check future visits to a candidate goal?** Being free now does not
    guarantee it can be occupied forever. The last_visit and permanent maps
    reject an unsafe terminal arrival.
12. **Why does priority matter?** Early robots choose routes without considering
    later routes. A goal can plug an aisle. The bay-exit fixture succeeds only
    when B plans before A under these limits.
13. **Does failure prove impossibility?** Static disconnection proves that robot
    cannot reach its goal in this static map. Horizon or expansion exhaustion
    only proves this bounded attempt failed. The tiny no-bypass corridor has a
    separate ordering argument for impossibility.
14. **Is the full planner optimal or complete?** No. Low-level A* is shortest
    under current reservations when search succeeds before limits. That does not
    optimize the joint objective, and retries do not confer completeness.
15. **How is safety verified?** validation.py independently inspects every path,
    legal transitions and padded simultaneous states, without reading reservations.
16. **What did the experiments show?** Both coordinators safely solved 20/20
    aggregate instances. Independent A* safely solved 10/20. Portfolio mean cost
    exceeded fixed order by 2.4 ticks at six robots on five paired cases. This is
    a small sample, not a general guarantee.
