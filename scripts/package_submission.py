"""Create a clean reproducible ZIP and verify every compressed member."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".firecrawl",
    "build",
    "dist",
    "htmlcov",
    ".git",
}


def main():
    files = sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.name not in {".DS_Store", ".coverage", ".env"}
        and not (p.name.startswith(".env.") and p.name != ".env.example")
        and p.suffix not in {".pyc", ".pyo"}
        and not any(
            part in EXCLUDED or part.endswith(".egg-info")
            for part in p.relative_to(ROOT).parts
        )
    )
    required = [
        "docs/report.pdf",
        "docs/report.docx",
        "slides/presentation.pptx",
        "slides/presentation.pdf",
        "assets/demo.gif",
        "results/test_execution.txt",
    ]
    for f in required:
        if not (ROOT / f).is_file():
            raise RuntimeError(f"missing required deliverable: {f}")
    manifest = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
        if p.name != "manifest.json"
    }
    (ROOT / "results/manifest.json").write_text(json.dumps(manifest, indent=2))
    files = sorted(set(files) | {ROOT / "results/manifest.json"})
    archive = ROOT.parent / "warehouse_case_study_submission.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, Path(ROOT.name) / p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP integrity error")
        print(
            f"Verified {len(z.namelist())} members in {archive}, {archive.stat().st_size} bytes"
        )


if __name__ == "__main__":
    main()
