"""Portable PDF conversion and per-page QA PNG export (requires external tools)."""

import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--soffice", default="soffice")
    args = p.parse_args()
    qa = ROOT / "build/qa"
    qa.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="warehouse_lo_") as profile:
        for folder, filename in (
            ("docs", "report.docx"),
            ("slides", "presentation.pptx"),
        ):
            subprocess.run(
                [
                    args.soffice,
                    "--headless",
                    f"-env:UserInstallation={Path(profile).as_uri()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(ROOT / folder),
                    str(ROOT / folder / filename),
                ],
                check=True,
                timeout=120,
            )
            pdf = (ROOT / folder / filename).with_suffix(".pdf")
            if not pdf.exists():
                raise RuntimeError(f"conversion did not produce {pdf}")
            out = qa / pdf.stem
            out.mkdir(exist_ok=True)
            subprocess.run(
                ["pdftoppm", "-r", "100", "-png", str(pdf), str(out / "page")],
                check=True,
                timeout=120,
            )


if __name__ == "__main__":
    main()
