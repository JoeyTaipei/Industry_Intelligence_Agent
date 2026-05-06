"""Streamlit demo app for the Industry Intelligence Agent.

This app is designed for an interview demo, not production. It keeps the UI
simple while showing the full workflow: company lookup, news signals, annual
report reading, KRI extraction, trend notes, and report generation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.annual_report_reader import read_annual_report_pdf
from src.company_registry import get_company_profile, load_company_registry
from src.industry_trend_reader import convert_to_trend_notes
from src.kri_extractor import extract_kri_mentions
from src.news_collector import fetch_rss_articles, load_rss_sources
from src.report_generator import (
    build_dashboard_kpi_kri_table,
    build_digital_transformation_opportunity_map,
    generate_json_report,
    generate_markdown_report,
    score_source_relevance,
)
from src.summarizer import generate_company_brief


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "raw" / "company_registry.csv"
DEFAULT_RSS_CONFIG_PATH = PROJECT_ROOT / "configs" / "rss_sources.yaml"


@st.cache_data(show_spinner=False)
def load_registry_cached(csv_path: str) -> pd.DataFrame:
    """Load company registry data once and cache it for the demo."""
    return load_company_registry(csv_path)


@st.cache_data(show_spinner=False)
def load_rss_sources_cached(config_path: str) -> list[dict[str, str]]:
    """Load RSS source config once and cache it for the demo."""
    return load_rss_sources(config_path)


@st.cache_data(show_spinner=False)
def fetch_news_cached(
    company_keyword: str,
    industry_keyword: str,
    rss_config_path: str,
    max_articles: int,
) -> pd.DataFrame:
    """Fetch RSS news for company and industry keywords."""
    rss_sources = load_rss_sources_cached(rss_config_path)
    frames: list[pd.DataFrame] = []

    for keyword in dict.fromkeys([company_keyword, industry_keyword]):
        if not keyword:
            continue
        frame = fetch_rss_articles(keyword=keyword, rss_sources=rss_sources, max_articles=max_articles)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["source", "title", "url", "published_date", "summary", "keyword"])

    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return combined

    return combined.drop_duplicates(subset=["url", "title"]).reset_index(drop=True)


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="Industry Intelligence Agent", layout="wide")
    st.title("Industry Intelligence Agent")
    st.caption("Interactive demo for producing an Industry Intelligence Brief and KRI Evidence Table.")

    inputs = render_sidebar()
    initialize_state()

    col1, col2 = st.columns([1, 1])
    with col1:
        run_clicked = st.button("Run analysis", type="primary", use_container_width=True)
    with col2:
        report_clicked = st.button("Generate report", use_container_width=True)

    if run_clicked:
        run_analysis(inputs)

    if report_clicked:
        generate_report(inputs["use_llm"])

    render_tabs()


def render_sidebar() -> dict[str, Any]:
    """Render sidebar inputs and return their values."""
    with st.sidebar:
        st.header("Inputs")
        company_name = st.text_input("Company name", value="TSMC")
        ticker = st.text_input("Ticker", value="2330.TW")
        industry = st.text_input("Industry", value="semiconductor")
        uploaded_pdf = st.file_uploader("Annual report PDF upload", type=["pdf"])
        use_llm = st.checkbox("Use LLM", value=False)

        st.divider()
        max_news = st.slider("Max news articles", min_value=0, max_value=50, value=20, step=5)
        registry_path = st.text_input("Registry CSV", value=str(DEFAULT_REGISTRY_PATH))
        rss_config_path = st.text_input("RSS config", value=str(DEFAULT_RSS_CONFIG_PATH))

    return {
        "company_name": company_name.strip(),
        "ticker": ticker.strip(),
        "industry": industry.strip(),
        "uploaded_pdf": uploaded_pdf,
        "use_llm": use_llm,
        "max_news": max_news,
        "registry_path": registry_path,
        "rss_config_path": rss_config_path,
    }


def initialize_state() -> None:
    """Create default session state values."""
    defaults = {
        "company_profile": {},
        "news_df": pd.DataFrame(),
        "kri_df": pd.DataFrame(),
        "trend_notes": {"industry": ""},
        "annual_report_data": {},
        "annual_report_summary": "",
        "dashboard_df": pd.DataFrame(),
        "markdown_report": "",
        "json_report": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_analysis(inputs: dict[str, Any]) -> None:
    """Run data collection and extraction steps."""
    with st.spinner("Running analysis..."):
        registry_df = safe_load_registry(inputs["registry_path"])
        company_profile = safe_get_company_profile(
            registry_df=registry_df,
            company_name=inputs["company_name"],
            ticker=inputs["ticker"],
            industry=inputs["industry"],
        )

        news_df = safe_fetch_news(inputs)
        news_df = score_source_relevance(
            news_df,
            {"company_name": inputs["company_name"], "ticker": inputs["ticker"], "industry": inputs["industry"]},
            {"industry": inputs["industry"]},
        )
        annual_report_data = safe_read_uploaded_pdf(inputs["uploaded_pdf"])
        annual_report_chunks = annual_report_data.get("chunks", [])
        annual_report_summary = build_annual_report_summary(annual_report_data)

        combined_text = combine_evidence_text(news_df, annual_report_summary)
        trend_notes = convert_to_trend_notes(combined_text, industry=inputs["industry"]) if combined_text else {"industry": inputs["industry"]}

        kri_df = safe_extract_kri(news_df, annual_report_chunks, inputs)
        dashboard_df = build_dashboard_table(news_df, kri_df, trend_notes)

        st.session_state.company_profile = company_profile
        st.session_state.news_df = news_df
        st.session_state.kri_df = kri_df
        st.session_state.trend_notes = trend_notes
        st.session_state.annual_report_data = annual_report_data
        st.session_state.annual_report_summary = annual_report_summary
        st.session_state.dashboard_df = dashboard_df

    st.success("Analysis complete.")


def generate_report(use_llm: bool) -> None:
    """Generate Markdown and JSON reports from current session evidence."""
    input_data = {
        "company_profile": st.session_state.company_profile,
        "news_df": st.session_state.news_df,
        "kri_df": st.session_state.kri_df,
        "trend_notes": st.session_state.trend_notes,
        "annual_report_chunks": st.session_state.annual_report_data.get("chunks", []),
        "industry": st.session_state.trend_notes.get("industry", ""),
    }

    if use_llm:
        markdown_report = generate_company_brief(input_data, use_llm=True)
    else:
        markdown_report = generate_markdown_report(
            company_profile=st.session_state.company_profile,
            news_df=st.session_state.news_df,
            kri_df=st.session_state.kri_df,
            industry_trend_json=st.session_state.trend_notes,
            annual_report_summary=st.session_state.annual_report_summary,
        )

    json_report = generate_json_report(
        company_profile=st.session_state.company_profile,
        news_df=st.session_state.news_df,
        kri_df=st.session_state.kri_df,
        industry_trend_json=st.session_state.trend_notes,
        annual_report_summary=st.session_state.annual_report_summary,
    )

    st.session_state.markdown_report = markdown_report
    st.session_state.json_report = json_report
    st.success("Report generated.")


def render_tabs() -> None:
    """Render the main page tabs."""
    tabs = st.tabs(
        [
            "Company Profile",
            "Business Signal Extraction",
            "KRI Evidence Table",
            "Industry Trends",
            "Industry Intelligence Brief",
        ]
    )

    with tabs[0]:
        st.subheader("Company Profile")
        profile = st.session_state.company_profile
        if profile:
            st.dataframe(pd.DataFrame([profile]), use_container_width=True)
        else:
            st.info("Run analysis to load a company profile.")

    with tabs[1]:
        st.subheader("Business Signal Extraction")
        st.dataframe(st.session_state.news_df, use_container_width=True)
        st.download_button(
            "Download business signal CSV",
            data=dataframe_to_csv(st.session_state.news_df),
            file_name="business_signal_extraction.csv",
            mime="text/csv",
        )

    with tabs[2]:
        st.subheader("KRI Evidence Table")
        st.dataframe(st.session_state.kri_df, use_container_width=True)
        st.download_button(
            "Download KRI Evidence Table CSV",
            data=dataframe_to_csv(st.session_state.kri_df),
            file_name="kri_evidence_table.csv",
            mime="text/csv",
        )
        st.subheader("Dashboard-ready KPI/KRI Table")
        st.dataframe(st.session_state.dashboard_df, use_container_width=True)

    with tabs[3]:
        st.subheader("Industry Trends")
        trend_notes = st.session_state.trend_notes
        st.json(trend_notes)
        st.dataframe(trend_notes_to_dataframe(trend_notes), use_container_width=True)
        st.subheader("Digital Transformation Opportunity Map")
        st.dataframe(
            build_digital_transformation_opportunity_map(trend_notes, st.session_state.kri_df),
            use_container_width=True,
        )

    with tabs[4]:
        st.subheader("Industry Intelligence Brief")
        if st.session_state.markdown_report:
            st.markdown(st.session_state.markdown_report)
            st.download_button(
                "Download Industry Intelligence Brief",
                data=st.session_state.markdown_report,
                file_name="industry_intelligence_brief.md",
                mime="text/markdown",
            )
        else:
            st.info("Click Generate report after running analysis.")


def safe_load_registry(registry_path: str) -> pd.DataFrame:
    """Load registry data with user-friendly error handling."""
    path = Path(registry_path)
    if not path.exists():
        st.warning(f"Registry CSV not found: {path}")
        return pd.DataFrame()

    try:
        return load_registry_cached(str(path))
    except Exception as exc:
        st.warning(f"Could not load registry CSV: {exc}")
        return pd.DataFrame()


def safe_get_company_profile(
    registry_df: pd.DataFrame,
    company_name: str,
    ticker: str,
    industry: str,
) -> dict[str, Any]:
    """Find company profile or create a minimal profile from sidebar inputs."""
    try:
        profile = get_company_profile(registry_df, company_name=company_name or None, ticker=ticker or None)
    except Exception as exc:
        st.warning(f"Company profile search failed: {exc}")
        profile = {}

    if profile:
        return profile

    return {
        "company_name": company_name,
        "ticker": ticker,
        "industry": industry,
        "source": "sidebar_input",
    }


def safe_fetch_news(inputs: dict[str, Any]) -> pd.DataFrame:
    """Fetch RSS news and continue gracefully if unavailable."""
    if inputs["max_news"] <= 0:
        return pd.DataFrame(columns=["source", "title", "url", "published_date", "summary", "keyword"])

    try:
        return fetch_news_cached(
            company_keyword=inputs["company_name"] or inputs["ticker"],
            industry_keyword=inputs["industry"],
            rss_config_path=inputs["rss_config_path"],
            max_articles=inputs["max_news"],
        )
    except Exception as exc:
        st.warning(f"News collection failed: {exc}")
        return pd.DataFrame(columns=["source", "title", "url", "published_date", "summary", "keyword"])


def safe_read_uploaded_pdf(uploaded_pdf: Any) -> dict[str, Any]:
    """Read an uploaded annual report PDF, if provided."""
    if uploaded_pdf is None:
        return {}

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_pdf.getbuffer())
            temp_path = Path(temp_file.name)

        return read_annual_report_pdf(temp_path)
    except Exception as exc:
        st.warning(f"Annual report reading failed: {exc}")
        return {}
    finally:
        if temp_path:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass


def safe_extract_kri(
    news_df: pd.DataFrame,
    annual_report_chunks: list[dict[str, Any]],
    inputs: dict[str, Any],
) -> pd.DataFrame:
    """Extract KRI evidence from news and annual report chunks."""
    frames: list[pd.DataFrame] = []

    try:
        if not news_df.empty:
            news_text = " ".join(
                (news_df["title"].fillna("").astype(str) + ". " + news_df["summary"].fillna("").astype(str)).tolist()
            )
            news_kri = extract_kri_mentions(news_text, source_id="streamlit_news", source_type="news")
            frames.append(news_kri)
    except Exception as exc:
        st.warning(f"KRI extraction from news failed: {exc}")

    try:
        if annual_report_chunks:
            report_kri = extract_kri_mentions(
                annual_report_chunks,
                source_id="uploaded_annual_report",
                source_type="annual_report",
            )
            frames.append(report_kri)
    except Exception as exc:
        st.warning(f"KRI extraction from annual report failed: {exc}")

    if not frames:
        return pd.DataFrame(
            columns=[
                "source_id",
                "kri_category",
                "matched_keyword",
                "evidence_sentence",
                "severity_hint",
                "source_type",
            ]
        )

    kri_df = pd.concat(frames, ignore_index=True)
    kri_df["company_or_industry"] = inputs["company_name"] or inputs["industry"]
    kri_df = score_source_relevance(
        kri_df,
        {"company_name": inputs["company_name"], "ticker": inputs["ticker"], "industry": inputs["industry"]},
        {"industry": inputs["industry"]},
    )
    return kri_df


def build_annual_report_summary(annual_report_data: dict[str, Any]) -> str:
    """Create a short annual report summary field for the report generator."""
    if not annual_report_data:
        return ""

    sections = annual_report_data.get("sections", {}) or {}
    for key in ["business_overview", "financial_overview", "management_discussion", "risk_factors"]:
        if sections.get(key):
            return sections[key]

    chunks = annual_report_data.get("chunks", [])
    if chunks:
        return chunks[0].get("text", "")

    return annual_report_data.get("cleaned_text", "")[:3000]


def combine_evidence_text(news_df: pd.DataFrame, annual_report_summary: str) -> str:
    """Combine available evidence for rule-based trend extraction."""
    news_text = ""
    if not news_df.empty:
        news_text = " ".join(news_df.get("summary", pd.Series(dtype=str)).fillna("").astype(str).tolist())
    return " ".join([news_text, annual_report_summary]).strip()


def build_dashboard_table(
    news_df: pd.DataFrame,
    kri_df: pd.DataFrame,
    trend_notes: dict[str, Any],
) -> pd.DataFrame:
    """Create a dashboard-ready KPI/KRI table."""
    return build_dashboard_kpi_kri_table(news_df, kri_df, trend_notes)


def trend_notes_to_dataframe(trend_notes: dict[str, Any]) -> pd.DataFrame:
    """Flatten trend notes into a table for display."""
    rows: list[dict[str, Any]] = []
    industry = trend_notes.get("industry", "")
    for key, value in trend_notes.items():
        if key == "industry":
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            rows.append({"industry": industry, "category": key, "item": item})
    return pd.DataFrame(rows, columns=["industry", "category", "item"])


def dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to downloadable CSV bytes."""
    return df.to_csv(index=False).encode("utf-8-sig")


if __name__ == "__main__":
    main()
