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

## Streamlit Web App Demo

This MVP lets a user:

- upload an annual report PDF
- fetch recent internet news via Google News RSS
- extract KRI evidence from news and annual report text
- generate a Traditional Chinese consulting report
- export CSV, Excel, and Markdown outputs

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Default demo inputs:

- `company_name`: Apple
- `ticker`: AAPL
- `industry_keyword`: consumer electronics semiconductor supply chain
- `news_query`: Apple tariff supply chain China Taiwan semiconductor
- `language`: zh-TW
- `export_excel`: true

Outputs:

```text
data/exports/news_articles.csv
data/exports/annual_report_evidence.csv
data/exports/kri_evidence.csv
data/exports/dashboard_ready.csv
data/reports/chinese_report.md
data/reports/final_demo_summary_zh.md
data/reports/industry_intelligence_demo.xlsx
```

---

## What It Does

| Step | Action |
|---|---|
| 1 | Enter company name / ticker / industry in sidebar |
| 2 | Enter a Google News RSS query |
| 3 | Upload an annual report PDF |
| 4 | Click **Run Analysis** |
| 5 | Review Traditional Chinese report and download CSV / Excel / Markdown outputs |

---

## Dashboard Tabs

| Tab | Contents |
|---|---|
| 公司概況 | User-input company profile and dashboard summary |
| 網路新聞 | Google News RSS articles |
| 年報風險證據 | Extracted annual report sections, prioritizing Risk Factors and MD&A |
| KRI Evidence | KRI evidence table and category × severity pivot |
| 中文分析報告 | Traditional Chinese consulting-style report |
| Downloads | CSV, Excel, and Markdown outputs |

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
│   └── raw/                      ← company_registry.csv
├── configs/
│   └── rss_sources.yaml          ← RSS feed URLs (edit without code change)
├── scripts/
│   └── run_pipeline.py           ← CLI pipeline runner
└── requirements.txt
```

---

## PDF Text Extraction & Fallback

The app extracts text from annual report PDFs using **pdfplumber** (primary) and **PyMuPDF** (fallback).

If the PDF is a scanned image or protected file and no text can be extracted, the app will:
1. Show a clear warning message in Traditional Chinese
2. Display a text area — paste the Risk Factors / MD&A section directly
3. Use the pasted text for KRI extraction and report generation
4. Save the pasted text to `data/uploads/manual_annual_report_text.txt`

The `extraction_status` field tracks how the annual report text was sourced:
- `pdf_text_extracted` — PDF text read successfully
- `manual_text_used` — user pasted text as fallback
- `news_only` — no annual report provided
- `extraction_failed` — PDF provided but text could not be read

> **Future improvement (not implemented):** If the annual report is a scanned PDF, OCR can be added using Tesseract (`pytesseract`) or a cloud OCR service (Google Document AI, Azure Form Recognizer). This would convert scanned pages to searchable text before the KRI extraction pipeline runs.

---

## Tech Stack

Python · pandas · Streamlit · Altair · pdfplumber · feedparser · reportlab · PyYAML
