"""CSV, JSON, and Markdown exporters."""

from __future__ import annotations

import json
from pathlib import Path

from industry_intelligence_agent.analysis.brief import brief_to_markdown
from industry_intelligence_agent.models import SourceDocument


def export_documents(documents: list[SourceDocument], out_dir: str | Path) -> None:
    """Export source documents as CSV and JSON."""
    import pandas as pd

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = [doc.to_dict() for doc in documents]

    pd.DataFrame(records).to_csv(output / "documents.csv", index=False)
    with (output / "documents.json").open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def export_brief(brief: dict, out_dir: str | Path) -> None:
    """Export structured brief as JSON and Markdown."""
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)

    with (output / "industry_brief.json").open("w", encoding="utf-8") as file:
        json.dump(brief, file, ensure_ascii=False, indent=2)

    with (output / "industry_brief.md").open("w", encoding="utf-8") as file:
        file.write(brief_to_markdown(brief))

