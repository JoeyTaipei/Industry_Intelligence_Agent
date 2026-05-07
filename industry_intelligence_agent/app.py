"""Streamlit web app MVP for the Industry Intelligence Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.annual_report_reader import build_annual_report_evidence_rows, read_annual_report_pdf
from src.excel_report_generator import generate_excel_report
from src.industry_trend_reader import convert_to_trend_notes
from src.kri_extractor import extract_kri_mentions
from src.news_collector import fetch_google_news_rss, generate_sample_news, save_articles
from src.report_generator import (
    build_dashboard_kpi_kri_table,
    generate_chinese_report,
    generate_final_demo_summary_zh,
)


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
REPORT_DIR = DATA_DIR / "reports"
TEMP_DIR = DATA_DIR / "temp"

NEWS_CSV = EXPORT_DIR / "news_articles.csv"
ANNUAL_EVIDENCE_CSV = EXPORT_DIR / "annual_report_evidence.csv"
KRI_CSV = EXPORT_DIR / "kri_evidence.csv"
DASHBOARD_CSV = EXPORT_DIR / "dashboard_ready.csv"
CHINESE_REPORT_MD = REPORT_DIR / "chinese_report.md"
FINAL_SUMMARY_MD = REPORT_DIR / "final_demo_summary_zh.md"
EXCEL_REPORT = REPORT_DIR / "industry_intelligence_demo.xlsx"


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="Industry Intelligence Agent", layout="wide")
    ensure_folders()

    st.title("Industry Intelligence Agent")
    st.caption("產業新聞、年報與 KRI 風險證據分析 MVP")

    inputs = render_inputs()

    if st.button("Run Analysis", type="primary", use_container_width=True):
        run_analysis(inputs)

    if "results" in st.session_state:
        render_results(st.session_state["results"])


def render_inputs() -> dict[str, Any]:
    """Render app inputs."""
    with st.sidebar:
        st.header("分析設定")
        company_name = st.text_input("Company name", value="Apple")
        ticker = st.text_input("Ticker", value="AAPL")
        industry_keyword = st.text_input(
            "Industry keyword",
            value="consumer electronics semiconductor supply chain",
        )
        default_query = f"{company_name} {industry_keyword} tariff supply chain risk".strip()
        news_query = st.text_input(
            "News query",
            value=default_query,
        )
        annual_report_pdf = st.file_uploader("Annual report PDF", type=["pdf"])
        max_news_articles = st.slider("Max news articles", min_value=5, max_value=30, value=10, step=1)
        export_excel = st.checkbox("Export Excel", value=True)
        language = st.selectbox("Language", ["zh-TW", "en"], index=0)

    return {
        "company_name": company_name.strip(),
        "ticker": ticker.strip(),
        "industry_keyword": industry_keyword.strip(),
        "news_query": news_query.strip(),
        "annual_report_pdf": annual_report_pdf,
        "max_news_articles": max_news_articles,
        "export_excel": export_excel,
        "language": language,
    }


def run_analysis(inputs: dict[str, Any]) -> None:
    """Run the MVP workflow and persist output files."""
    company_profile = {
        "company_name": inputs["company_name"],
        "ticker": inputs["ticker"],
        "industry": inputs["industry_keyword"],
        "source": "user_input",
    }

    with st.spinner("正在擷取 Google News RSS、解析年報並抽取 KRI evidence..."):
        news_df = fetch_news(inputs)
        annual_report_data = read_uploaded_annual_report(inputs)
        annual_evidence_df = build_annual_evidence_dataframe(annual_report_data, inputs)
        kri_df = build_kri_dataframe(news_df, annual_report_data, inputs)
        trend_notes = build_trend_notes(news_df, annual_report_data, inputs)
        dashboard_df = build_dashboard_kpi_kri_table(news_df, kri_df, {"industry": inputs["industry_keyword"], **trend_notes})

        chinese_report = generate_chinese_report(
            company_profile=company_profile,
            news_df=news_df,
            annual_report_evidence_df=annual_evidence_df,
            kri_df=kri_df,
            dashboard_df=dashboard_df,
            output_path=CHINESE_REPORT_MD,
        )
        final_summary = generate_final_demo_summary_zh(
            company_name=inputs["company_name"],
            industry=inputs["industry_keyword"],
            output_path=FINAL_SUMMARY_MD,
        )

        save_outputs(news_df, annual_evidence_df, kri_df, dashboard_df)
        excel_path = None
        if inputs["export_excel"]:
            excel_path = generate_excel_report(
                news_df=news_df,
                annual_report_evidence_df=annual_evidence_df,
                kri_df=kri_df,
                dashboard_df=dashboard_df,
                chinese_summary=final_summary,
                output_path=EXCEL_REPORT,
            )

    st.session_state["results"] = {
        "inputs": inputs,
        "company_profile": company_profile,
        "news_df": news_df,
        "annual_report_data": annual_report_data,
        "annual_evidence_df": annual_evidence_df,
        "kri_df": kri_df,
        "trend_notes": trend_notes,
        "dashboard_df": dashboard_df,
        "chinese_report": chinese_report,
        "final_summary": final_summary,
        "excel_path": excel_path,
    }
    st.success("分析完成。")


def fetch_news(inputs: dict[str, Any]) -> pd.DataFrame:
    """Fetch Google News RSS and fall back to sample rows if needed."""
    news_df = fetch_google_news_rss(
        query=inputs["news_query"],
        max_articles=inputs["max_news_articles"],
        company_name=inputs["company_name"],
        industry=inputs["industry_keyword"],
    )
    if news_df.empty:
        st.warning("Google News RSS 擷取失敗或沒有結果，已改用 sample news 讓 demo 繼續。")
        news_df = generate_sample_news(
            company_name=inputs["company_name"],
            industry=inputs["industry_keyword"],
            keyword=inputs["news_query"],
        )
    return news_df


def read_uploaded_annual_report(inputs: dict[str, Any]) -> dict[str, Any]:
    """Save and read the uploaded annual report PDF."""
    uploaded_pdf = inputs.get("annual_report_pdf")
    if uploaded_pdf is None:
        return {
            "pdf_path": "",
            "raw_text": "",
            "cleaned_text": "",
            "sections": {},
            "prioritized_text": "",
            "chunks": [],
            "metadata": {},
        }

    safe_name = Path(uploaded_pdf.name).name
    upload_path = UPLOAD_DIR / safe_name
    upload_path.write_bytes(uploaded_pdf.getbuffer())
    return read_annual_report_pdf(upload_path)


def build_annual_evidence_dataframe(annual_report_data: dict[str, Any], inputs: dict[str, Any]) -> pd.DataFrame:
    """Create section-level annual report evidence for display/export."""
    rows = build_annual_report_evidence_rows(
        annual_report_data,
        company_name=inputs["company_name"],
        industry=inputs["industry_keyword"],
    )
    return pd.DataFrame(
        rows,
        columns=[
            "company_name",
            "industry",
            "section",
            "priority",
            "evidence_text",
            "source_type",
            "source_id",
        ],
    )


def build_kri_dataframe(news_df: pd.DataFrame, annual_report_data: dict[str, Any], inputs: dict[str, Any]) -> pd.DataFrame:
    """Extract KRI evidence from news rows and annual report priority chunks."""
    frames = []
    news_kri = extract_kri_mentions(
        news_df,
        source_id="google_news",
        source_type="news",
        company_name=inputs["company_name"],
        industry=inputs["industry_keyword"],
    )
    if not news_kri.empty:
        frames.append(news_kri)

    prioritized_text = annual_report_data.get("prioritized_text") or annual_report_data.get("cleaned_text", "")
    if prioritized_text:
        annual_kri = extract_kri_mentions(
            prioritized_text,
            source_id="uploaded_annual_report",
            source_type="annual_report",
            company_name=inputs["company_name"],
            industry=inputs["industry_keyword"],
        )
        if not annual_kri.empty:
            frames.append(annual_kri)

    if not frames:
        return pd.DataFrame(
            columns=[
                "source_id",
                "company_name",
                "industry",
                "source_type",
                "published_date",
                "kri_category",
                "matched_keywords",
                "evidence_sentence",
                "detected_countries",
                "detected_percentages",
                "severity_hint",
                "risk_score_hint",
                "recommended_follow_up",
            ]
        )

    return pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["source_type", "kri_category", "evidence_sentence"]
    )


def build_trend_notes(news_df: pd.DataFrame, annual_report_data: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    """Build lightweight trend notes from available evidence."""
    news_text = " ".join((news_df.get("title", "") + ". " + news_df.get("summary", "")).fillna("").astype(str).tolist()) if not news_df.empty else ""
    annual_text = annual_report_data.get("prioritized_text") or ""
    combined_text = " ".join([news_text, annual_text]).strip()
    if not combined_text:
        return {"industry": inputs["industry_keyword"]}
    return convert_to_trend_notes(combined_text, industry=inputs["industry_keyword"])


def save_outputs(
    news_df: pd.DataFrame,
    annual_evidence_df: pd.DataFrame,
    kri_df: pd.DataFrame,
    dashboard_df: pd.DataFrame,
) -> None:
    """Save standard output files."""
    save_articles(news_df, NEWS_CSV)
    annual_evidence_df.to_csv(ANNUAL_EVIDENCE_CSV, index=False, encoding="utf-8-sig")
    kri_df.to_csv(KRI_CSV, index=False, encoding="utf-8-sig")
    dashboard_df.to_csv(DASHBOARD_CSV, index=False, encoding="utf-8-sig")


def render_results(results: dict[str, Any]) -> None:
    """Render tabs after analysis has run."""
    tabs = st.tabs(
        [
            "公司概況",
            "網路新聞",
            "年報風險證據",
            "KRI Evidence",
            "中文分析報告",
            "Downloads",
        ]
    )

    with tabs[0]:
        st.subheader("公司概況")
        st.dataframe(pd.DataFrame([results["company_profile"]]), use_container_width=True, hide_index=True)
        st.dataframe(results["dashboard_df"], use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("網路新聞")
        st.dataframe(results["news_df"], use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("年報風險證據")
        if results["annual_evidence_df"].empty:
            st.info("尚未上傳年報 PDF，或 PDF 未解析出可用章節。")
        else:
            st.dataframe(results["annual_evidence_df"], use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("KRI Evidence")
        kri_df = results["kri_df"]
        if kri_df.empty:
            st.info("目前沒有抽取到 KRI evidence。")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("High", int((kri_df["severity_hint"] == "high").sum()))
            col2.metric("Medium", int((kri_df["severity_hint"] == "medium").sum()))
            col3.metric("Low", int((kri_df["severity_hint"] == "low").sum()))
            st.dataframe(kri_df, use_container_width=True, hide_index=True)
            st.markdown("**KRI 類別 x 嚴重度**")
            st.dataframe(kri_pivot(kri_df), use_container_width=True, hide_index=True)

    with tabs[4]:
        st.subheader("中文分析報告")
        st.markdown(results["chinese_report"])

    with tabs[5]:
        st.subheader("Downloads")
        render_download("news_articles.csv", NEWS_CSV, "text/csv")
        render_download("annual_report_evidence.csv", ANNUAL_EVIDENCE_CSV, "text/csv")
        render_download("kri_evidence.csv", KRI_CSV, "text/csv")
        render_download("dashboard_ready.csv", DASHBOARD_CSV, "text/csv")
        render_download("chinese_report.md", CHINESE_REPORT_MD, "text/markdown")
        render_download("final_demo_summary_zh.md", FINAL_SUMMARY_MD, "text/markdown")
        if results.get("excel_path"):
            render_download("industry_intelligence_demo.xlsx", EXCEL_REPORT, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def kri_pivot(kri_df: pd.DataFrame) -> pd.DataFrame:
    """Create a COUNTIFS-style KRI pivot table."""
    if kri_df.empty:
        return pd.DataFrame()
    pivot = kri_df.groupby(["kri_category", "severity_hint"]).size().unstack(fill_value=0)
    for column in ["high", "medium", "low"]:
        if column not in pivot.columns:
            pivot[column] = 0
    pivot = pivot[["high", "medium", "low"]]
    pivot["total"] = pivot.sum(axis=1)
    return pivot.sort_values("total", ascending=False).reset_index()


def render_download(label: str, path: Path, mime: str) -> None:
    """Render a download button if a file exists."""
    if not path.exists():
        st.caption(f"{label} 尚未產生")
        return
    st.download_button(
        label=f"下載 {label}",
        data=path.read_bytes(),
        file_name=label,
        mime=mime,
        use_container_width=True,
    )


def ensure_folders() -> None:
    """Create required data folders."""
    for folder in [UPLOAD_DIR, EXPORT_DIR, REPORT_DIR, TEMP_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
