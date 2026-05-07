# 產業情報代理人 | Industry Intelligence Agent

**中文：** 以 Python 建立的產業情報分析工具，可將新聞、年報、公司基本資料整理成 KRI 風險證據、互動儀表板與中英雙語顧問報告。

**EN:** A Python-based industry intelligence tool that turns news, annual reports, and company data into KRI evidence, interactive dashboards, and bilingual consulting briefs.

---

## Quick Start

```bash
cd industry_intelligence_agent
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## What It Does

| Step | Action |
|---|---|
| 1 | Enter company name / ticker / industry in sidebar |
| 2 | Toggle **Use demo data** (pre-loaded real TSMC/Taiwan semiconductor news) or uncheck for live RSS |
| 3 | Optionally upload an annual report PDF |
| 4 | Click **▶ 執行分析 \| Run Analysis** |
| 5 | Select language → click **📄 產生報告 \| Generate Report** |

---

## Dashboard Tabs

| Tab | Contents |
|---|---|
| 公司基本資料 | Company profile from registry |
| 新聞訊號擷取 | Filtered news articles with relevance scores |
| KRI 風險證據 | **Full KPI/KRI dashboard**: filters, clean evidence table, COUNTIFS pivot table, working capital section, news vs annual report comparison |
| 產業趨勢 | Trend notes (main trends, growth drivers, risks, DT opportunities) + timeline chart |
| 產業情報簡報 | Metrics + charts + bilingual sectioned report + download |

---

## Charts in Report Tab

- **KRI Severity Bar Chart** — High / Medium / Low counts (red / orange / green)
- **KRI Category Donut Chart** — proportion across 12 risk categories
- **KRI Risk Signal Timeline** — scatter plot of each KRI event by date and category

---

## KRI System

12 risk categories extracted by keyword matching with severity scoring:

| Severity | Score | Examples |
|---|---|---|
| 🔴 High | 3 | supply chain, geopolitical, customer concentration, ESG/energy |
| 🟡 Medium | 2 | regulatory, profitability, inventory |
| 🟢 Low | 1 | cyber/digital |

**COUNTIFS Pivot Table** in Tab 2 shows category × severity counts — the single most useful output for analyst prioritisation.

---

## Key Demo Data (Real News, 2026)

| Fact | Number | Source |
|---|---|---|
| TSMC revenue YoY (Mar 2026) | +45.2% | HeyGoTrade |
| Taiwan energy import dependency | 97% | Yahoo Finance |
| Taiwan LNG reserve without imports | 11 days | Yahoo Finance |
| US tariff on Chinese chips | 50% | Tom's Hardware |
| Taiwan reciprocal tariff (US deal) | ≤15% | CNBC |
| TSMC Arizona cost premium vs Taiwan | +30% | 247 Wall St |

---

## File Structure

```
industry_intelligence_agent/
├── app.py                        ← Streamlit app (entry point)
├── src/
│   ├── kri_extractor.py          ← KRI keyword extraction + severity scoring
│   ├── report_generator.py       ← ZH/EN Markdown report generation
│   ├── news_collector.py         ← RSS feed fetching + keyword filter
│   ├── annual_report_reader.py   ← PDF text extraction
│   ├── industry_trend_reader.py  ← Trend note extraction
│   ├── company_registry.py       ← Company profile lookup
│   └── summarizer.py             ← LLM/rule-based brief generation
├── data/
│   ├── demo/                     ← Pre-built demo data (real 2026 news)
│   ├── raw/                      ← company_registry.csv
│   └── report/                   ← interview_prep_guide.pdf
├── configs/
│   └── rss_sources.yaml          ← RSS feed URLs (edit without code change)
├── scripts/
│   ├── generate_interview_pdf.py ← Regenerate interview prep PDF
│   └── run_pipeline.py           ← CLI pipeline runner
└── requirements.txt
```

---

## Interview Prep

PDF with full preparation guide (architecture, KRI methodology, key numbers, Q&A):

```
data/report/interview_prep_guide.pdf
```

Regenerate anytime:

```bash
python scripts/generate_interview_pdf.py
```

---

## Tech Stack

Python · pandas · Streamlit · Altair · pdfplumber · feedparser · reportlab · PyYAML
