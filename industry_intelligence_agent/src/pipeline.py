"""End-to-end MVP pipeline for the Industry Intelligence Agent."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.annual_report_reader import (
    chunk_text,
    clean_annual_report_text,
    extract_text_from_pdf,
    generate_sample_annual_report_text,
    save_chunks_to_json,
)
from src.company_registry import (
    generate_sample_company_registry,
    get_company_profile,
    load_company_registry,
)
from src.excel_report_generator import generate_excel_report
from src.kri_extractor import extract_kri_mentions, save_kri_results
from src.news_collector import (
    fetch_rss_articles,
    generate_sample_news,
    load_rss_sources,
    load_sample_news,
    save_articles,
)
from src.report_generator import (
    build_dashboard_kpi_kri_table,
    generate_final_demo_summary_zh,
    generate_json_report,
    generate_markdown_report,
    save_report,
)


logger = logging.getLogger(__name__)


def run_mvp_pipeline(
    company: str,
    industry: str,
    company_registry: str | Path | None = None,
    news_csv: str | Path | None = None,
    annual_report: str | Path | None = None,
    use_sample_data: bool = True,
    export_excel: bool = True,
    language: str = "zh-TW",
    output_dir: str | Path = "data/exports",
) -> dict[str, str]:
    """Run the complete interview-ready MVP workflow."""
    project_root = Path(__file__).resolve().parents[1]
    output_path = _resolve_path(output_dir, project_root)
    reports_path = project_root / "data" / "reports"
    raw_path = project_root / "data" / "raw"
    processed_path = project_root / "data" / "processed"
    for folder in [output_path, reports_path, raw_path, processed_path]:
        folder.mkdir(parents=True, exist_ok=True)

    registry_path = _resolve_path(company_registry, project_root) if company_registry else raw_path / "company_registry.csv"
    sample_news_path = _resolve_path(news_csv, project_root) if news_csv else raw_path / "sample_news.csv"

    if use_sample_data:
        # In sample mode, refresh default sample inputs so the demo is complete
        # and reproducible. A user-provided custom path is still respected.
        if company_registry is None or not registry_path.exists():
            generate_sample_company_registry(registry_path)
        if news_csv is None or not sample_news_path.exists():
            generate_sample_news(sample_news_path)

    registry_df = load_company_registry(registry_path)
    company_profile = get_company_profile(registry_df, company_name=company) or {
        "company_name": company,
        "ticker": "",
        "industry": industry,
        "source": "user_input",
    }
    if industry:
        company_profile["industry"] = industry

    company_profile_df = pd.DataFrame([company_profile])

    news_df = _load_or_collect_news(
        company=company_profile.get("company_name", company),
        industry=industry,
        sample_news_path=sample_news_path,
        project_root=project_root,
        use_sample_data=use_sample_data,
    )
    news_df["company_name"] = news_df["company_name"].replace("", company_profile.get("company_name", company))
    news_df["industry"] = news_df["industry"].replace("", industry)

    annual_text = _load_annual_report_text(
        annual_report=annual_report,
        company_name=company_profile.get("company_name", company),
        industry=industry,
        project_root=project_root,
        use_sample_data=use_sample_data,
    )
    annual_text = clean_annual_report_text(annual_text)
    annual_chunks = chunk_text(annual_text)

    trend_notes = _load_or_generate_trend_notes(company_profile.get("company_name", company), industry, project_root)

    kri_df = _extract_all_kri(
        news_df=news_df,
        annual_text=annual_text,
        company_name=company_profile.get("company_name", company),
        industry=industry,
    )

    dashboard_df = build_dashboard_kpi_kri_table(news_df, kri_df, trend_notes)

    markdown_report = generate_markdown_report(company_profile, news_df, kri_df, trend_notes, annual_text)
    json_report = generate_json_report(company_profile, news_df, kri_df, trend_notes, annual_text)
    final_summary_zh = generate_final_demo_summary_zh(company_profile.get("company_name", company), industry)

    output_files = {
        "company_profile_csv": output_path / "company_profile.csv",
        "news_articles_csv": output_path / "news_articles.csv",
        "kri_evidence_csv": output_path / "kri_evidence.csv",
        "dashboard_ready_csv": output_path / "dashboard_ready.csv",
        "annual_report_chunks_json": processed_path / "annual_report_chunks.json",
        "industry_intelligence_brief_md": reports_path / "industry_intelligence_brief.md",
        "industry_intelligence_brief_json": reports_path / "industry_intelligence_brief.json",
        "final_demo_summary_zh_md": reports_path / "final_demo_summary_zh.md",
        "excel_workbook": reports_path / "industry_intelligence_demo.xlsx",
    }

    company_profile_df.to_csv(output_files["company_profile_csv"], index=False, encoding="utf-8-sig")
    save_articles(news_df, output_files["news_articles_csv"])
    save_kri_results(kri_df, output_files["kri_evidence_csv"])
    dashboard_df.to_csv(output_files["dashboard_ready_csv"], index=False, encoding="utf-8-sig")
    save_chunks_to_json(annual_chunks, output_files["annual_report_chunks_json"])
    save_report(markdown_report, output_files["industry_intelligence_brief_md"])
    save_report(json_report, output_files["industry_intelligence_brief_json"])
    save_report(final_summary_zh, output_files["final_demo_summary_zh_md"])

    if export_excel:
        generate_excel_report(
            company_profile_df=company_profile_df,
            news_df=news_df,
            kri_df=kri_df,
            dashboard_df=dashboard_df,
            output_path=output_files["excel_workbook"],
        )

    return {key: str(value) for key, value in output_files.items()}


def _load_or_collect_news(
    company: str,
    industry: str,
    sample_news_path: Path,
    project_root: Path,
    use_sample_data: bool,
) -> pd.DataFrame:
    """Load sample news first; try RSS only when sample mode is disabled."""
    if use_sample_data:
        return load_sample_news(sample_news_path)

    try:
        rss_path = project_root / "configs" / "rss_sources.yaml"
        rss_sources = load_rss_sources(rss_path)
        frames = [
            fetch_rss_articles(company, rss_sources),
            fetch_rss_articles(industry, rss_sources),
        ]
        news_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["url", "title"])
        if not news_df.empty:
            return news_df
    except Exception as exc:
        logger.exception("RSS collection failed, falling back to sample news: %s", exc)

    return load_sample_news(sample_news_path)


def _load_annual_report_text(
    annual_report: str | Path | None,
    company_name: str,
    industry: str,
    project_root: Path,
    use_sample_data: bool,
) -> str:
    """Read PDF annual report or generate sample text for the demo."""
    if annual_report:
        path = _resolve_path(annual_report, project_root)
        if path.exists():
            text = extract_text_from_pdf(path)
            if text:
                return text
        logger.warning("Annual report path not found or unreadable: %s", path)

    if use_sample_data:
        return generate_sample_annual_report_text(company_name, industry)
    return ""


def _load_or_generate_trend_notes(company_name: str, industry: str, project_root: Path) -> dict[str, Any]:
    """Use demo trend notes if available, otherwise create simple notes."""
    demo_path = project_root / "data" / "demo" / "sample_industry_trend_notes.json"
    if demo_path.exists():
        try:
            return json.loads(demo_path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Could not read demo trend notes.")
    return {
        "industry": industry,
        "main_trends": [
            f"{industry} demand is influenced by AI adoption, capacity planning, and supply chain resilience.",
        ],
        "growth_drivers": ["AI infrastructure investment", "Enterprise digital transformation"],
        "risks": ["Supply chain disruption", "Customer concentration", "Geopolitical uncertainty"],
        "digital_transformation_opportunities": [
            "Demand forecasting dashboard",
            "Supplier risk monitoring",
            "Working capital early-warning dashboard",
        ],
    }


def _extract_all_kri(news_df: pd.DataFrame, annual_text: str, company_name: str, industry: str) -> pd.DataFrame:
    """Extract KRI evidence from news summaries and annual report text."""
    frames = []
    if not news_df.empty:
        news_text = " ".join((news_df["title"].fillna("") + ". " + news_df["summary"].fillna("")).astype(str).tolist())
        frames.append(extract_kri_mentions(news_text, "news_articles", "news", company_name=company_name, industry=industry))
    if annual_text:
        frames.append(extract_kri_mentions(annual_text, "annual_report_text", "annual_report", company_name=company_name, industry=industry))
    if not frames:
        return pd.DataFrame(columns=[
            "source_id", "company_name", "industry", "source_type", "kri_category",
            "matched_keyword", "evidence_sentence", "severity_hint", "risk_score_hint",
        ])
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["kri_category", "evidence_sentence"])


def _resolve_path(path_value: str | Path | None, project_root: Path) -> Path:
    path = Path(path_value or "")
    return path if path.is_absolute() else project_root / path
