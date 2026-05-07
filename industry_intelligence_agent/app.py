"""產業情報代理人 | Industry Intelligence Agent — Streamlit App (Final Edition)."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

import altair as alt
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
    generate_markdown_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR     = PROJECT_ROOT / "data"
DEMO_DIR     = DATA_DIR / "demo"
EXPORT_DIR   = DATA_DIR / "exports"
REPORT_DIR   = DATA_DIR / "reports"
UPLOAD_DIR   = DATA_DIR / "uploads"

DEMO_NEWS_CSV = DEMO_DIR / "sample_news_articles.csv"

_WC_CATEGORIES = {"inventory risk", "receivables risk", "cash flow risk", "liquidity risk", "profitability risk"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    for d in [EXPORT_DIR, REPORT_DIR, UPLOAD_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _sev_count(kri_df: pd.DataFrame, sev: str) -> int:
    if kri_df.empty or "severity_hint" not in kri_df.columns:
        return 0
    return int((kri_df["severity_hint"].str.lower() == sev).sum())


def _dataframe_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


# ── News fetching ─────────────────────────────────────────────────────────────

def _fetch_news(inputs: dict[str, Any]) -> pd.DataFrame:
    """Demo mode: load from pre-built CSV. Live mode: Google News RSS → fallback."""
    company = inputs["company_name"]
    industry = inputs["industry_keyword"]

    if inputs["use_demo_data"]:
        if DEMO_NEWS_CSV.exists():
            df = pd.read_csv(DEMO_NEWS_CSV, dtype=str).fillna("")
            df["company_name"] = company
            return df
        st.warning("Demo news CSV not found — generating sample rows.")
        return generate_sample_news(company_name=company, industry=industry)

    # Live mode: try Google News RSS
    news_df = fetch_google_news_rss(
        query=inputs["news_query"],
        max_articles=inputs["max_news"],
        company_name=company,
        industry=industry,
    )
    if not news_df.empty:
        return news_df

    # Fallback: pre-built CSV if RSS returns nothing
    st.warning("Google News RSS 未返回結果，已載入 demo 新聞供分析繼續。")
    if DEMO_NEWS_CSV.exists():
        df = pd.read_csv(DEMO_NEWS_CSV, dtype=str).fillna("")
        df["company_name"] = company
        return df
    return generate_sample_news(company_name=company, industry=industry, keyword=inputs["news_query"])


# ── PDF reading ───────────────────────────────────────────────────────────────

_EMPTY_ANNUAL: dict[str, Any] = {
    "pdf_path": "", "raw_text": "", "cleaned_text": "",
    "sections": {}, "prioritized_text": "", "chunks": [],
    "extraction_status": "news_only",
    "metadata": {"character_count": 0, "word_count": 0,
                 "has_risk_factors": False, "has_management_discussion": False},
}


def _read_pdf(uploaded_file: Any) -> dict[str, Any]:
    """Save upload to temp file and extract text. Returns empty result if no file."""
    if uploaded_file is None:
        return dict(_EMPTY_ANNUAL)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = Path(tmp.name)
        result = read_annual_report_pdf(tmp_path)
        tmp_path.unlink(missing_ok=True)
        return result
    except Exception as exc:
        st.warning(f"PDF 解析時發生錯誤：{exc}")
        return dict(_EMPTY_ANNUAL)


def _apply_manual_text(annual_data: dict[str, Any], manual_text: str) -> dict[str, Any]:
    """Override annual_data with user-pasted text, save to uploads/, return updated dict."""
    text = manual_text.strip()
    save_path = UPLOAD_DIR / "manual_annual_report_text.txt"
    save_path.write_text(text, encoding="utf-8")

    updated = dict(annual_data)
    updated["cleaned_text"]     = text
    updated["prioritized_text"] = text
    updated["extraction_status"] = "manual_text_used"
    updated["metadata"] = {
        "character_count": len(text),
        "word_count": len(text.split()),
        "has_risk_factors": "risk factor" in text.lower(),
        "has_management_discussion": "management" in text.lower() and "discussion" in text.lower(),
    }
    # Re-chunk for KRI extraction
    from src.annual_report_reader import chunk_text
    updated["chunks"] = chunk_text(text)
    return updated


# ── Report generation ─────────────────────────────────────────────────────────

def _generate_report(inputs: dict[str, Any], lang: str) -> str:
    """Build the report from current session state."""
    r = st.session_state
    company_profile = {
        "company_name": inputs["company_name"],
        "ticker":       inputs["ticker"],
        "industry":     inputs["industry_keyword"],
    }
    extraction_status = r.get("annual_report_data", {}).get("extraction_status", "news_only")
    if lang == "zh":
        return generate_chinese_report(
            company_profile=company_profile,
            news_df=r.get("news_df", pd.DataFrame()),
            annual_report_evidence_df=r.get("annual_evidence_df", pd.DataFrame()),
            kri_df=r.get("kri_df", pd.DataFrame()),
            dashboard_df=r.get("dashboard_df", pd.DataFrame()),
            extraction_status=extraction_status,
        )
    return generate_markdown_report(
        company_profile=company_profile,
        news_df=r.get("news_df", pd.DataFrame()),
        kri_df=r.get("kri_df", pd.DataFrame()),
        industry_trend_json=r.get("trend_notes", {}),
        annual_report_summary=r.get("annual_report_data", {}).get("prioritized_text", ""),
    )


# ── Analysis pipeline ─────────────────────────────────────────────────────────

def _run_analysis(inputs: dict[str, Any]) -> None:
    with st.spinner("分析中..."):
        news_df = _fetch_news(inputs)

        # PDF extraction
        annual_data = _read_pdf(inputs["annual_pdf"])
        char_count = annual_data.get("metadata", {}).get("character_count", 0)

        # Apply manual text override if PDF failed and user pasted text
        manual_text = inputs.get("manual_text", "").strip()
        if inputs["annual_pdf"] and char_count == 0 and manual_text:
            annual_data = _apply_manual_text(annual_data, manual_text)
            char_count = annual_data["metadata"]["character_count"]
            st.info(f"使用手動貼入文字：{char_count:,} 字元。")
        elif inputs["annual_pdf"] and char_count == 0:
            # Mark failed; app will show text_area on next render
            st.session_state["pdf_extraction_failed"] = True
            annual_data["extraction_status"] = "news_only"
        elif inputs["annual_pdf"]:
            st.session_state["pdf_extraction_failed"] = False
            found = [k for k, v in annual_data.get("sections", {}).items() if v]
            st.info(f"年報解析完成：{char_count:,} 字元，找到章節：{found or '（使用全文）'}")

        if not inputs["annual_pdf"]:
            annual_data["extraction_status"] = "news_only"

        annual_evidence_rows = build_annual_report_evidence_rows(
            annual_data,
            company_name=inputs["company_name"],
            industry=inputs["industry_keyword"],
        )
        annual_evidence_df = pd.DataFrame(
            annual_evidence_rows,
            columns=["company_name", "industry", "section", "priority", "evidence_text", "source_type", "source_id"],
        )

        frames = []
        if not news_df.empty:
            frames.append(extract_kri_mentions(
                news_df, source_id="news", source_type="news",
                company_name=inputs["company_name"], industry=inputs["industry_keyword"],
            ))
        prioritized = annual_data.get("prioritized_text") or annual_data.get("cleaned_text", "")
        if prioritized:
            frames.append(extract_kri_mentions(
                prioritized, source_id="annual_report", source_type="annual_report",
                company_name=inputs["company_name"], industry=inputs["industry_keyword"],
            ))
        kri_df = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["source_type", "kri_category", "evidence_sentence"]
        ) if frames else pd.DataFrame()

        news_text  = " ".join((news_df.get("title", "") + ". " + news_df.get("summary", "")).fillna("").tolist()) if not news_df.empty else ""
        annual_txt = annual_data.get("prioritized_text", "")
        trend_notes = convert_to_trend_notes(" ".join([news_text, annual_txt]).strip(),
                                             industry=inputs["industry_keyword"]) if (news_text or annual_txt) else {"industry": inputs["industry_keyword"]}

        dashboard_df = build_dashboard_kpi_kri_table(news_df, kri_df, {"industry": inputs["industry_keyword"]})

        st.session_state["news_df"]            = news_df
        st.session_state["annual_report_data"] = annual_data
        st.session_state["annual_evidence_df"] = annual_evidence_df
        st.session_state["kri_df"]             = kri_df
        st.session_state["trend_notes"]        = trend_notes
        st.session_state["dashboard_df"]       = dashboard_df
        st.session_state["report_md"]          = ""   # clear old report

    st.success(f"分析完成 — 新聞 {len(news_df)} 筆，KRI {len(kri_df)} 筆。")


# ── Charts ────────────────────────────────────────────────────────────────────

def _chart_severity(kri_df: pd.DataFrame) -> None:
    st.markdown("**嚴重度分佈 | Severity**")
    sev_df = (
        kri_df["severity_hint"].str.lower()
        .value_counts().reindex(["high","medium","low"], fill_value=0).reset_index()
    )
    sev_df.columns = ["severity", "count"]
    sev_df["label"] = sev_df["severity"].map({"high":"🔴 High","medium":"🟡 Medium","low":"🟢 Low"})
    st.altair_chart(
        alt.Chart(sev_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("label:N", sort=["🔴 High","🟡 Medium","🟢 Low"], title=""),
            y=alt.Y("count:Q", title="項目數", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("label:N",
                scale=alt.Scale(domain=["🔴 High","🟡 Medium","🟢 Low"], range=["#d62728","#ff7f0e","#2ca02c"]),
                legend=None),
            tooltip=["label:N", "count:Q"],
        ).properties(height=200),
        use_container_width=True,
    )


def _chart_category_donut(kri_df: pd.DataFrame) -> None:
    st.markdown("**類別分佈 | Categories**")
    cat_df = kri_df["kri_category"].value_counts().reset_index()
    cat_df.columns = ["category","count"]
    st.altair_chart(
        alt.Chart(cat_df).mark_arc(innerRadius=45, outerRadius=95).encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("category:N", scale=alt.Scale(scheme="tableau20"),
                legend=alt.Legend(title="KRI 類別", labelFontSize=10)),
            tooltip=["category:N","count:Q"],
        ).properties(height=240),
        use_container_width=True,
    )


def _chart_timeline(kri_df: pd.DataFrame) -> None:
    if "published_date" not in kri_df.columns:
        return
    tdf = kri_df[["published_date","kri_category","severity_hint","evidence_sentence"]].copy()
    tdf["published_date"] = pd.to_datetime(tdf["published_date"], errors="coerce")
    tdf = tdf.dropna(subset=["published_date"])
    if tdf.empty:
        return
    tdf["evidence_short"] = tdf["evidence_sentence"].str[:60] + "…"
    st.markdown("**風險訊號時間軸 | Timeline**")
    st.altair_chart(
        alt.Chart(tdf).mark_circle(size=130).encode(
            x=alt.X("published_date:T", title="日期"),
            y=alt.Y("kri_category:N", title="", sort="-x"),
            color=alt.Color("severity_hint:N",
                scale=alt.Scale(domain=["high","medium","low"], range=["#d62728","#ff7f0e","#2ca02c"]),
                legend=alt.Legend(title="嚴重度")),
            tooltip=["published_date:T","kri_category:N","severity_hint:N","evidence_short:N"],
        ).properties(height=max(180, len(tdf["kri_category"].unique())*36)),
        use_container_width=True,
    )


def _kri_pivot(kri_df: pd.DataFrame) -> pd.DataFrame:
    if kri_df.empty or "kri_category" not in kri_df.columns:
        return pd.DataFrame()
    pivot = kri_df.groupby(["kri_category","severity_hint"]).size().unstack(fill_value=0)
    for c in ["high","medium","low"]:
        if c not in pivot.columns:
            pivot[c] = 0
    pivot = pivot[["high","medium","low"]]
    pivot.columns = ["🔴 High","🟡 Medium","🟢 Low"]
    pivot["合計"] = pivot.sum(axis=1)
    return pivot.sort_values("合計", ascending=False).reset_index().rename(columns={"kri_category":"KRI 類別"})


def _pivot_chart(pivot_df: pd.DataFrame) -> None:
    melt = pivot_df.melt(id_vars="KRI 類別", value_vars=["🔴 High","🟡 Medium","🟢 Low"],
                         var_name="嚴重度", value_name="項目數")
    st.altair_chart(
        alt.Chart(melt).mark_bar().encode(
            x=alt.X("項目數:Q", stack="zero"),
            y=alt.Y("KRI 類別:N", sort="-x", title=""),
            color=alt.Color("嚴重度:N",
                scale=alt.Scale(domain=["🔴 High","🟡 Medium","🟢 Low"], range=["#d62728","#ff7f0e","#2ca02c"])),
            tooltip=["KRI 類別","嚴重度","項目數"],
        ).properties(height=max(180, len(pivot_df)*30)),
        use_container_width=True,
    )


def _render_report_sections(report_md: str) -> None:
    """Display report in bordered section cards."""
    parts = re.split(r"\n(## .+)", report_md)
    if parts[0].strip():
        st.markdown(parts[0])
    i = 1
    while i < len(parts) - 1:
        title, body = parts[i], parts[i+1] if i+1 < len(parts) else ""
        if any(w in title.lower() for w in ["guardrail", "使用聲明", "限制與治理"]):
            st.info(f"{title}\n\n{body.strip()}")
        else:
            with st.container(border=True):
                st.markdown(title)
                st.markdown(body.strip())
        i += 2


# ── Tabs ──────────────────────────────────────────────────────────────────────

def _render_tabs(inputs: dict[str, Any]) -> None:
    news_df         = st.session_state.get("news_df", pd.DataFrame())
    annual_data     = st.session_state.get("annual_report_data", {})
    annual_ev_df    = st.session_state.get("annual_evidence_df", pd.DataFrame())
    kri_df          = st.session_state.get("kri_df", pd.DataFrame())
    dashboard_df    = st.session_state.get("dashboard_df", pd.DataFrame())
    report_md       = st.session_state.get("report_md", "")

    tabs = st.tabs(["公司概況", "新聞訊號", "年報風險證據", "KRI 儀表板", "情報簡報", "下載"])

    # ── Tab 0: Company ────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("公司概況 | Company Profile")
        st.dataframe(pd.DataFrame([{
            "company_name": inputs["company_name"],
            "ticker":       inputs["ticker"],
            "industry":     inputs["industry_keyword"],
        }]), use_container_width=True, hide_index=True)
        if not dashboard_df.empty:
            st.dataframe(dashboard_df, use_container_width=True, hide_index=True)
        else:
            st.info("請先執行分析。")

    # ── Tab 1: News ───────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader("新聞訊號擷取 | News Signals")
        if news_df.empty:
            st.info("請先執行分析。")
        else:
            show_cols = [c for c in ["published_date","source","title","summary","url"] if c in news_df.columns]
            st.dataframe(news_df[show_cols], use_container_width=True, hide_index=True)
            st.download_button("⬇ 下載新聞 CSV", _dataframe_csv(news_df),
                               "news_articles.csv", "text/csv")

    # ── Tab 2: Annual Report ──────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("年報風險證據 | Annual Report Evidence")
        meta   = annual_data.get("metadata", {})
        status = annual_data.get("extraction_status", "news_only")
        _status_badges = {
            "pdf_text_extracted": "🟢 PDF 文字擷取成功",
            "manual_text_used":   "🔵 使用手動貼入文字",
            "news_only":          "⚪ 僅新聞（無年報）",
            "extraction_failed":  "🔴 PDF 擷取失敗",
        }
        st.caption(f"年報狀態：{_status_badges.get(status, status)}")

        if meta.get("character_count", 0) > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("字元數", f"{meta['character_count']:,}")
            c2.metric("詞數",   f"{meta.get('word_count', 0):,}")
            c3.metric("Risk Factors", "✅" if meta.get("has_risk_factors") else "❌")
            c4.metric("MD&A",         "✅" if meta.get("has_management_discussion") else "❌")
            if not annual_ev_df.empty:
                st.dataframe(annual_ev_df, use_container_width=True, hide_index=True)
                st.download_button("⬇ 下載年報證據 CSV", _dataframe_csv(annual_ev_df),
                                   "annual_report_evidence.csv", "text/csv")
            else:
                st.info("年報文字已擷取，但未找到標準章節標題（Risk Factors / MD&A）。KRI 仍從全文擷取。")
        elif status == "extraction_failed":
            st.error(
                "此 PDF 無法擷取到文字，可能是掃描版或受保護文件。\n\n"
                "請回到頁面頂部，將年報 Risk Factors / MD&A 文字貼入文字框後重新執行分析。"
            )
            st.markdown(
                "**可搜尋文字版 PDF 下載：**\n"
                "- Apple 10-K: https://investor.apple.com/sec-filings/annual-reports\n"
                "- TSMC Annual Report: https://ir.tsmc.com/english/annualreports.htm\n"
                "- TWSE 公開資訊觀測站: https://mops.twse.com.tw"
            )
        else:
            st.info("尚未上傳年報 PDF。\n\n"
                    "上傳後系統將自動擷取 Risk Factors 與 MD&A 段落，用於 KRI 分析。")

    # ── Tab 3: KRI Dashboard ──────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("KRI 情報儀表板 | KRI Dashboard")
        if kri_df.empty:
            st.info("請先執行分析以載入 KRI 資料。")
        else:
            # Metrics
            high, medium, low = _sev_count(kri_df,"high"), _sev_count(kri_df,"medium"), _sev_count(kri_df,"low")
            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("新聞數", len(news_df))
            m2.metric("KRI 總計", len(kri_df))
            m3.metric("🔴 High", high)
            m4.metric("🟡 Medium", medium)
            m5.metric("🟢 Low", low)
            st.divider()

            # Charts row
            cl, cr = st.columns(2)
            with cl: _chart_severity(kri_df)
            with cr: _chart_category_donut(kri_df)
            _chart_timeline(kri_df)
            st.divider()

            # Filters
            all_sev = ["high","medium","low"]
            all_cat = sorted(kri_df["kri_category"].dropna().unique().tolist()) if "kri_category" in kri_df.columns else []
            f1, f2 = st.columns(2)
            with f1:
                sel_sev = st.multiselect("嚴重度篩選", all_sev, default=all_sev,
                    format_func=lambda s: {"high":"🔴 High","medium":"🟡 Medium","low":"🟢 Low"}.get(s,s))
            with f2:
                sel_cat = st.multiselect("類別篩選", all_cat, default=all_cat)

            mask = pd.Series(True, index=kri_df.index)
            if "severity_hint" in kri_df.columns and sel_sev:
                mask &= kri_df["severity_hint"].str.lower().isin(sel_sev)
            if "kri_category" in kri_df.columns and sel_cat:
                mask &= kri_df["kri_category"].isin(sel_cat)
            filtered = kri_df[mask].copy()

            # Clean evidence table
            disp_cols = [c for c in ["published_date","kri_category","severity_hint","source_type",
                                      "evidence_sentence","recommended_follow_up"] if c in filtered.columns]
            label_map = {"published_date":"日期","kri_category":"風險類別","severity_hint":"嚴重度",
                         "source_type":"來源","evidence_sentence":"證據句","recommended_follow_up":"建議追問"}
            st.markdown(f"**KRI 風險證據表（{len(filtered)} 項）**")
            st.dataframe(filtered[disp_cols].rename(columns=label_map), use_container_width=True, hide_index=True)
            st.download_button("⬇ 下載 KRI 證據 CSV", _dataframe_csv(filtered),
                               "kri_evidence.csv", "text/csv")
            st.divider()

            # COUNTIFS Pivot
            with st.container(border=True):
                st.markdown("**📊 KRI 類別 × 嚴重度樞紐表（COUNTIFS 等效）**")
                pivot_df = _kri_pivot(filtered)
                if not pivot_df.empty:
                    st.dataframe(pivot_df, use_container_width=True, hide_index=True)
                    _pivot_chart(pivot_df)

            # Working Capital section
            wc_mask = kri_df["kri_category"].str.lower().isin(_WC_CATEGORIES) if "kri_category" in kri_df.columns else pd.Series(False, index=kri_df.index)
            wc_df = kri_df[wc_mask]
            with st.container(border=True):
                st.markdown("**💰 營運資金 & 財務 KRI 專區**")
                st.caption("庫存風險 · 應收帳款 · 現金流 · 流動性 · 獲利能力")
                if wc_df.empty:
                    st.info("目前無相關 KRI 證據。")
                else:
                    wc_show = [c for c in ["published_date","kri_category","severity_hint","evidence_sentence"] if c in wc_df.columns]
                    st.dataframe(wc_df[wc_show].rename(columns=label_map), use_container_width=True, hide_index=True)
                kpi_list = [
                    ("庫存天數 DIO", "inventory risk"),
                    ("應收帳款天數 DSO", "receivables risk"),
                    ("現金轉換週期 CCC", "cash flow risk"),
                    ("流動比率 Current Ratio", "liquidity risk"),
                    ("毛利率 Gross Margin", "profitability risk"),
                ]
                triggered = set(wc_df["kri_category"].str.lower().tolist()) if not wc_df.empty else set()
                for kpi, cat in kpi_list:
                    st.markdown(f"- {'🔴' if cat in triggered else '⬜'} {kpi}")

            # News vs Annual Report comparison
            if "source_type" in kri_df.columns and kri_df["source_type"].nunique() > 1:
                with st.container(border=True):
                    st.markdown("**📰 新聞 vs 年報 風險語言對比**")
                    src_piv = (kri_df.groupby(["kri_category","source_type"]).size()
                               .unstack(fill_value=0).reset_index()
                               .rename(columns={"kri_category":"KRI 類別"}))
                    st.dataframe(src_piv, use_container_width=True, hide_index=True)
                    st.caption("⚠️ 同時出現在新聞與年報 = 管理層已有共識；僅在新聞出現 = 可能的認知差距。")

    # ── Tab 4: Report ─────────────────────────────────────────────────────────
    with tabs[4]:
        st.subheader("產業情報簡報 | Intelligence Brief")
        if not kri_df.empty:
            h, m, l = _sev_count(kri_df,"high"), _sev_count(kri_df,"medium"), _sev_count(kri_df,"low")
            mm1,mm2,mm3,mm4,mm5 = st.columns(5)
            mm1.metric("新聞數", len(news_df))
            mm2.metric("KRI 總計", len(kri_df))
            mm3.metric("🔴 High", h)
            mm4.metric("🟡 Medium", m)
            mm5.metric("🟢 Low", l)
            st.divider()
        if report_md:
            st.download_button("⬇ 下載報告 (.md)", report_md.encode("utf-8"),
                               "intelligence_brief.md", "text/markdown")
            _render_report_sections(report_md)
        else:
            st.info("步驟：① 執行分析 → ② 選語言 → ③ 產生報告")

    # ── Tab 5: Downloads ──────────────────────────────────────────────────────
    with tabs[5]:
        st.subheader("下載 | Downloads")
        if not kri_df.empty:
            st.download_button("⬇ KRI Evidence CSV", _dataframe_csv(kri_df), "kri_evidence.csv", "text/csv", use_container_width=True)
        if not news_df.empty:
            st.download_button("⬇ 新聞 CSV", _dataframe_csv(news_df), "news_articles.csv", "text/csv", use_container_width=True)
        if not annual_ev_df.empty:
            st.download_button("⬇ 年報證據 CSV", _dataframe_csv(annual_ev_df), "annual_report_evidence.csv", "text/csv", use_container_width=True)
        if not dashboard_df.empty:
            st.download_button("⬇ Dashboard CSV", _dataframe_csv(dashboard_df), "dashboard_ready.csv", "text/csv", use_container_width=True)
        if report_md:
            st.download_button("⬇ 情報簡報 Markdown", report_md.encode("utf-8"), "intelligence_brief.md", "text/markdown", use_container_width=True)

        # Excel export
        st.divider()
        if st.button("📊 產生 Excel 工作簿 | Export Excel", use_container_width=True):
            with st.spinner("產生 Excel..."):
                final_summary = generate_final_demo_summary_zh(
                    company_name=inputs["company_name"],
                    industry=inputs["industry_keyword"],
                )
                excel_path = REPORT_DIR / "industry_intelligence.xlsx"
                generate_excel_report(
                    news_df=news_df,
                    annual_report_evidence_df=annual_ev_df,
                    kri_df=kri_df,
                    dashboard_df=dashboard_df,
                    chinese_summary=final_summary,
                    output_path=excel_path,
                )
            if excel_path.exists():
                st.download_button(
                    "⬇ 下載 Excel 工作簿",
                    excel_path.read_bytes(),
                    "industry_intelligence.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="產業情報代理人 | Industry Intelligence Agent", layout="wide")
    _ensure_dirs()

    st.title("產業情報代理人 | Industry Intelligence Agent")
    st.caption("互動式產業情報分析工具：新聞擷取 · KRI 風險辨識 · 中英雙語報告  "
               "| News · KRI Extraction · Bilingual Brief")

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("分析設定 | Settings")
        company_name     = st.text_input("公司名稱 | Company", value="TSMC")
        ticker           = st.text_input("股票代碼 | Ticker",  value="2330.TW")
        industry_keyword = st.text_input("產業關鍵字 | Industry", value="semiconductor AI server")
        news_query       = st.text_input("新聞查詢 | News Query",
                                          value=f"{company_name} tariff supply chain risk")
        annual_pdf       = st.file_uploader("年報 PDF | Annual Report PDF", type=["pdf"])
        use_demo_data    = st.checkbox("使用 Demo 資料 | Use Demo Data", value=True,
                                        help="勾選：載入預建 TSMC 真實新聞。取消：使用 Google News RSS 即時抓取。")
        st.divider()
        max_news = st.slider("最多新聞數 | Max Articles", 5, 30, 10, 1)

    # ── Manual text fallback (shown when PDF extraction failed) ───────────────
    manual_text = ""
    if st.session_state.get("pdf_extraction_failed"):
        st.warning(
            "此 PDF 可能是掃描版或受保護文件，系統無法直接擷取文字。\n\n"
            "你可以改用**可搜尋文字版 PDF**，或將年報 Risk Factors / MD&A 段落貼入下方文字框。"
        )
        manual_text = st.text_area(
            "貼上年報 Risk Factors / MD&A 文字 | Paste annual report text",
            height=220,
            placeholder="例如：Item 1A. Risk Factors\nThe company faces significant supply chain risk...",
        )
        if manual_text.strip():
            st.info(f"已輸入 {len(manual_text.strip()):,} 字元，執行分析後將用於 KRI 擷取。")

    inputs = {
        "company_name":    company_name.strip(),
        "ticker":          ticker.strip(),
        "industry_keyword":industry_keyword.strip(),
        "news_query":      news_query.strip(),
        "annual_pdf":      annual_pdf,
        "use_demo_data":   use_demo_data,
        "max_news":        max_news,
        "manual_text":     manual_text,
    }

    # ── Language + Buttons ────────────────────────────────────────────────────
    lang = st.radio("報告語言 | Language", ["中文", "English"],
                    horizontal=True, label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ 執行分析 | Run Analysis", type="primary", use_container_width=True):
            _run_analysis(inputs)
    with col2:
        if st.button("📄 產生報告 | Generate Report", use_container_width=True):
            if st.session_state.get("kri_df") is not None:
                with st.spinner("產生報告中..."):
                    st.session_state["report_md"] = _generate_report(inputs, "zh" if lang == "中文" else "en")
                st.success("報告已產生。請切換至「情報簡報」tab 查看。")
            else:
                st.warning("請先執行分析。")

    _render_tabs(inputs)


if __name__ == "__main__":
    main()
