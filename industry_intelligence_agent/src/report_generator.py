"""Report and dashboard export helpers for the Streamlit MVP."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def generate_chinese_report(
    company_profile: dict[str, Any],
    news_df: pd.DataFrame,
    annual_report_evidence_df: pd.DataFrame,
    kri_df: pd.DataFrame,
    dashboard_df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> str:
    """Generate the Traditional Chinese consulting-style report."""
    company = company_profile.get("company_name", "目標公司")
    ticker = company_profile.get("ticker", "")
    industry = company_profile.get("industry", "目標產業")
    high = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    low = _count_severity(kri_df, "low")
    top_categories = _top_kri_categories(kri_df)

    report = "\n".join(
        [
            "# 產業情報與 KRI 風險分析報告",
            "",
            f"**公司：** {company}",
            f"**Ticker：** {ticker}",
            f"**產業關鍵字：** {industry}",
            f"**產生時間：** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## 1. Executive Summary 中文摘要",
            f"- 本報告為 Industry Intelligence Agent MVP 產出，目的在協助顧問快速整理新聞、年報與 KRI 風險證據，不是 production 系統。",
            f"- 本次分析包含 {len(news_df)} 則網路新聞、{len(annual_report_evidence_df)} 段年報重點，以及 {len(kri_df)} 筆 KRI evidence。",
            f"- 嚴重度分布：高 {high} 筆、中 {medium} 筆、低 {low} 筆。",
            f"- 主要風險主題：{top_categories or '目前證據不足，需補充資料來源。'}",
            "- 風險分數不是財務模型，severity 只是人工覆核的優先順序提示，最終決策仍需要 human review。",
            "",
            "## 2. 資料來源",
            _source_section(news_df, annual_report_evidence_df),
            "",
            "## 3. 主要產業趨勢",
            _trend_section(news_df, kri_df),
            "",
            "## 4. 年報 Risk Factors 重點",
            _annual_section(annual_report_evidence_df),
            "",
            "## 5. KRI Evidence Table",
            _kri_table_markdown(kri_df),
            "",
            "## 6. 商業影響",
            _business_impact_section(kri_df),
            "",
            "## 7. 建議客戶下一步",
            _next_steps_section(kri_df),
            "",
            "## 8. 限制與治理",
            "- 本工具是 MVP，不是 production 風險管理平台。",
            "- risk_score_hint 不是財務模型，不代表損失金額、違約機率或投資建議。",
            "- severity_hint 是 prioritization hint，只用來協助人工排序與覆核。",
            "- Google News RSS 與年報 PDF 解析可能受資料品質、網路狀態、PDF 格式影響。",
            "- 最終商業判斷需由顧問、財務/法務/風險團隊進行 human review，並回到原始來源驗證。",
        ]
    )

    if output_path:
        save_report(report, output_path)
    return report


def generate_final_demo_summary_zh(
    company_name: str,
    industry: str,
    output_path: str | Path | None = None,
) -> str:
    """Generate a concise Traditional Chinese demo summary."""
    text = f"""# 最後一頁展示：Industry Intelligence Agent

## 我做了什麼
我用 Python 與 Streamlit 建立一個產業情報 MVP，讓使用者輸入公司與產業、上傳年報 PDF、透過 Google News RSS 擷取近期新聞，並自動抽取 KRI 風險證據。

## 本次 demo
- 公司：{company_name or "目標公司"}
- 產業：{industry or "目標產業"}
- 輸出：CSV、Excel workbook、繁體中文 Markdown 顧問報告

## 顧問價值
這個工具把新聞與年報中的零散文字轉成可覆核的 KRI evidence table，協助顧問在訪談前建立假設、排序風險、設計下一步追問。

## 治理聲明
本工具是 MVP，不是 production 系統；risk score 不是財務模型，severity 只是人工覆核優先順序提示，最終決策需要 human review。
"""
    if output_path:
        save_report(text, output_path)
    return text


def build_dashboard_kpi_kri_table(
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Create a one-row dashboard summary table."""
    news_df = _ensure_dataframe(news_df)
    kri_df = _ensure_dataframe(kri_df)
    industry_trend_json = industry_trend_json or {}
    company = _first_non_empty(kri_df, "company_name") or _first_non_empty(news_df, "company_name") or "Target Company"
    industry = industry_trend_json.get("industry") or _first_non_empty(kri_df, "industry") or _first_non_empty(news_df, "industry")
    high = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    low = _count_severity(kri_df, "low")

    return pd.DataFrame(
        [
            {
                "company_name": company,
                "industry": industry,
                "total_news_count": len(news_df),
                "total_kri_count": len(kri_df),
                "high_severity_kri_count": high,
                "medium_severity_kri_count": medium,
                "low_severity_kri_count": low,
                "overall_risk_level": "High" if high else "Medium" if medium else "Low",
                "recommended_follow_up": "請優先覆核 high/medium KRI evidence，並回到新聞與年報原文確認。",
            }
        ]
    )


def generate_json_report(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> dict[str, Any]:
    """Backward-compatible JSON report helper."""
    company_profile = company_profile or {}
    news_df = _ensure_dataframe(news_df)
    kri_df = _ensure_dataframe(kri_df)
    return {
        "report_name": "Industry Intelligence Agent MVP",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company_profile": company_profile,
        "news_articles": news_df.to_dict(orient="records"),
        "kri_evidence": kri_df.to_dict(orient="records"),
        "annual_report_summary": annual_report_summary,
        "dashboard_ready": build_dashboard_kpi_kri_table(news_df, kri_df, industry_trend_json).to_dict(orient="records"),
        "guardrails": [
            "MVP, not production.",
            "Risk score is not a financial model.",
            "Severity is a prioritization hint.",
            "Final decision requires human review.",
        ],
    }


def generate_markdown_report_zh(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> str:
    """Backward-compatible Traditional Chinese report helper."""
    annual_df = pd.DataFrame(
        [
            {
                "section": "annual_report_summary",
                "evidence_text": _summary_to_text(annual_report_summary),
                "source_type": "annual_report",
            }
        ]
    )
    return generate_chinese_report(
        company_profile or {},
        _ensure_dataframe(news_df),
        annual_df,
        _ensure_dataframe(kri_df),
        build_dashboard_kpi_kri_table(news_df, kri_df, industry_trend_json),
    )


def generate_markdown_report(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
) -> str:
    """Simple English-compatible wrapper for old callers."""
    data = generate_json_report(company_profile, news_df, kri_df, industry_trend_json, annual_report_summary)
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def export_dashboard_tables(
    company_profile: dict[str, Any] | None,
    news_df: pd.DataFrame | None,
    kri_df: pd.DataFrame | None,
    industry_trend_json: dict[str, Any] | None,
    annual_report_summary: str | dict[str, Any] | None,
    output_dir: str | Path,
) -> dict[str, str]:
    """Export the standard CSV tables."""
    _ = annual_report_summary
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "company_profile": output / "company_profile.csv",
        "news_articles": output / "news_articles.csv",
        "kri_evidence": output / "kri_evidence.csv",
        "dashboard_ready": output / "dashboard_ready.csv",
    }
    pd.DataFrame([company_profile or {}]).to_csv(paths["company_profile"], index=False, encoding="utf-8-sig")
    _ensure_dataframe(news_df).to_csv(paths["news_articles"], index=False, encoding="utf-8-sig")
    _ensure_dataframe(kri_df).to_csv(paths["kri_evidence"], index=False, encoding="utf-8-sig")
    build_dashboard_kpi_kri_table(news_df, kri_df, industry_trend_json).to_csv(paths["dashboard_ready"], index=False, encoding="utf-8-sig")
    return {key: str(value) for key, value in paths.items()}


def build_digital_transformation_opportunity_map(
    industry_trend_json: dict[str, Any] | None,
    kri_df: pd.DataFrame | None,
) -> pd.DataFrame:
    """Small compatibility helper used by older app versions."""
    _ = kri_df
    opportunities = (industry_trend_json or {}).get("digital_transformation_opportunities", []) or [
        "KRI 風險監控儀表板",
        "供應鏈與關稅情境追蹤",
        "年報與新聞 evidence repository",
    ]
    return pd.DataFrame(
        {
            "opportunity": opportunities,
            "business_value": ["提升風險可視性與人工覆核效率"] * len(opportunities),
            "guardrail": ["需以客戶資料驗證"] * len(opportunities),
        }
    )


def score_source_relevance(
    df: pd.DataFrame,
    company_profile: dict[str, Any] | None = None,
    industry_trend_json: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Add a lightweight source relevance score for display."""
    if df is None or df.empty:
        return _ensure_dataframe(df)
    result = df.copy()
    keywords = [
        (company_profile or {}).get("company_name", ""),
        (company_profile or {}).get("ticker", ""),
        (company_profile or {}).get("industry", ""),
        (industry_trend_json or {}).get("industry", ""),
    ]
    keywords = [str(keyword).lower() for keyword in keywords if keyword]
    scores = []
    for _, row in result.iterrows():
        text = " ".join(str(row.get(col, "")) for col in result.columns).lower()
        score = 50 + min(30, 10 * sum(1 for keyword in keywords if keyword and keyword in text))
        if str(row.get("severity_hint", "")).lower() == "high":
            score += 15
        scores.append(min(score, 100))
    result["source_relevance_score"] = scores
    return result


def save_report(report_text: str | dict[str, Any], output_path: str | Path) -> None:
    """Save text/Markdown or JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(report_text, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    else:
        text = report_text if isinstance(report_text, str) else json.dumps(report_text, ensure_ascii=False, indent=2, default=str)
        path.write_text(text, encoding="utf-8")


def generate_industry_report(
    company_name: str,
    ticker: str,
    industry: str,
    company_profile: dict,
    documents: list[dict],
) -> dict[str, Any]:
    """Backward-compatible helper for older demo scripts."""
    news_df = pd.DataFrame(documents)
    profile = dict(company_profile or {})
    profile.setdefault("company_name", company_name)
    profile.setdefault("ticker", ticker)
    profile.setdefault("industry", industry)
    return generate_json_report(profile, news_df, pd.DataFrame(), {"industry": industry}, "")


def _source_section(news_df: pd.DataFrame, annual_df: pd.DataFrame) -> str:
    lines = [
        f"- 網路新聞：{len(news_df)} 則，來源為 Google News RSS 或 sample fallback。",
        f"- 年報證據：{len(annual_df)} 段，優先擷取 Risk Factors 與 Management Discussion。",
    ]
    if not news_df.empty:
        lines.append("- 近期新聞標題：")
        for _, row in news_df.head(5).iterrows():
            lines.append(f"  - {row.get('title', '')}")
    return "\n".join(lines)


def _trend_section(news_df: pd.DataFrame, kri_df: pd.DataFrame) -> str:
    categories = _top_kri_categories(kri_df)
    if not categories and news_df.empty:
        return "- 目前資料不足，建議補充新聞與年報。"
    lines = []
    if categories:
        lines.append(f"- 從 KRI evidence 觀察，主要風險趨勢集中在：{categories}。")
    if not news_df.empty:
        lines.append("- 近期新聞可作為市場外部訊號，需與年報揭露交叉驗證。")
    return "\n".join(lines)


def _annual_section(annual_df: pd.DataFrame) -> str:
    if annual_df.empty:
        return "- 尚未上傳或成功解析年報 PDF。"
    lines = []
    for _, row in annual_df.head(8).iterrows():
        lines.append(f"- **{row.get('section', '')}**：{_shorten(row.get('evidence_text', ''), 450)}")
    return "\n".join(lines)


def _kri_table_markdown(kri_df: pd.DataFrame) -> str:
    if kri_df.empty:
        return "- 尚未抽取到 KRI evidence。"
    columns = [
        "source_type",
        "kri_category",
        "severity_hint",
        "risk_score_hint",
        "detected_countries",
        "detected_percentages",
        "evidence_sentence",
    ]
    display = kri_df[[column for column in columns if column in kri_df.columns]].head(20).copy()
    headers = display.columns.tolist()
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in display.iterrows():
        values = [str(row.get(column, "")).replace("\n", " ").replace("|", "/") for column in headers]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def _business_impact_section(kri_df: pd.DataFrame) -> str:
    if kri_df.empty:
        return "- 目前沒有足夠 KRI evidence 判斷商業影響。"
    impacts = {
        "trade/tariff risk": "關稅與貿易政策可能影響成本結構、售價、供應鏈配置與毛利率。",
        "supply chain risk": "供應鏈延遲或短缺可能影響交期、庫存策略與營收認列。",
        "supplier concentration risk": "供應商集中可能降低議價能力並提高營運中斷風險。",
        "cost pressure risk": "成本壓力可能壓縮毛利率，需追蹤價格轉嫁能力。",
        "demand risk": "需求波動可能影響庫存、產能規劃與現金流。",
        "liquidity risk": "流動性壓力需連結 working capital、短期資金與信用額度。",
    }
    seen = list(dict.fromkeys(kri_df["kri_category"].dropna().astype(str).tolist()))
    return "\n".join(f"- {category}：{impacts.get(category, '需進一步評估財務與營運影響。')}" for category in seen[:8])


def _next_steps_section(kri_df: pd.DataFrame) -> str:
    steps = [
        "- 回到新聞 URL 與年報原文，驗證 high/medium KRI evidence 的來源與語境。",
        "- 將 KRI 類別映射到可量化 KPI，例如毛利率、庫存天數、供應商交期、現金流、負債比率。",
        "- 與管理層訪談確認哪些風險已被內部追蹤，哪些只是外部市場訊號。",
        "- 若要 production 化，加入來源可信度、時間序列、人工覆核狀態與權限控管。",
    ]
    if not kri_df.empty:
        follow_ups = kri_df.get("recommended_follow_up", pd.Series(dtype=str)).dropna().astype(str).drop_duplicates().head(3).tolist()
        steps.extend(f"- {item}" for item in follow_ups)
    return "\n".join(steps)


def _top_kri_categories(kri_df: pd.DataFrame) -> str:
    if kri_df is None or kri_df.empty or "kri_category" not in kri_df.columns:
        return ""
    counts = kri_df["kri_category"].value_counts().head(5)
    return "、".join(f"{category} ({count})" for category, count in counts.items())


def _ensure_dataframe(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, list):
        return pd.DataFrame(value)
    return pd.DataFrame()


def _count_severity(kri_df: pd.DataFrame, severity: str) -> int:
    if kri_df is None or kri_df.empty or "severity_hint" not in kri_df.columns:
        return 0
    return int((kri_df["severity_hint"].astype(str).str.lower() == severity).sum())


def _first_non_empty(df: pd.DataFrame, column: str) -> str:
    if df is None or df.empty or column not in df.columns:
        return ""
    values = df[column].dropna().astype(str)
    values = values[values != ""]
    return values.iloc[0] if not values.empty else ""


def _summary_to_text(summary: str | dict[str, Any] | None) -> str:
    if not summary:
        return ""
    if isinstance(summary, str):
        return summary
    return str(summary.get("summary") or summary.get("cleaned_text") or summary.get("text") or summary)


def _shorten(value: Any, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."
