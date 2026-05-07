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
    extraction_status: str = "news_only",
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
            _source_section(news_df, annual_report_evidence_df, extraction_status),
            "",
            "## 3. 主要產業趨勢",
            _trend_section(news_df, kri_df),
            "",
            "## 4. 年報 Risk Factors 重點",
            _annual_section(annual_report_evidence_df),
            "",
            "## 5. KRI Evidence",
            _kri_evidence_section(kri_df),
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


def _source_section(news_df: pd.DataFrame, annual_df: pd.DataFrame, extraction_status: str = "news_only") -> str:
    _status_labels = {
        "pdf_text_extracted": "年報 PDF 文字擷取成功",
        "manual_text_used":   "使用者手動貼入年報文字",
        "news_only":          "僅使用新聞（無年報文字）",
    }
    status_label = _status_labels.get(extraction_status, extraction_status)
    lines = [
        f"- 網路新聞：{len(news_df)} 則，來源為 Google News RSS 或預建 demo 資料。",
        f"- 年報證據：{len(annual_df)} 段，優先擷取 Risk Factors 與 Management Discussion。",
        f"- 年報擷取狀態：{status_label}",
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


def _kri_evidence_section(kri_df: pd.DataFrame) -> str:
    """Section 5: rich KRI evidence with categories, counts, and annotated evidence sentences."""
    if kri_df.empty:
        return "- 尚未抽取到 KRI evidence。建議補充新聞或上傳可搜尋文字的年報 PDF。"

    high = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    low = _count_severity(kri_df, "low")
    top_cats = _top_kri_categories(kri_df)
    news_count = int((kri_df.get("source_type", pd.Series(dtype=str)) == "news").sum()) if "source_type" in kri_df.columns else 0
    ar_count = len(kri_df) - news_count

    lines: list[str] = [
        "### 來源概述",
        f"- 共 **{len(kri_df)}** 筆 KRI evidence：新聞 {news_count} 筆、年報 {ar_count} 筆。",
        f"- 嚴重度：🔴 高 {high} 筆 · 🟡 中 {medium} 筆 · 🟢 低 {low} 筆",
        f"- 主要風險類別：{top_cats or '不足，需補充資料來源。'}",
        "",
        "### Evidence 清單（最多顯示 10 筆，依嚴重度排序）",
    ]

    _sev_order = {"high": 0, "medium": 1, "low": 2}
    sorted_df = kri_df.copy()
    if "severity_hint" in sorted_df.columns:
        sorted_df["_sev_rank"] = sorted_df["severity_hint"].str.lower().map(_sev_order).fillna(3)
        sorted_df = sorted_df.sort_values("_sev_rank").drop(columns=["_sev_rank"])

    for _, row in sorted_df.head(10).iterrows():
        sev = str(row.get("severity_hint", "")).lower()
        sev_icon = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}.get(sev, sev.upper())
        cat = row.get("kri_category", "")
        src = row.get("source_type", "")
        keywords = row.get("matched_keywords", row.get("matched_keyword", ""))
        countries = row.get("detected_countries", "")
        pcts = row.get("detected_percentages", "")
        evidence = _shorten(str(row.get("evidence_sentence", "")), 300)

        _business_hint = _category_to_business_hint(cat)

        meta_parts = [f"來源：{src}"]
        if keywords:
            meta_parts.append(f"關鍵字：{keywords}")
        if countries:
            meta_parts.append(f"國家/地區：{countries}")
        if pcts:
            meta_parts.append(f"數字：{pcts}")

        lines += [
            f"**{sev_icon} | {cat}**",
            f"  - {' · '.join(meta_parts)}",
            f"  - 證據：{evidence}",
            f"  - 商業意涵：{_business_hint}",
            "",
        ]

    return "\n".join(lines)


def _category_to_business_hint(category: str) -> str:
    """Map a KRI category to a concise Traditional Chinese business implication."""
    _hints: dict[str, str] = {
        "supply chain risk":            "供應鏈中斷可能造成交期延誤、庫存不足或生產停滯，需評估替代來源與安全庫存水位。",
        "geopolitical risk":            "地緣政治風險可能影響市場准入、出口管制合規與產能配置策略。",
        "customer concentration risk":  "客戶集中度高代表單一客戶訂單異動將直接衝擊營收穩定性，需確認前五大客戶占比。",
        "ESG / sustainability risk":    "能源與碳排放要求可能提高資本支出，並影響供應鏈合規成本與品牌聲譽。",
        "regulatory risk":              "法規變動或出口管制可能增加合規成本、限制市場進入，並提高法律不確定性。",
        "profitability risk":           "成本上升或定價壓力可能壓縮毛利率，需追蹤 COGS 趨勢與轉嫁定價能力。",
        "inventory risk":               "庫存積壓或短缺可能影響現金流，需監控庫存天數（DIO）與預測準確率。",
        "cash flow risk":               "現金流壓力可能影響短期償債能力，需追蹤自由現金流與資本支出規劃。",
        "liquidity risk":               "流動性不足可能限制運營彈性，需連結 working capital 與信用額度狀況。",
        "receivables risk":             "應收帳款回收延遲或壞帳損失將影響現金轉換週期（CCC）與財務健康度。",
        "cyber / digital risk":         "資安事件可能造成營運中斷、資料外洩與合規罰款，需評估 OT/IT 防禦能力。",
        "leverage risk":                "高槓桿可能限制財務彈性，需監控利息保障倍數與債務到期結構。",
    }
    return _hints.get(category.lower().strip(), "需進一步評估此風險對財務與營運的具體影響。")


# ── Impact group mappings ─────────────────────────────────────────────────────

_REVENUE_CATS = {"customer concentration risk", "demand risk", "cash flow risk", "inventory risk"}
_COST_CATS    = {"profitability risk", "regulatory risk", "geopolitical risk", "leverage risk",
                 "ESG / sustainability risk"}
_SUPPLY_CATS  = {"supply chain risk", "inventory risk", "cyber / digital risk", "receivables risk"}
_REGUL_CATS   = {"geopolitical risk", "regulatory risk", "ESG / sustainability risk"}
_DEMAND_CATS  = {"customer concentration risk"}


def _business_impact_section(kri_df: pd.DataFrame) -> str:
    """Section 6: group KRI into 5 business impact dimensions."""
    if kri_df.empty:
        return "- 目前沒有足夠 KRI evidence 判斷商業影響。建議補充新聞或上傳年報 PDF。"

    present_cats: set[str] = set(kri_df["kri_category"].dropna().str.lower().str.strip().tolist()) if "kri_category" in kri_df.columns else set()

    def _impact_lines(cats_map: set[str], fallback: str) -> list[str]:
        matched = [c for c in kri_df["kri_category"].dropna().unique() if c.lower().strip() in cats_map]
        if not matched:
            return [f"  - 本次 KRI evidence 未觸及此影響類別（{fallback}）。"]
        lines = []
        for cat in matched:
            subset = kri_df[kri_df["kri_category"] == cat]
            high_n = int((subset["severity_hint"].str.lower() == "high").sum()) if "severity_hint" in subset.columns else 0
            lines.append(f"  - **{cat}**（{len(subset)} 筆，其中高嚴重度 {high_n} 筆）：{_category_to_business_hint(cat)}")
        return lines

    sections = [
        ("### 1. 營收影響", _impact_lines(_REVENUE_CATS, "客戶集中度、需求、現金流")),
        ("### 2. 成本影響", _impact_lines(_COST_CATS,    "關稅、法規、獲利、槓桿")),
        ("### 3. 供應鏈 / 營運影響", _impact_lines(_SUPPLY_CATS, "供應鏈、庫存、資安")),
        ("### 4. 法規 / 地緣政治影響", _impact_lines(_REGUL_CATS, "地緣政治、法規、ESG")),
        ("### 5. 客戶 / 需求影響", _impact_lines(_DEMAND_CATS, "客戶集中度")),
    ]

    lines: list[str] = [
        "> 以下根據 KRI evidence 初步分析潛在商業衝擊。所有分析為假設性推論，需透過財務資料與管理層訪談驗證。",
        "",
    ]
    for header, body in sections:
        lines.append(header)
        lines.extend(body)
        lines.append("")

    lines.append("> 若本次分析未涵蓋某類別，表示 KRI evidence 不足，非代表風險不存在。")
    return "\n".join(lines)


_CAT_PLAYBOOK: dict[str, dict[str, str]] = {
    "supply chain risk": {
        "urgency":  "本週",
        "action":   "確認主要零組件替代料源清單；為 single-source 供應商建立緊急切換計畫",
        "kpi":      "供應商交期達成率 %、安全庫存天數、single-source 零組件數量",
        "question": "目前有幾個零組件無替代來源？最高風險零組件的庫存水位是多少天？",
        "outcome":  "識別 single-source 零組件並啟動替代料源評估",
    },
    "geopolitical risk": {
        "urgency":  "本週",
        "action":   "列出關稅敏感產品線，計算各稅率情境下 COGS 增量與毛利率敏感度",
        "kpi":      "關稅影響 COGS 增量（USD）、毛利率敏感度（%per 10% tariff change）",
        "question": "哪些產品線含有受出口管制影響的零組件？是否已做過關稅情境 stress test？",
        "outcome":  "完成關稅情境模型，識別毛利率最脆弱的產品線",
    },
    "customer concentration risk": {
        "urgency":  "本週",
        "action":   "計算前五大客戶各自的營收佔比；確認訂單取消 / 延遲條款與最低採購承諾",
        "kpi":      "前五大客戶營收佔比 %、最大單一客戶佔比 %、訂單能見度（週數）",
        "question": "若最大客戶訂單縮減 20%，對本年度 revenue 與 gross profit 影響是多少？",
        "outcome":  "建立客戶集中度熱力圖，設定觸發客戶多元化計畫的閾值",
    },
    "ESG / sustainability risk": {
        "urgency":  "本月",
        "action":   "確認能源來源結構與再生能源佔比；盤點碳排放資料的可靠性與揭露缺口",
        "kpi":      "能源強度（kWh/product unit）、再生能源佔比 %、Scope 1+2 碳排量",
        "question": "ESG 資料目前由哪個部門負責？揭露標準是 GRI、TCFD 還是其他？",
        "outcome":  "建立 ESG 資料治理架構，確認可用於外部揭露的指標",
    },
    "regulatory risk": {
        "urgency":  "本月",
        "action":   "列出受出口管制影響的材料清單（鎵、鍺、石墨等）；確認合規義務與申請流程",
        "kpi":      "受管制材料庫存水位、出口許可申請週期（天）、合規成本佔 COGS %",
        "question": "目前使用哪些受出口管制的材料？申請許可的平均等待時間是多少？",
        "outcome":  "建立材料合規清單，降低因許可延遲導致的生產中斷風險",
    },
    "profitability risk": {
        "urgency":  "本月",
        "action":   "分析過去四季毛利率趨勢；拆解 COGS 成本驅動因子（材料、人力、製造費用）",
        "kpi":      "毛利率 %（季度趨勢）、COGS per unit、定價調整幅度 vs 成本增幅",
        "question": "毛利率下降的主因是材料成本、匯率還是訂單量？有沒有在做定價策略調整？",
        "outcome":  "識別主要成本壓力來源，評估轉嫁至客戶定價的可行性",
    },
    "inventory risk": {
        "urgency":  "本月",
        "action":   "計算庫存天數（DIO）並與行業標準對比；識別高齡庫存與跌價風險品項",
        "kpi":      "庫存天數 DIO（目標 vs 實際）、高齡庫存 / 總庫存 %、需求預測準確率 %",
        "question": "目前庫存超過 90 天的品項佔比是多少？預測準確率是否有在追蹤？",
        "outcome":  "建立庫存健康儀表板，設定跌價準備金觸發規則",
    },
    "cash flow risk": {
        "urgency":  "本月",
        "action":   "追蹤自由現金流（FCF）與資本支出計畫；確認未來 12 個月的流動性缺口",
        "kpi":      "自由現金流（FCF）、現金轉換週期（CCC）、資本支出 / 營收比 %",
        "question": "未來 12 個月最大的資本支出是哪個項目？最低現金緩衝目標是多少？",
        "outcome":  "建立 12 個月現金流預測模型，識別需要融資的月份",
    },
    "liquidity risk": {
        "urgency":  "本月",
        "action":   "確認流動比率與速動比率；盤點可動用的信用額度與備用融資來源",
        "kpi":      "流動比率（Current Ratio）、速動比率（Quick Ratio）、未動用信用額度（USD）",
        "question": "目前有哪些備用信用額度？最近一次流動性壓力測試是什麼時候做的？",
        "outcome":  "確認流動性緩衝是否充足，制定壓力情境下的融資觸發計畫",
    },
    "receivables risk": {
        "urgency":  "本月",
        "action":   "分析應收帳款帳齡分布；確認主要客戶的付款條件與逾期比率",
        "kpi":      "應收帳款天數 DSO、逾期帳款 / 總應收 %、壞帳準備金覆蓋率",
        "question": "前三大客戶的平均付款天期是多少？目前有沒有逾期 60 天以上的帳款？",
        "outcome":  "建立帳齡健康報表，設定催收啟動與壞帳提列規則",
    },
    "cyber / digital risk": {
        "urgency":  "本季",
        "action":   "評估 OT/IT 整合環境的資安暴露面；確認事件應變計畫（IRP）的存在與有效性",
        "kpi":      "資安事件數量 / 季、事件平均應變時間（MTTR）、ICS/OT 網路隔離比率 %",
        "question": "智慧工廠環境有沒有做 OT/IT 網路分隔？最近一次資安演練是何時？",
        "outcome":  "識別高風險 OT 接入點，啟動資安評估與緊急應變計畫更新",
    },
    "leverage risk": {
        "urgency":  "本季",
        "action":   "分析負債結構與到期日程；計算利息保障倍數與債務 / EBITDA 比率",
        "kpi":      "利息保障倍數（Interest Coverage Ratio）、債務 / EBITDA、到期債務佔比 %",
        "question": "未來 18 個月有多少債務到期？如果利率上升 2%，利息費用增加多少？",
        "outcome":  "確認財務槓桿是否在債務契約（covenant）的安全範圍內",
    },
}


def _next_steps_section(kri_df: pd.DataFrame) -> str:
    """Section 7: complete consulting recommendations with priority matrix,
    per-KRI playbook, measurable KPIs, management questions, and
    a validation framework so recommendations can be confirmed effective.
    """
    if kri_df.empty:
        return (
            "> 目前沒有 KRI evidence，無法產生具體建議。\n"
            "> 建議補充新聞或上傳可搜尋文字的年報 PDF 後重新分析。"
        )

    high   = _count_severity(kri_df, "high")
    medium = _count_severity(kri_df, "medium")
    present_cats: set[str] = set(
        kri_df["kri_category"].dropna().str.lower().str.strip().tolist()
    ) if "kri_category" in kri_df.columns else set()

    # Build sorted priority list from actual KRI found
    sev_order = {"high": 0, "medium": 1, "low": 2}
    sorted_kri = (
        kri_df[["kri_category", "severity_hint"]]
        .dropna(subset=["kri_category"])
        .copy()
    )
    if "severity_hint" in sorted_kri.columns:
        sorted_kri["_rank"] = sorted_kri["severity_hint"].str.lower().map(sev_order).fillna(3)
        sorted_kri = sorted_kri.sort_values("_rank")
    unique_cats_ordered = list(dict.fromkeys(sorted_kri["kri_category"].tolist()))

    # ── Priority matrix ───────────────────────────────────────────────────────
    sev_label = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}
    matrix_rows: list[str] = [
        "| 優先 | KRI 類別 | 嚴重度 | 建議行動 | 衡量指標 | 驗證問題 |",
        "|---|---|---|---|---|---|",
    ]
    for rank, cat in enumerate(unique_cats_ordered[:8], start=1):
        sev_val = ""
        if "severity_hint" in kri_df.columns:
            row_sev = kri_df[kri_df["kri_category"] == cat]["severity_hint"].iloc[0] if not kri_df[kri_df["kri_category"] == cat].empty else ""
            sev_val = sev_label.get(str(row_sev).lower(), row_sev)
        pb = _CAT_PLAYBOOK.get(cat.lower().strip(), {})
        action   = pb.get("action",   "需進一步評估具體行動")
        kpi      = pb.get("kpi",      "需定義衡量指標")
        question = pb.get("question", "需與管理層確認")
        matrix_rows.append(f"| {rank} | {cat} | {sev_val} | {action[:60]}… | {kpi[:50]}… | {question[:60]}… |")

    # ── Per-group lines ───────────────────────────────────────────────────────
    def _playbook_lines(cats: list[str], include_outcome: bool = False) -> list[str]:
        lines: list[str] = []
        for cat in cats:
            pb = _CAT_PLAYBOOK.get(cat.lower().strip())
            if not pb:
                lines.append(f"- **{cat}**：需進一步評估具體行動與衡量指標。")
                continue
            lines.append(f"- **{cat}**（緊急度：{pb['urgency']}）")
            lines.append(f"  - 行動：{pb['action']}")
            lines.append(f"  - 衡量 KPI：{pb['kpi']}")
            lines.append(f"  - 管理層驗證問題：{pb['question']}")
            if include_outcome:
                lines.append(f"  - 預期產出：{pb['outcome']}")
        return lines or ["- 本次 KRI evidence 未觸及此時程，無需優先處理。"]

    immediate_cats = [c for c in unique_cats_ordered if _CAT_PLAYBOOK.get(c.lower().strip(), {}).get("urgency") == "本週"]
    monthly_cats   = [c for c in unique_cats_ordered if _CAT_PLAYBOOK.get(c.lower().strip(), {}).get("urgency") == "本月"]
    quarterly_cats = [c for c in unique_cats_ordered if _CAT_PLAYBOOK.get(c.lower().strip(), {}).get("urgency") == "本季"]
    all_remaining  = [c for c in unique_cats_ordered if c.lower().strip() not in _CAT_PLAYBOOK]

    # Management questions from playbook
    mgmt_questions: list[str] = []
    for cat in unique_cats_ordered[:6]:
        pb = _CAT_PLAYBOOK.get(cat.lower().strip(), {})
        if pb.get("question"):
            mgmt_questions.append(f"- **{cat}**：{pb['question']}")
    if not mgmt_questions:
        mgmt_questions = ["- 與管理層確認哪些風險已有對策、哪些仍在觀察中。"]

    lines: list[str] = [
        "> 本節為基於 KRI evidence 的初步諮詢建議。每一條建議都對應一個可量化的 KPI 和一個可向管理層驗證的問題。",
        "> **這是 evidence-based prioritization，不是財務模型。建議需以客戶內部資料與管理層訪談驗證後才能成為最終建議。**",
        "",
        "### 優先處理矩陣",
        *matrix_rows,
        "",
        "---",
        "",
        "### 1. 立即處理（本週）",
        *_playbook_lines(immediate_cats, include_outcome=True),
        "",
        "### 2. 短期行動（本月）",
        *_playbook_lines(monthly_cats, include_outcome=True),
        "",
        "### 3. 中期規劃（本季）",
        *_playbook_lines(quarterly_cats, include_outcome=False),
        "",
        "### 4. 管理層訪談問題",
        "> 以下問題來自 KRI playbook，面試或客戶訪談時可直接使用：",
        *mgmt_questions,
        "- **所有類別**：哪些 KRI 已在月度 review 中追蹤？哪些是今天第一次聽到？",
        "- **所有類別**：哪些 KPI 有明確的目標值與觸發行動的閾值？",
        "",
        "### 5. 人工覆核清單",
        f"- 優先覆核 **{high}** 筆高嚴重度 KRI：回到原始新聞 URL 或年報段落，確認語境正確、未斷章取義。",
        f"- 次優先覆核 **{medium}** 筆中嚴重度 KRI：確認是否為管理層已知風險或新外部訊號。",
        "- 對比新聞 KRI 與年報 KRI：同時出現 = 管理層已有共識；僅在新聞出現 = 潛在認知差距。",
        "- 若任何 KRI 來源為 sample/fallback 資料，需以真實年報與新聞替換後重新執行分析。",
        "",
        "---",
        "",
        "### 如何確認這些建議對企業有效果",
        "> 建議有效的標準：每個行動都能在 30–60 天內產生可量化的基準線，並在 90 天後看到變化。",
        "",
        "| 驗證機制 | 說明 |",
        "|---|---|",
        "| KPI 基準線 | 執行建議前先記錄現況數字（DIO、DSO、毛利率等），作為 before 基準 |",
        "| 管理層確認 | 每條建議需請管理層確認：是已知風險還是新訊號？是否已有對策？ |",
        "| 30 天 check-in | 30 天後確認優先矩陣中前三項行動是否已啟動 |",
        "| 60 天 KPI review | 60 天後比對 KPI 基準線，確認是否朝目標方向移動 |",
        "| KRI 重新掃描 | 60 天後重新執行 KRI extraction，觀察高嚴重度項目是否減少或升高 |",
        "| 認知差距追蹤 | 確認原本「僅出現於新聞」的 KRI，60 天後是否已在年報或管理層報告中揭露 |",
    ]

    return "\n".join(lines)


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
