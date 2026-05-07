"""Streamlit demo app for the Industry Intelligence Agent.

This app is designed for an interview demo, not production. It keeps the UI
simple while showing the full workflow: company lookup, news signals, annual
report reading, KRI extraction, trend notes, and report generation.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

import altair as alt

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
    generate_markdown_report_zh,
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
    st.set_page_config(page_title="產業情報代理人 | Industry Intelligence Agent", layout="wide")
    st.title("產業情報代理人 | Industry Intelligence Agent")
    st.caption("互動式產業情報分析工具，支援新聞擷取、KRI 風險辨識與中文報告產生。"
               "  ·  Interactive demo for news signals, KRI extraction, and industry brief generation.")

    inputs = render_sidebar()
    initialize_state()

    # Row 1: language toggle
    lang = st.radio(
        "報告語言 | Report language",
        ["中文", "English"],
        horizontal=True,
        key="lang_top",
        label_visibility="collapsed",
    )

    # Row 2: action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ 執行分析 | Run Analysis", type="primary", use_container_width=True):
            run_analysis(inputs)
    with col2:
        if st.button("📄 產生報告 | Generate Report", use_container_width=True):
            generate_report(inputs["use_llm"], lang="zh" if lang == "中文" else "en")

    render_tabs()


def render_sidebar() -> dict[str, Any]:
    """Render sidebar inputs and return their values."""
    with st.sidebar:
        st.header("Inputs")
        company_name = st.text_input("Company name", value="TSMC")
        ticker = st.text_input("Ticker", value="2330.TW")
        industry = st.text_input("Industry", value="semiconductor")
        uploaded_pdf = st.file_uploader("Annual report PDF upload", type=["pdf"])
        use_demo_data = st.checkbox("Use demo data (interview mode)", value=True)
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
        "use_demo_data": use_demo_data,
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


def load_demo_data(inputs: dict[str, Any]) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Load pre-built demo CSVs/JSON for interview mode."""
    base = PROJECT_ROOT / "data" / "demo"
    news_df = pd.read_csv(base / "sample_news_articles.csv")
    with open(base / "sample_industry_trend_notes.json", encoding="utf-8") as f:
        trend_notes = json.load(f)
    kri_df = pd.read_csv(base / "sample_kri_extraction_results.csv")
    if "company_or_industry" in kri_df.columns and "company_name" not in kri_df.columns:
        kri_df["company_name"] = inputs["company_name"] or kri_df["company_or_industry"]
        kri_df["industry"] = trend_notes.get("industry", inputs["industry"])
    return news_df, trend_notes, kri_df


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

        # Always read the uploaded PDF (annual report) regardless of demo mode
        annual_report_data = safe_read_uploaded_pdf(inputs["uploaded_pdf"])
        annual_report_chunks = annual_report_data.get("chunks", [])
        annual_report_summary = build_annual_report_summary(annual_report_data)

        if inputs["use_demo_data"]:
            news_df, trend_notes, base_kri_df = load_demo_data(inputs)
            # Merge demo KRI with any KRI extracted from the uploaded PDF
            if annual_report_chunks:
                pdf_kri = safe_extract_kri(pd.DataFrame(), annual_report_chunks, inputs)
                kri_df = pd.concat([base_kri_df, pdf_kri], ignore_index=True) if not pdf_kri.empty else base_kri_df
                # Update trend notes to include PDF signals
                combined_text = combine_evidence_text(pd.DataFrame(), annual_report_summary)
                if combined_text:
                    pdf_trends = convert_to_trend_notes(combined_text, industry=inputs["industry"])
                    for key in ["main_trends", "growth_drivers", "risks"]:
                        if pdf_trends.get(key):
                            existing = trend_notes.get(key) or []
                            trend_notes[key] = existing + [f"[年報] {s}" for s in pdf_trends[key]]
            else:
                kri_df = base_kri_df
        else:
            news_df = safe_fetch_news(inputs)
            combined_text = combine_evidence_text(news_df, annual_report_summary)
            trend_notes = convert_to_trend_notes(combined_text, industry=inputs["industry"]) if combined_text else {"industry": inputs["industry"]}
            kri_df = safe_extract_kri(news_df, annual_report_chunks, inputs)

        news_df = score_source_relevance(
            news_df,
            {"company_name": inputs["company_name"], "ticker": inputs["ticker"], "industry": inputs["industry"]},
            {"industry": inputs["industry"]},
        )
        dashboard_df = build_dashboard_table(news_df, kri_df, trend_notes)

        st.session_state.company_profile = company_profile
        st.session_state.news_df = news_df
        st.session_state.kri_df = kri_df
        st.session_state.trend_notes = trend_notes
        st.session_state.annual_report_data = annual_report_data
        st.session_state.annual_report_summary = annual_report_summary
        st.session_state.dashboard_df = dashboard_df

    st.success("Analysis complete.")


def generate_report(use_llm: bool, lang: str = "zh") -> None:
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
    elif lang == "zh":
        markdown_report = generate_markdown_report_zh(
            company_profile=st.session_state.company_profile,
            news_df=st.session_state.news_df,
            kri_df=st.session_state.kri_df,
            industry_trend_json=st.session_state.trend_notes,
            annual_report_summary=st.session_state.annual_report_summary,
        )
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


def _render_report_dashboard() -> None:
    """Metric cards + Altair charts above the report text."""
    news_df = st.session_state.news_df
    kri_df = st.session_state.kri_df

    # ── Metric cards ──────────────────────────────────────────────────────────
    def _sev_count(sev: str) -> int:
        if kri_df.empty or "severity_hint" not in kri_df.columns:
            return 0
        return int((kri_df["severity_hint"].str.lower() == sev).sum())

    high, medium, low = _sev_count("high"), _sev_count("medium"), _sev_count("low")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("新聞訊號 | News", len(news_df))
    m2.metric("KRI 項目 | Items", len(kri_df))
    m3.metric("🔴 高 High", high)
    m4.metric("🟡 中 Medium", medium)
    m5.metric("🟢 低 Low", low)

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    if not kri_df.empty and "severity_hint" in kri_df.columns and "kri_category" in kri_df.columns:
        col_l, col_r = st.columns(2)

        # Left: severity bar chart
        with col_l:
            st.markdown("**KRI 嚴重度分佈 | Severity Distribution**")
            sev_labels = {"high": "高 High", "medium": "中 Medium", "low": "低 Low"}
            sev_df = (
                kri_df["severity_hint"].str.lower()
                .value_counts()
                .reindex(["high", "medium", "low"], fill_value=0)
                .reset_index()
            )
            sev_df.columns = ["severity", "count"]
            sev_df["label"] = sev_df["severity"].map(sev_labels)
            chart_sev = (
                alt.Chart(sev_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("label:N", sort=["高 High", "中 Medium", "低 Low"], title="", axis=alt.Axis(labelFontSize=13)),
                    y=alt.Y("count:Q", title="項目數", axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color(
                        "label:N",
                        scale=alt.Scale(
                            domain=["高 High", "中 Medium", "低 Low"],
                            range=["#d62728", "#ff7f0e", "#2ca02c"],
                        ),
                        legend=None,
                    ),
                    tooltip=[alt.Tooltip("label:N", title="嚴重度"), alt.Tooltip("count:Q", title="項目數")],
                )
                .properties(height=220)
            )
            st.altair_chart(chart_sev, use_container_width=True)

        # Right: KRI category pie / donut chart
        with col_r:
            st.markdown("**KRI 類別分佈 | Category Breakdown**")
            cat_df = kri_df["kri_category"].value_counts().reset_index()
            cat_df.columns = ["category", "count"]
            chart_cat = (
                alt.Chart(cat_df)
                .mark_arc(innerRadius=45, outerRadius=95)
                .encode(
                    theta=alt.Theta("count:Q"),
                    color=alt.Color(
                        "category:N",
                        scale=alt.Scale(scheme="tableau20"),
                        legend=alt.Legend(title="KRI 類別", labelFontSize=11, titleFontSize=12),
                    ),
                    tooltip=[alt.Tooltip("category:N", title="類別"), alt.Tooltip("count:Q", title="項目數")],
                )
                .properties(height=240)
            )
            st.altair_chart(chart_cat, use_container_width=True)

    # KRI date timeline (replaces news relevance chart)
    if not kri_df.empty and "published_date" in kri_df.columns and "kri_category" in kri_df.columns:
        st.markdown("**KRI 風險訊號時間軸 | Risk Signal Timeline**")
        tdf = kri_df[["published_date", "kri_category", "severity_hint", "evidence_sentence"]].copy()
        tdf["published_date"] = pd.to_datetime(tdf["published_date"], errors="coerce")
        tdf = tdf.dropna(subset=["published_date"])
        tdf["evidence_short"] = tdf["evidence_sentence"].str[:60] + "…"
        chart_time = (
            alt.Chart(tdf)
            .mark_circle(size=120)
            .encode(
                x=alt.X("published_date:T", title="日期"),
                y=alt.Y("kri_category:N", title="", sort="-x", axis=alt.Axis(labelFontSize=11)),
                color=alt.Color(
                    "severity_hint:N",
                    scale=alt.Scale(
                        domain=["high", "medium", "low"],
                        range=["#d62728", "#ff7f0e", "#2ca02c"],
                    ),
                    legend=alt.Legend(title="嚴重度"),
                ),
                tooltip=[
                    alt.Tooltip("published_date:T", title="日期"),
                    alt.Tooltip("kri_category:N", title="類別"),
                    alt.Tooltip("severity_hint:N", title="嚴重度"),
                    alt.Tooltip("evidence_short:N", title="證據"),
                ],
            )
            .properties(height=max(200, len(kri_df["kri_category"].unique()) * 35))
        )
        st.altair_chart(chart_time, use_container_width=True)

    st.divider()


def _render_report_sections(report_md: str) -> None:
    """Split report by ## headers and display each section in a bordered card."""
    # Split into [pre_header_text, "## Title", body, "## Title", body, ...]
    parts = re.split(r"\n(## .+)", report_md)

    # Render the title block (everything before first ## section)
    if parts[0].strip():
        st.markdown(parts[0])

    # Pair up (title, body) for each ## section
    i = 1
    while i < len(parts) - 1:
        title = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        # Guardrails section gets an info box instead of a card
        if "guardrail" in title.lower() or "使用聲明" in title:
            st.info(f"{title}\n\n{body.strip()}")
        else:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(body.strip())
        i += 2


_WC_CATEGORIES = {"inventory risk", "receivables risk", "cash flow risk", "liquidity risk", "profitability risk"}


def _kri_pivot(kri_df: pd.DataFrame) -> pd.DataFrame:
    """COUNTIFS equivalent: KRI category × severity count table."""
    if kri_df.empty or "kri_category" not in kri_df.columns:
        return pd.DataFrame()
    pivot = (
        kri_df.groupby(["kri_category", "severity_hint"])
        .size()
        .unstack(fill_value=0)
    )
    for col in ["high", "medium", "low"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[["high", "medium", "low"]]
    pivot.columns = ["🔴 高 High", "🟡 中 Medium", "🟢 低 Low"]
    pivot["合計 Total"] = pivot.sum(axis=1)
    return pivot.sort_values("合計 Total", ascending=False).reset_index().rename(
        columns={"kri_category": "KRI 類別"}
    )


def _render_kri_dashboard(kri_df: pd.DataFrame, news_df: pd.DataFrame) -> None:
    """Full KPI/KRI dashboard: filters, clean table, pivot, WC section, source comparison."""
    st.subheader("KPI / KRI 風險情報儀表板")

    if kri_df.empty:
        st.info("請先執行分析以載入 KRI 資料。")
        return

    # ── Filters ───────────────────────────────────────────────────────────────
    all_severities = ["high", "medium", "low"]
    all_categories = sorted(kri_df["kri_category"].dropna().unique().tolist()) if "kri_category" in kri_df.columns else []

    fc1, fc2 = st.columns(2)
    with fc1:
        sel_sev = st.multiselect(
            "嚴重度篩選 | Filter by Severity",
            options=all_severities,
            default=all_severities,
            format_func=lambda s: {"high": "🔴 高 High", "medium": "🟡 中 Medium", "low": "🟢 低 Low"}.get(s, s),
        )
    with fc2:
        sel_cat = st.multiselect(
            "風險類別篩選 | Filter by Category",
            options=all_categories,
            default=all_categories,
        )

    mask = pd.Series(True, index=kri_df.index)
    if "severity_hint" in kri_df.columns and sel_sev:
        mask &= kri_df["severity_hint"].str.lower().isin(sel_sev)
    if "kri_category" in kri_df.columns and sel_cat:
        mask &= kri_df["kri_category"].isin(sel_cat)
    filtered = kri_df[mask].copy()

    # ── Clean evidence table ───────────────────────────────────────────────────
    st.markdown(f"**KRI 風險證據表（{len(filtered)} 項）**")
    display_cols = [c for c in [
        "published_date", "kri_category", "severity_hint",
        "source_type", "evidence_sentence",
        "analytical_interpretation", "recommended_follow_up_zh",
    ] if c in filtered.columns]
    col_labels = {
        "published_date": "日期",
        "kri_category": "風險類別",
        "severity_hint": "嚴重度",
        "source_type": "來源類型",
        "evidence_sentence": "證據句（英）",
        "analytical_interpretation": "分析解讀（中）",
        "recommended_follow_up_zh": "建議追問",
    }
    display_df = filtered[display_cols].rename(columns=col_labels)
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={"嚴重度": st.column_config.TextColumn(width="small")},
    )
    st.download_button(
        "⬇ 下載 KRI 證據 CSV",
        data=dataframe_to_csv(filtered),
        file_name="kri_evidence_table.csv",
        mime="text/csv",
    )

    st.divider()

    # ── COUNTIFS Pivot Table ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("**📊 KRI 類別 × 嚴重度樞紐表（COUNTIFS 等效）**")
        pivot_df = _kri_pivot(filtered)
        if not pivot_df.empty:
            st.dataframe(pivot_df, use_container_width=True, hide_index=True)
            # Stacked bar chart
            melt = pivot_df.melt(
                id_vars="KRI 類別",
                value_vars=["🔴 高 High", "🟡 中 Medium", "🟢 低 Low"],
                var_name="嚴重度",
                value_name="項目數",
            )
            chart_pivot = (
                alt.Chart(melt)
                .mark_bar()
                .encode(
                    x=alt.X("項目數:Q", title="項目數", stack="zero"),
                    y=alt.Y("KRI 類別:N", sort="-x", title=""),
                    color=alt.Color(
                        "嚴重度:N",
                        scale=alt.Scale(
                            domain=["🔴 高 High", "🟡 中 Medium", "🟢 低 Low"],
                            range=["#d62728", "#ff7f0e", "#2ca02c"],
                        ),
                    ),
                    tooltip=["KRI 類別", "嚴重度", "項目數"],
                )
                .properties(height=max(180, len(pivot_df) * 30))
            )
            st.altair_chart(chart_pivot, use_container_width=True)

    # ── Working Capital / Operational KPI Section ──────────────────────────────
    wc_mask = kri_df["kri_category"].str.lower().isin(_WC_CATEGORIES) if "kri_category" in kri_df.columns else pd.Series(False, index=kri_df.index)
    wc_df = kri_df[wc_mask]

    with st.container(border=True):
        st.markdown("**💰 營運資金 & 財務 KRI 專區**")
        st.caption("涵蓋：庫存風險、應收帳款、現金流、流動性、獲利能力")
        if wc_df.empty:
            st.info("目前無營運資金相關 KRI 證據。")
        else:
            wc_cols = [c for c in ["published_date", "kri_category", "severity_hint", "evidence_sentence", "analytical_interpretation"] if c in wc_df.columns]
            wc_labels = {"published_date": "日期", "kri_category": "風險類別", "severity_hint": "嚴重度",
                         "evidence_sentence": "證據句", "analytical_interpretation": "分析解讀"}
            st.dataframe(wc_df[wc_cols].rename(columns=wc_labels), use_container_width=True, hide_index=True)

            # KPI tracking reminder
            kpi_items = [
                ("庫存天數 Days Inventory Outstanding", "inventory risk"),
                ("應收帳款天數 Days Sales Outstanding", "receivables risk"),
                ("現金轉換週期 Cash Conversion Cycle", "cash flow risk"),
                ("流動比率 Current Ratio", "liquidity risk"),
                ("毛利率 Gross Margin %", "profitability risk"),
            ]
            st.markdown("**追蹤指標清單**")
            for kpi, cat in kpi_items:
                flag = "🔴" if cat in wc_df["kri_category"].str.lower().values else "⬜"
                st.markdown(f"- {flag} {kpi}")

    # ── News vs Annual Report Comparison ──────────────────────────────────────
    if "source_type" in kri_df.columns and kri_df["source_type"].nunique() > 1:
        with st.container(border=True):
            st.markdown("**📰 新聞訊號 vs 年報風險語言對比**")
            src_pivot = (
                kri_df.groupby(["kri_category", "source_type"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
                .rename(columns={"kri_category": "KRI 類別"})
            )
            st.dataframe(src_pivot, use_container_width=True, hide_index=True)
            st.caption("⚠️ 同時出現在新聞與年報的類別，代表管理層與市場對該風險已有共識；僅出現在新聞的類別，可能是管理層尚未公開揭露的認知差距。")


def render_tabs() -> None:
    """Render the main page tabs."""
    tabs = st.tabs(
        [
            "公司基本資料",
            "新聞訊號擷取",
            "KRI 風險證據",
            "產業趨勢",
            "產業情報簡報",
        ]
    )

    with tabs[0]:
        st.subheader("公司基本資料")
        profile = st.session_state.company_profile
        if profile:
            st.dataframe(pd.DataFrame([profile]), use_container_width=True)
        else:
            st.info("請先點擊「Run analysis」載入公司資料。")

    with tabs[1]:
        st.subheader("新聞訊號擷取")
        st.dataframe(st.session_state.news_df, use_container_width=True)
        st.download_button(
            "下載新聞訊號 CSV",
            data=dataframe_to_csv(st.session_state.news_df),
            file_name="business_signal_extraction.csv",
            mime="text/csv",
        )

    with tabs[2]:
        _render_kri_dashboard(st.session_state.kri_df, st.session_state.news_df)

    with tabs[3]:
        st.subheader("產業趨勢")
        trend_notes = st.session_state.trend_notes
        if not trend_notes or trend_notes == {"industry": ""}:
            st.info("請先點擊「Run analysis」載入趨勢資料。")
        else:
            _render_trend_notes(trend_notes)
        st.subheader("數位轉型機會地圖")
        st.dataframe(
            build_digital_transformation_opportunity_map(trend_notes, st.session_state.kri_df),
            use_container_width=True,
        )

    with tabs[4]:
        st.subheader("產業情報簡報 | Industry Intelligence Brief")
        _render_report_dashboard()
        if st.session_state.markdown_report:
            st.download_button(
                "⬇ 下載報告 (.md)",
                data=st.session_state.markdown_report,
                file_name="industry_intelligence_brief.md",
                mime="text/markdown",
            )
            _render_report_sections(st.session_state.markdown_report)
        else:
            st.info("步驟：① 執行分析 → ② 選擇語言 → ③ 產生報告")


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


def _render_trend_notes(trend_notes: dict[str, Any]) -> None:
    """Render trend notes as formatted Markdown sections instead of raw dict."""
    label_map = {
        "main_trends": "主要趨勢",
        "growth_drivers": "成長驅動因素",
        "risks": "風險訊號",
        "key_companies": "主要公司",
        "data_indicators": "關鍵資料指標",
        "digital_transformation_opportunities": "數位轉型機會",
    }
    for key, label in label_map.items():
        items = trend_notes.get(key)
        if not items:
            continue
        st.markdown(f"**{label}**")
        for item in items:
            st.markdown(f"- {item}")


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
