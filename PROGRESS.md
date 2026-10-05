# Execution record

## Plan
Implement and test spatial search and independent validation, then space-time
reservations and bounded priority retries. Build CLI/replay/rendering, execute
experiments, author evidence-based artifacts, visually inspect, package.

## Environment discovery
- Workspace initially contained only `prompt.md`.
- Python 3.12 available at `/opt/homebrew/bin/python3.12` (system `python3` is 3.9).
- Local `.venv` created for task execution; excluded from submission.
- Bundled artifact runtime loader is not exposed; local fallback dependencies
  used under the prompt's dependency fallback rule.
- CBS and dynamic obstacles deferred to future work.

## Completed implementation and execution
- Implemented spatial A*/h=0, space-time waits, permanent reservations, reverse
  edge checks, future-goal holding checks, priorities, clean retries and validator.
- Six diagnostic configurations and 20 seeded aggregate instances created.
- Tests: `../.venv/bin/python -m pytest -q | tee results/test_execution.txt`.
  Final captured core result: **22 passed in 1.03s**. One test compares 50 maps
  against BFS. A constructive passing-bay witness exposes planner incompleteness.
- Experiments: `../.venv/bin/python -m warehouse_ai benchmark --config configs/benchmark.json`.
  78 runs retained, 60 aggregate and 18 diagnostic. Both coordinators 20/20 safe,
  independent 10/20 safe. Default portfolio cost 111, makespan 21, moves 110, wait 1.
- Headless: `python -m warehouse_ai render --plan results/default_plan.json --output assets/demo.gif`.
  Also exported default tick 10, completion, and intersection conflict tick 1.
- Documents: `MPLBACKEND=Agg ../.venv/bin/python scripts/build_artifacts.py`.
  Report DOCX/source and 15-slide editable PPTX generated from saved evidence.
- PDFs: `../.venv/bin/python scripts/render_artifacts.py --soffice /Volumes/WarehouseLO/LibreOffice.app/Contents/MacOS/soffice`.
- Canonical DOCX QA:
  `env PATH="/Volumes/WarehouseLO/LibreOffice.app/Contents/MacOS:$PATH" ../.venv/bin/python /Users/shiv/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py docs/report.docx --output_dir build/docqa-release --emit_pdf`.
  Final report 15 pages. Fixed title border, chart sample-label overlap, paragraph
  spacing and code font after inspecting rendered pages.
- GUI: launched `MPLBACKEND=MacOSX python -m warehouse_ai replay --plan results/default_plan.json`.
  Native window visually checked. Step, reset, play/pause, overlay toggle and speed
  slider operated. Observed tick 21 and 6/6 arrivals. Headless GIF is separate evidence.
- Fresh environment: Python 3.12 venv at `/tmp/warehouse-fresh-H2r2u9/venv`, with
  `env -u PYTHONPATH .../python -m pip install -e '.[test]'`. All 22 tests passed,
  safe default plan, 78-run benchmark and GIF succeeded without document extras.

## Final gates completed
- All 15 final report pages and all 15 final slides visually inspected; no
  unresolved clipping or overlap. Native notes/charts and genuine Office/PDF
  packages checked with `../.venv/bin/python scripts/verify_delivery.py`.
- Built clean ZIP with `../.venv/bin/python scripts/package_submission.py`;
  extracted with `unzip -q warehouse_case_study_submission.zip -d /tmp/warehouse-fresh-H2r2u9/extracted`.
- Installed extracted project into the clean environment with
  `env -u PYTHONPATH /tmp/warehouse-fresh-H2r2u9/venv/bin/python -m pip install --no-deps -e /tmp/warehouse-fresh-H2r2u9/extracted/warehouse_case_study`.
  Dependencies had already been installed from the documented `.[test]` extra.
- From the extracted project, `env -u PYTHONPATH /tmp/warehouse-fresh-H2r2u9/venv/bin/python -m pytest -q`
  gave **22 passed in 1.10s**, captured in `results/extracted_test_execution.txt`.
- Extracted CLI planned a safe default and rendered a real tick-10 PNG.
  Imported package location was confirmed inside the extracted directory.
- Final packaging includes these records, checks every member CRC and compares
  every bundled file against `results/manifest.json` SHA-256 entries.

## User handoff
Required deliverables completed. Replace student metadata before submission.
Use README setup/run commands and docs/demo_script.md for the live presentation.
No critical acceptance failure remains; limitations below are intentional scope.

## GitHub submission preparation
- User requested publication to https://github.com/shiv-eshwar/FAI-case-study.git.
  Read-only checks confirmed the repository was empty and the account connected.
- Project becomes the repository root; no existing remote work is overwritten.
- README rewritten with setup, exact commands, real GIF/screenshots, measured
  results, limitations and links to submission documents. Development disclosure
  remains factual; no human-only authorship claim was introduced.
- Python files consistently formatted and imports sorted. Removed unused artifact
  builder variables. Ruff checks passed; all 22 tests passed again in 1.06s
  (`results/github_test_execution.txt`).
- Added read-only-permission GitHub Actions tests on Python 3.11 and 3.12.
- Git and ZIP exclusions cover environments, caches, generated build directories,
  and credentials. Raw measured data and report/slide evidence remain unchanged.
- Published initial commit `6c6313f` to `main`, then cloned the public repository
  into `/tmp/fai-github-submission-6c6313f`. That clone passed all 22 tests in 1.04s;
  all 82 SHA-256 manifest entries and 16 README links matched.
- Initial GitHub Actions run 37352499355 passed on Python 3.11 and 3.12. Updated
  checkout/setup-python to verified current release tags to remove deprecated
  Node.js action-runtime warnings. Final workflow result is visible on GitHub.

## Known scope limits
Prioritized planning is incomplete and not globally optimal. Passing-bay fixture
fails despite a validated witness. Static maps, point robots and finite limits.
CBS omitted. Local python-docx/python-pptx fallback used because the required
bundled artifact runtime loader was unavailable. LibreOffice 26.8.0.3 ran from
a downloaded, checksum-verified temporary official-vendor image, not an installed
user desktop app. No PowerPoint-native inspection claim is made.
