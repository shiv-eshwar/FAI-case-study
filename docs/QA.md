# Verification record

## Algorithms and results

- Core captured suite: 22 passed in 1.03 seconds, `results/test_execution.txt`.
- BFS oracle covers 50 seeded random maps, rather than counting each as a test.
- Aggregate benchmark: 20 same-instance cases, three algorithms, 60 runs.
- Six diagnostics add 18 runs. Failures/unsafe routes remain in CSV/JSON.
- Fixed and portfolio each 20/20 safe aggregate completion. Independent 10/20.
- Saved default plan independently validates with cost 111 and makespan 21.
- Both coordinators fail the feasible passing-bay diagnostic. A constructive
  collision-free witness is explicitly checked in test_search.py.

## Artifact rendering and visual review

Report: real DOCX and 15-page Letter PDF, rendered with LibreOffice 26.8.0.3.
The document skill's canonical render_docx.py also generated every page PNG.
Every report page was visually inspected. Repairs removed blank pagination,
overflow onto sparse pages, an inherited title border, sample-label overlaps
in cost/makespan charts and an unavailable monospaced font substitution.

Slides: real editable 15-slide 16:9 PPTX and 15-page PDF. Every slide was rendered
with LibreOffice and inspected individually. Text, tables, speaker notes and two
measured charts remain editable native objects. Screenshots are evidence images.
Slide footer position was adjusted to avoid the model table. PowerPoint itself
was not used for native rendering or inspection.

The bundled artifact runtime loader and @oai/artifact-tool were not exposed here.
The prompt's local-library fallback was used with python-docx/python-pptx, and
this deviation is disclosed. A temporary official LibreOffice disk image was
SHA-256 verified against Homebrew's vendor metadata before use:
`8858d8058da4f862f47559486814e65efc27294da67c5e4bb56b006b1ee59f89`.
Rendering binaries, disk image and QA PNGs are excluded from submission.

After the student supplied their details, both covers and Office properties were
updated to Shiveshwar Kumar Sah, BL.EN.U4CSE23072. Both PDFs were regenerated.
The report remained 15 pages and every page was reviewed; pages 2–14 were also
pixel-identical to the earlier canonical render. The updated title slide was
visually reviewed. PPTX part comparison confirmed only slide 1 and core properties
changed. No student-name or roll-number placeholders remain in either Office
package or PDF. Institution, faculty and submission date await supplied details.

## Simulation evidence

Headless Agg exports produced real GIF/PNG files from saved JSON paths. The
baseline screenshot shows the actual intersection vertex conflict at tick 1.
The safe screenshots show tick 10 and final tick 21 of the saved default plan.

Separately, the native MacOSX Matplotlib window was opened and controlled through
computer use. Single Step changed tick 0 to 1; reset returned to tick 0; paths and
trails toggled; the speed slider changed from 4 to about 9.82 ticks/sec. Play/pause
stopped the display at tick 2, and automatic playback reached tick 21 with six
arrivals. This checks the available macOS GUI, not every OS/backend combination.

## Installation and packaging

For GitHub submission, source formatting and import cleanup were followed by
another full local test run: **22 passed in 1.06s**, retained in
results/github_test_execution.txt. Ruff lint checks passed. A GitHub Actions
workflow additionally runs the suite on Ubuntu with Python 3.11 and 3.12.
Both jobs passed in GitHub Actions run 37352499355. The repository was also cloned
back from GitHub; its suite passed all 22 tests in 1.04s, and its bundled manifest
and README image/document paths verified successfully.

A clean Python 3.12 venv installed only `.[test]` with PYTHONPATH removed. It ran
all 22 tests, planned the default safely, completed all 78 benchmark records and
exported a GIF without the optional document dependencies. Tested runtime and
dependency versions are in results/metadata.json. Windows instructions are
provided, but this session did not execute on Windows.

The ZIP was extracted into a separate temporary directory and that extracted
source was installed into the fresh environment. Import location was checked.
Its full suite passed: **22 passed in 1.10s**; actual output is retained in
results/extracted_test_execution.txt. Its CLI produced a new default plan that
independently validated with zero conflicts, cost 111 and makespan 21, and
exported a tick-10 PNG. Final archive CRC and per-file SHA-256 manifest checks
were also performed after packaging the final documentation records.

The final archive uses a relative project root and excludes venvs, caches,
credentials, external research downloads and temporary renders. A SHA-256
manifest lists bundled files. Archive integrity and extracted-project checks
are captured in the final acceptance record.
