"""Consulting-style report and dashboard export helpers.

The goal of this module is to make the MVP feel like a business deliverable,
not a technical script. It separates facts from analytical interpretation and
recommended follow-up questions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def generate_markdown_report(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> str:
    """Generate the main Industry Intelligence Brief as Markdown."""
    company_profile = company_profile or {}
    news_df = score_source_relevance(_ensure_dataframe(news_df), company_profile, industry_trend_json)
    kri_df = score_source_relevance(_ensure_dataframe(kri_df), company_profile, industry_trend_json)
    industry_trend_json = industry_trend_json or {}

    company = company_profile.get("company_name") or "Target Company"
    industry = industry_trend_json.get("industry") or company_profile.get("industry") or "Target Industry"
    annual_text = _summary_to_text(annual_report_summary)

    sections = [
        "# Industry Intelligence Brief",
        "",
        f"**Company:** {company}",
        f"**Industry:** {industry}",
        f"**Generated at:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Executive Summary",
        _executive_summary(company, industry, news_df, kri_df, industry_trend_json),
        "",
        "## 2. Company Profile",
        _company_profile_section(company_profile),
        "",
        "## 3. Business Model",
        _business_model_section(company_profile, annual_text),
        "",
        "## 4. Industry Trends",
        _list_with_prefix(industry_trend_json.get("main_trends"), "Fact from sources"),
        "",
        "## 5. Recent News Signals",
        _news_section(news_df),
        "",
        "## 6. KRI Risk Evidence",
        _kri_section(kri_df),
        "",
        "## 7. Potential Data Analysis Use Cases",
        _data_analysis_use_cases(kri_df),
        "",
        "## 8. Digital Transformation Opportunities",
        _digital_opportunity_section(industry_trend_json, kri_df),
        "",
        "## 9. Recommended Next Steps",
        _recommended_next_steps(company, industry, news_df, kri_df),
        "",
        "### Guardrails",
        "- Facts from sources: company registry, news summaries, annual report snippets, KRI evidence sentences.",
        "- Analytical interpretation: risk prioritization, business implications, and digital opportunity mapping.",
        "- Recommended follow-up: client interview questions and validation steps.",
        "- Human review is required before using this as a final risk conclusion.",
    ]
    return "\n".join(sections)


def generate_json_report(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> dict[str, Any]:
    """Generate the same report content as JSON for apps and dashboards."""
    company_profile = company_profile or {}
    news_df = score_source_relevance(_ensure_dataframe(news_df), company_profile, industry_trend_json)
    kri_df = score_source_relevance(_ensure_dataframe(kri_df), company_profile, industry_trend_json)
    industry_trend_json = industry_trend_json or {}
    company = company_profile.get("company_name") or "Target Company"
    industry = industry_trend_json.get("industry") or company_profile.get("industry") or "Target Industry"

    return {
        "report_name": "Industry Intelligence Brief",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_profile": company_profile,
        "industry": industry,
        "executive_summary": _executive_summary_points(company, industry, news_df, kri_df, industry_trend_json),
        "news_articles": news_df.to_dict(orient="records"),
        "kri_evidence": kri_df.to_dict(orient="records"),
        "industry_trends": industry_trend_json,
        "annual_report_summary": _summary_to_text(annual_report_summary),
        "dashboard_ready": build_dashboard_kpi_kri_table(news_df, kri_df, industry_trend_json).to_dict(orient="records"),
        "guardrails": [
            "Only summarize provided evidence.",
            "Distinguish facts from interpretation.",
            "Use KRI output as evidence extraction, not final decisioning.",
            "Human review is required.",
        ],
    }


def generate_markdown_report_zh(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> str:
    """Generate the Industry Intelligence Brief in Traditional Chinese."""
    company_profile = company_profile or {}
    news_df = score_source_relevance(_ensure_dataframe(news_df), company_profile, industry_trend_json)
    kri_df = score_source_relevance(_ensure_dataframe(kri_df), company_profile, industry_trend_json)
    industry_trend_json = industry_trend_json or {}

    company = company_profile.get("company_name") or "目標公司"
    industry = industry_trend_json.get("industry") or company_profile.get("industry") or "目標產業"
    annual_text = _summary_to_text(annual_report_summary)

    sections = [
        "# 產業情報簡報",
        "",
        f"**公司：** {company}",
        f"**產業：** {industry}",
        f"**產生時間：** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. 執行摘要",
        _executive_summary_zh(company, industry, news_df, kri_df, industry_trend_json),
        "",
        "## 2. 公司基本資料",
        _company_profile_section_zh(company_profile),
        "",
        "## 3. 商業模式",
        _business_model_section_zh(company_profile, annual_text),
        "",
        "## 4. 產業趨勢",
        _list_with_prefix_zh(industry_trend_json.get("main_trends"), "來源事實"),
        "",
        "## 5. 近期新聞訊號",
        _news_section_zh(news_df),
        "",
        "## 6. KRI 風險證據",
        _kri_section_zh(kri_df),
        "",
        "## 7. 資料分析應用場景",
        _data_analysis_use_cases_zh(),
        "",
        "## 8. 數位轉型機會",
        _digital_opportunity_section_zh(industry_trend_json, kri_df),
        "",
        "## 9. 建議追問與後續步驟",
        _recommended_next_steps_zh(company, industry, news_df, kri_df),
        "",
        "### 使用聲明",
        "- 來源事實：公司基本資料、新聞摘要、年報片段、KRI 證據句。",
        "- 分析解讀：風險優先排序、商業意涵與數位轉型機會映射。",
        "- 建議追問：客戶訪談問題與資料驗證步驟。",
        "- 本報告為分析輔助工具，作為最終風險結論前須經人工審閱。",
    ]
    return "\n".join(sections)


def _executive_summary_zh(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame, trend_json: dict[str, Any]) -> str:
    return "\n".join(f"- {point}" for point in _executive_summary_points_zh(company, industry, news_df, kri_df, trend_json))


def _executive_summary_points_zh(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame, trend_json: dict[str, Any]) -> list[str]:
    top_trend = (trend_json.get("main_trends") or ["證據不足。"])[0]
    top_risk = _first_non_empty(kri_df, "kri_category") or "未擷取到 KRI 證據。"
    high = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    return [
        f"來源事實：本簡報分析 {company}（產業：{industry}）。",
        f"來源事實：證據包含 {len(news_df)} 則新聞，{len(kri_df)} 項 KRI 風險證據（高嚴重度 {high} 項，中嚴重度 {medium} 項）。",
        f"分析解讀：主要趨勢訊號：{top_trend}",
        f"分析解讀：首要風險主題：{top_risk}",
        "建議追問：請與管理層訪談確認風險實質性，並建立 KPI/KRI 追蹤儀表板。",
    ]


def _company_profile_section_zh(profile: dict[str, Any]) -> str:
    if not profile:
        return "- 公司基本資料不可用。"
    label_map = {
        "company_name": "公司名稱", "ticker": "股票代碼", "industry": "產業",
        "country": "國家", "website": "網站", "description": "公司描述",
        "source": "資料來源",
    }
    return "\n".join(
        f"- 來源事實 — {label_map.get(k, k)}：{v}"
        for k, v in profile.items() if v
    )


def _business_model_section_zh(profile: dict[str, Any], annual_text: str) -> str:
    points = []
    if profile.get("industry"):
        points.append(f"來源事實：公司歸屬於 {profile['industry']} 產業。")
    if annual_text:
        points.append(f"來源事實：年報訊號：{_shorten(annual_text, 450)}")
    points.append("分析解讀：請將商業模式假設連結至營收驅動因素、營運風險與數位轉型機會。")
    return "\n".join(f"- {p}" for p in points)


def _news_section_zh(news_df: pd.DataFrame) -> str:
    if news_df.empty:
        return "- 無可用新聞證據。"
    lines = []
    for _, row in news_df.head(8).iterrows():
        lines.append(f"- 來源事實：{row.get('title', '')}：{_shorten(row.get('summary', ''), 220)}")
    return "\n".join(lines)


def _kri_section_zh(kri_df: pd.DataFrame) -> str:
    if kri_df.empty:
        return "- 未擷取到 KRI 風險證據。"
    severity_map = {"high": "高", "medium": "中", "low": "低"}
    lines = []
    for _, row in kri_df.head(10).iterrows():
        sev = severity_map.get(str(row.get("severity_hint", "")).lower(), row.get("severity_hint", ""))
        lines.append(
            f"- 來源事實：{row.get('kri_category', '')}（嚴重度：{sev}）："
            f"{_shorten(row.get('evidence_sentence', ''), 240)}"
        )
    return "\n".join(lines)


def _data_analysis_use_cases_zh() -> str:
    return "\n".join([
        "- 建立 KPI/KRI 儀表板，依公司、產業、嚴重度與風險類別分層。",
        "- 使用 Excel COUNTIFS/SUMIFS 彙總各嚴重度 KRI 證據數量。",
        "- 對比新聞訊號與年報風險語言，找出管理層認知差距。",
        "- 追蹤營運資金、庫存、應收帳款與供應商延遲等關鍵指標。",
    ])


def _digital_opportunity_section_zh(trend_json: dict[str, Any], kri_df: pd.DataFrame) -> str:
    items = trend_json.get("digital_transformation_opportunities") or [
        "營運資金儀表板",
        "供應商風險監控",
        "需求預測與產能規劃",
    ]
    return _list_with_prefix_zh(items, "分析解讀")


def _recommended_next_steps_zh(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame) -> str:
    return "\n".join([
        "- 建議追問：管理層目前追蹤哪些風險？哪些僅為外部市場訊號？",
        "- 建議追問：每月定期檢視哪些 KPI/KRI 指標？",
        "- 建議追問：哪些資料來源已足夠可靠，可納入儀表板報告？",
        "- 建議追問：哪個數位轉型機會有最清楚的 KPI 衡量連結？",
    ])


def _list_with_prefix_zh(items: Any, prefix: str) -> str:
    if not items:
        return "- 證據不足。"
    if isinstance(items, str):
        items = [items]
    return "\n".join(f"- {prefix}：{item}" for item in items)


def generate_final_demo_summary_zh(
    company_name: str,
    industry: str,
    output_path: str | Path | None = None,
) -> str:
    """Generate the final one-page Traditional Chinese interview summary."""
    text = f"""# 最後一頁展示：Industry Intelligence Agent

## 我做了什麼
用 Python 建立一個可以讀取新聞、年報、公司基本資料與產業趨勢的分析工具。本次 demo 聚焦於 {company_name or "目標公司"} 與 {industry or "目標產業"}。

## 解決什麼問題
幫助顧問快速整理產業趨勢、辨識公司風險、產生 KRI evidence，並輸出 dashboard-ready data。

## 用到什麼技術
Python、pandas、PDF text extraction、RSS news collection、KRI extraction、Excel reporting、LLM-assisted summary、Markdown report、CSV export。

## 對 Deloitte Digital Technology Intern 的連結
這個專案對應 JD 中的：
- 整理資料分析與產業趨勢內容
- 撰寫數據分析程式
- 支援數位轉型與 AI 應用
- 將技術分析轉成 business insight

## 一句話總結
我能把產業資料與公司資訊轉成可分析、可視覺化、可交付的商業洞察。
"""
    if output_path:
        save_report(text, output_path)
    return text


def export_dashboard_tables(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
    output_dir: str | Path,
) -> dict[str, str]:
    """Export dashboard-ready CSV tables."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    company_profile = company_profile or {}
    news_df = score_source_relevance(_ensure_dataframe(news_df), company_profile, industry_trend_json)
    kri_df = score_source_relevance(_ensure_dataframe(kri_df), company_profile, industry_trend_json)
    industry_trend_json = industry_trend_json or {}

    paths = {
        "company_profile": output / "company_profile.csv",
        "news_articles": output / "news_articles.csv",
        "kri_evidence": output / "kri_evidence.csv",
        "dashboard_ready": output / "dashboard_ready.csv",
    }
    pd.DataFrame([company_profile]).to_csv(paths["company_profile"], index=False, encoding="utf-8-sig")
    news_df.to_csv(paths["news_articles"], index=False, encoding="utf-8-sig")
    kri_df.to_csv(paths["kri_evidence"], index=False, encoding="utf-8-sig")
    build_dashboard_kpi_kri_table(news_df, kri_df, industry_trend_json).to_csv(paths["dashboard_ready"], index=False, encoding="utf-8-sig")
    return {key: str(value) for key, value in paths.items()}


def save_report(report_text: str | dict[str, Any], output_path: str | Path) -> None:
    """Save Markdown/text or JSON based on file extension."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(report_text, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    else:
        text = report_text if isinstance(report_text, str) else json.dumps(report_text, ensure_ascii=False, indent=2, default=str)
        path.write_text(text, encoding="utf-8")


def score_source_relevance(
    df: pd.DataFrame,
    company_profile: dict[str, Any] | None = None,
    industry_trend_json: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Add simple source relevance score and reason columns."""
    if df is None or df.empty:
        return _ensure_dataframe(df)

    result = df.copy()
    company_profile = company_profile or {}
    industry_trend_json = industry_trend_json or {}
    keywords = [
        company_profile.get("company_name", ""),
        company_profile.get("ticker", ""),
        company_profile.get("industry", ""),
        industry_trend_json.get("industry", ""),
    ]
    keywords = [str(item).lower() for item in keywords if item]

    scores = []
    reasons = []
    for _, row in result.iterrows():
        text = " ".join(str(row.get(col, "")) for col in result.columns).lower()
        score = 40
        reason = ["base row"]
        hits = [kw for kw in keywords if kw and kw in text]
        if hits:
            score += min(30, len(hits) * 10)
            reason.append("keyword match")
        if row.get("url") or row.get("source_id"):
            score += 10
            reason.append("source traceable")
        if row.get("severity_hint") == "high":
            score += 15
            reason.append("high severity")
        elif row.get("severity_hint") == "medium":
            score += 10
            reason.append("medium severity")
        scores.append(min(score, 100))
        reasons.append("; ".join(reason))

    result["source_relevance_score"] = scores
    result["source_relevance_reason"] = reasons
    return result


def build_dashboard_kpi_kri_table(
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
) -> pd.DataFrame:
    """Create the required dashboard-ready KPI/KRI table."""
    news_df = _ensure_dataframe(news_df)
    kri_df = _ensure_dataframe(kri_df)
    industry_trend_json = industry_trend_json or {}

    company = _first_non_empty(kri_df, "company_name") or _first_non_empty(news_df, "company_name") or "Target Company"
    industry = industry_trend_json.get("industry") or _first_non_empty(kri_df, "industry") or _first_non_empty(news_df, "industry")

    high = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    low = _count_severity(kri_df, "low")
    overall = "High" if high > 0 else "Medium" if medium > 0 else "Low"
    follow_up = "Validate high/medium KRI evidence with management interviews and source documents."

    return pd.DataFrame([
        {
            "company_name": company,
            "industry": industry,
            "total_news_count": len(news_df),
            "total_kri_count": len(kri_df),
            "high_severity_kri_count": high,
            "medium_severity_kri_count": medium,
            "low_severity_kri_count": low,
            "overall_risk_level": overall,
            "recommended_follow_up": follow_up,
        }
    ])


def build_digital_transformation_opportunity_map(
    industry_trend_json: dict[str, Any] | None,
    kri_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Map trend/risk signals to digital transformation opportunities."""
    industry_trend_json = industry_trend_json or {}
    opportunities = industry_trend_json.get("digital_transformation_opportunities", []) or []
    rows = [
        {
            "opportunity": item,
            "business_value": "Improve decision visibility and measurable KPI tracking.",
            "guardrail": "Validate with client data before recommendation.",
        }
        for item in opportunities
    ]
    return pd.DataFrame(rows)


def generate_industry_report(
    company_name: str,
    ticker: str,
    industry: str,
    company_profile: dict,
    documents: list[dict],
) -> dict[str, Any]:
    """Backward-compatible helper for older demo scripts."""
    news_df = pd.DataFrame(
        [
            {
                "source": doc.get("source_type", "document"),
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "published_date": doc.get("published_at", ""),
                "summary": doc.get("text", ""),
                "keyword": industry,
                "company_name": company_name,
                "industry": industry,
            }
            for doc in documents
        ]
    )
    profile = dict(company_profile or {})
    profile.setdefault("company_name", company_name)
    profile.setdefault("ticker", ticker)
    profile.setdefault("industry", industry)
    return generate_json_report(profile, news_df, pd.DataFrame(), {"industry": industry}, "")


def _executive_summary(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame, trend_json: dict[str, Any]) -> str:
    return "\n".join(f"- {point}" for point in _executive_summary_points(company, industry, news_df, kri_df, trend_json))


def _executive_summary_points(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame, trend_json: dict[str, Any]) -> list[str]:
    top_trend = (trend_json.get("main_trends") or ["Evidence is insufficient."])[0]
    top_risk = _first_non_empty(kri_df, "kri_category") or "No KRI evidence extracted."
    return [
        f"Fact from sources: This brief reviews {company} in {industry}.",
        f"Fact from sources: Evidence includes {len(news_df)} news records and {len(kri_df)} KRI evidence rows.",
        f"Analytical interpretation: The key trend signal is: {top_trend}",
        f"Analytical interpretation: The first risk theme for review is: {top_risk}",
        "Recommended follow-up: Confirm materiality with management interviews and dashboard-ready metrics.",
    ]


def _company_profile_section(profile: dict[str, Any]) -> str:
    if not profile:
        return "- Company profile not available."
    return "\n".join(f"- Fact from sources: {key}: {value}" for key, value in profile.items() if value)


def _business_model_section(profile: dict[str, Any], annual_text: str) -> str:
    points = []
    if profile.get("industry"):
        points.append(f"Fact from sources: The company is classified in {profile['industry']}.")
    if annual_text:
        points.append(f"Fact from sources: Annual report signal: {_shorten(annual_text, 450)}")
    points.append("Analytical interpretation: Link business model assumptions to revenue drivers, operating risks, and digital opportunities.")
    return "\n".join(f"- {point}" for point in points)


def _news_section(news_df: pd.DataFrame) -> str:
    if news_df.empty:
        return "- No news evidence available."
    lines = []
    for _, row in news_df.head(8).iterrows():
        lines.append(f"- Fact from sources: {row.get('title', '')}: {_shorten(row.get('summary', ''), 220)}")
    return "\n".join(lines)


def _kri_section(kri_df: pd.DataFrame) -> str:
    if kri_df.empty:
        return "- No KRI evidence extracted."
    lines = []
    for _, row in kri_df.head(10).iterrows():
        lines.append(
            f"- Fact from sources: {row.get('kri_category', '')} / {row.get('severity_hint', '')}: "
            f"{_shorten(row.get('evidence_sentence', ''), 240)}"
        )
    return "\n".join(lines)


def _data_analysis_use_cases(kri_df: pd.DataFrame) -> str:
    return "\n".join([
        "- Build a KPI/KRI dashboard by company, industry, severity, and risk category.",
        "- Use COUNTIFS/SUMIFS in Excel to summarize KRI evidence by severity.",
        "- Compare news signals with annual report risk language.",
        "- Track working capital, inventory, receivables, and supplier delay indicators.",
    ])


def _digital_opportunity_section(trend_json: dict[str, Any], kri_df: pd.DataFrame) -> str:
    items = trend_json.get("digital_transformation_opportunities") or [
        "Working capital dashboard",
        "Supplier risk monitoring",
        "Demand forecasting and capacity planning",
    ]
    return _list_with_prefix(items, "Analytical interpretation")


def _recommended_next_steps(company: str, industry: str, news_df: pd.DataFrame, kri_df: pd.DataFrame) -> str:
    return "\n".join([
        "- Recommended follow-up: Which risks are already tracked by management?",
        "- Recommended follow-up: What KPI/KRI metrics are reviewed monthly?",
        "- Recommended follow-up: Which data sources are reliable enough for dashboard reporting?",
        "- Recommended follow-up: Which digital opportunity has the clearest KPI impact?",
    ])


def _list_with_prefix(items: Any, prefix: str) -> str:
    if not items:
        return "- Evidence is insufficient."
    if isinstance(items, str):
        items = [items]
    return "\n".join(f"- {prefix}: {item}" for item in items)


def _ensure_dataframe(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, list):
        return pd.DataFrame(value)
    return pd.DataFrame()


def _summary_to_text(summary: str | dict[str, Any] | None) -> str:
    if not summary:
        return ""
    if isinstance(summary, str):
        return summary
    return str(summary.get("summary") or summary.get("cleaned_text") or summary.get("text") or summary)


def _first_non_empty(df: pd.DataFrame, column: str) -> str:
    if df.empty or column not in df.columns:
        return ""
    values = df[column].dropna().astype(str)
    values = values[values != ""]
    return values.iloc[0] if not values.empty else ""


def _count_severity(kri_df: pd.DataFrame, severity: str) -> int:
    if kri_df.empty or "severity_hint" not in kri_df.columns:
        return 0
    return int((kri_df["severity_hint"].astype(str).str.lower() == severity).sum())


def _shorten(value: Any, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."
