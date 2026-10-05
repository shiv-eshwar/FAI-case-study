"""Reconcile saved evidence and check artifact structure before packaging."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PIL import Image
from pypdf import PdfReader

from warehouse_ai.io import load_plan
from warehouse_ai.validation import metrics

ROOT = Path(__file__).resolve().parents[1]


def main():
    runs = json.loads((ROOT / "results/runs.json").read_text())
    sums = json.loads((ROOT / "results/summary.json").read_text())["aggregate"]
    assert len(runs) == 78
    for row in sums:
        group = [
            r
            for r in runs
            if r["group"] == "aggregate"
            and r["robot_count"] == row["robot_count"]
            and r["algorithm"] == row["algorithm"]
        ]
        assert (
            len(group) == row["samples"]
            and sum(r["valid"] for r in group) == row["valid_samples"]
        )
        good = [r for r in group if r["valid"]]
        if good:
            assert (
                abs(sum(r["sum_cost"] for r in good) / len(good) - row["mean_cost"])
                < 1e-10
            )
    s, d = load_plan(ROOT / "results/default_plan.json")
    assert d["validation"]["valid"] and metrics(d["paths"])["sum_cost"] == 111
    b, base = load_plan(ROOT / "results/baseline_plan.json")
    assert (
        not base["validation"]["valid"] and base["validation"]["vertex_conflicts"] > 0
    )
    report = PdfReader(ROOT / "docs/report.pdf")
    slides = PdfReader(ROOT / "slides/presentation.pdf")
    assert 12 <= len(report.pages) <= 16 and len(slides.pages) == 15
    for pdf in (report, slides):
        assert all(len(p.extract_text()) > 40 for p in pdf.pages)
    with ZipFile(ROOT / "slides/presentation.pptx") as z:
        names = z.namelist()
        assert z.testzip() is None
        assert (
            sum(n.startswith("ppt/charts/chart") and n.endswith(".xml") for n in names)
            == 2
        )
        assert (
            sum(
                n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml")
                for n in names
            )
            == 15
        )
        assert any(
            n.startswith("ppt/embeddings/") and n.endswith(".xlsx") for n in names
        )
    with ZipFile(ROOT / "docs/report.docx") as z:
        assert z.testzip() is None
        style = ET.fromstring(z.read("word/styles.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        title = next(
            s
            for s in style.findall("w:style", ns)
            if s.get("{" + ns["w"] + "}styleId") == "Title"
        )
        assert title.find("w:pPr/w:pBdr", ns) is None
    with Image.open(ROOT / "assets/demo.gif") as gif:
        assert gif.n_frames >= 22
    for p in (ROOT / "assets").glob("*.png"):
        with Image.open(p) as img:
            img.verify()
    record = {
        "run_records": len(runs),
        "report_pages": len(report.pages),
        "slides": len(slides.pages),
        "default": metrics(d["paths"]),
        "baseline_vertex_conflicts": base["validation"]["vertex_conflicts"],
        "office_packages": "ZIP integrity checked; native charts, workbooks and speaker notes present",
        "saved_summaries": "reconciled with raw run records",
    }
    (ROOT / "results/acceptance.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record))


if __name__ == "__main__":
    main()
