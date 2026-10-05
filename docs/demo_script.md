# Three to four minute demo

Run from the extracted project with its environment active. Have `assets/demo.gif`
and `assets/baseline_conflict.png` ready if a GUI is unavailable.

## 0 to 45 seconds

```bash
python -m warehouse_ai demo --scenario configs/intersection.json --algorithm independent --output results/unsafe_demo.json
```

Pause, then Step once. Point to the shared center at tick 1, red conflict ring,
and UNSAFE label. Both spatial routes have cost 2, but the joint plan is unsafe.
Close this window before the next command.

## 45 to 105 seconds

```bash
python -m warehouse_ai demo --scenario configs/intersection.json --algorithm fixed --output results/intersection_demo.json
```

Step through the coordinated intersection. Explain that B waits before entering
the center. Waiting has unit cost and belongs to the space-time search. Follow
the displayed arrival count until both robots finish, then close the window.

## 105 to 180 seconds

```bash
python -m warehouse_ai replay --plan results/default_plan.json
```

Show shelves, dashed starts and labeled destinations. Use Play/pause and the
speed slider. Show a horizontal detour and the vertical waiting action. Explain
that all robots update at the same tick. Finish at tick 21, six arrivals and
sum cost 111. Goals remain occupied. Toggle overlays to show the clean map.

## 180 to 225 seconds

```bash
python -m warehouse_ai plan --scenario configs/order_sensitive.json --algorithm fixed --horizons 8 --output results/fixed_failure.json
python -m warehouse_ai plan --scenario configs/order_sensitive.json --algorithm cooperative --horizons 8 --output results/retry_demo.json
python -m pytest -q
```

First command intentionally returns exit code 2 with bounded_search_exhausted.
Second succeeds with B before A. Explain order dependence and the independent
validator. State that retries improve this fixture, not general completeness.

Fallback: display the saved baseline PNG and safe GIF. Say explicitly that these
are headless replays of saved plans. Re-render without a GUI if required:

```bash
python -m warehouse_ai render --plan results/default_plan.json --output assets/demo.gif
```
