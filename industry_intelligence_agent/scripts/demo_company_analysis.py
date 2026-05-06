"""Small demo script for analyzing one example company."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_mvp_pipeline


def main() -> None:
    """Run a simple demo analysis with starter inputs."""
    paths = run_mvp_pipeline(
        company="TSMC",
        industry="semiconductor",
        use_sample_data=True,
        export_excel=True,
    )

    print("Demo analysis finished.")
    print(paths.get("industry_intelligence_brief_md"))


if __name__ == "__main__":
    main()
