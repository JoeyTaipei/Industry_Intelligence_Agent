# Industry Intelligence Agent

**Industry Intelligence Agent turns news, annual reports, company registry data, and industry trend notes into KRI evidence, Excel reports, and consulting-style insights.**

**中文：一個用 Python 建立的產業情報分析 MVP，可將新聞、年報、公司基本資料與產業趨勢整理成 KRI 風險證據、Excel 報表與顧問式商業洞察。**

**A Python MVP that turns company, news, annual report, and industry trend information into a consulting-style Industry Intelligence Brief, KRI Evidence Table, dashboard-ready CSVs, Excel workbook, and Traditional Chinese interview summary.**

Built for a **Deloitte Digital Technology Intern interview**, this project demonstrates practical data analytics, industry research automation, business risk thinking, Excel reporting, and responsible AI/LLM-assisted workflow design.

## Deloitte Taiwan Interview Snapshot

### 專案是什麼
這是一個以 Python 建立的產業情報分析 MVP，示範如何把公司資料、新聞、年報與產業趨勢整理成可分析、可報告、可展示的商業洞察。

### 解決什麼問題
顧問團隊在短時間內需要理解產業趨勢、公司風險與可能的數位轉型機會。本專案協助把分散資料轉成結構化 KRI evidence、dashboard-ready CSV 與 Excel workbook。

### 對應 Deloitte JD 哪些能力
- 整理資料分析與產業趨勢的文件與內容
- 撰寫數據分析程式
- 支援數位轉型與 AI 應用情境
- 將技術分析轉成 business insight

### 用到哪些技術
Python、pandas、RSS/sample news collection、PDF text extraction、keyword-based KRI extraction、Markdown/JSON/CSV export、Excel reporting with formulas、Streamlit demo、LLM-ready guardrail design。

### 產出哪些成果
Industry Intelligence Brief、KRI Evidence Table、dashboard-ready CSV、Excel analysis workbook、Traditional Chinese final demo summary。此 MVP 使用 sample/public-style data，最終商業判斷仍需人工審閱。

## 1. Project Overview

Industry Intelligence Agent is a working MVP for first-pass company and industry research.

Given a company and industry keyword, the pipeline can collect or load business evidence, extract KRI-related risk signals, and generate outputs that are ready for analysis, dashboards, Excel review, and interview presentation.

Demo scenario:

- **Company:** TSMC
- **Industry:** Taiwan semiconductor / AI server
- **Business question:** What are the key industry trends, business risks, and digital transformation opportunities?

## 2. Business Problem

Consulting teams often need to understand a company or industry quickly, but the information is scattered across:

- company registry data
- business news
- annual reports
- industry trend notes
- risk disclosures
- financial and operating indicators

Manually organizing these sources takes time and can make it difficult to connect evidence to business implications.

This MVP helps structure the research process:

- collect relevant evidence
- extract risk signals
- prepare dashboard-ready data
- generate a concise consulting-style report
- create client interview follow-up questions

## 3. Why This Matters for Deloitte Digital Technology

Deloitte Digital Technology work often connects data, business operations, risk, and digital transformation. This project shows that I can move from raw information to business insight.

This MVP demonstrates that I can:

- collect and organize industry information
- write Python data analysis scripts
- extract KRI and business risk evidence
- prepare dashboard-ready datasets
- generate Excel reports with practical formulas
- communicate findings in business-friendly Traditional Chinese
- apply AI/LLM concepts responsibly with human review and guardrails

Business value:

- risk evidence can become dashboard requirements
- industry signals can become client interview questions
- operating risks can become digital transformation opportunities
- structured outputs can support PowerPoint, Excel, or Streamlit demos

## 4. MVP Features

- **Company registry analysis:** loads or generates local company profile data
- **News signal collection:** loads sample news data and supports RSS-based collection
- **Annual report reader:** reads PDF text or generates sample annual-report-style text
- **KRI evidence extraction:** identifies business risk signals using a keyword dictionary
- **Dashboard-ready export:** creates clean CSV files for analysis and visualization
- **Excel workbook generation:** creates a professional workbook with filters, formulas, and conditional formatting
- **Consulting-style report:** generates Markdown and JSON Industry Intelligence Briefs
- **Traditional Chinese final page:** creates a one-page interview summary in 繁體中文
- **Responsible AI design:** keeps LLM usage optional and evidence-grounded

## 5. MVP Workflow

```text
Input
  company name + industry keyword
  local company registry CSV
  sample or RSS news
  annual report PDF or sample annual report text
  optional industry trend notes

Process
  1. Load company registry
  2. Search company profile
  3. Load or collect news
  4. Read annual report text
  5. Extract KRI evidence
  6. Generate Industry Intelligence Brief
  7. Export CSV / JSON / Markdown
  8. Generate Excel workbook
  9. Generate Traditional Chinese final demo summary

Output
  dashboard-ready data
  Excel workbook
  consulting-style report
  final interview summary page
```

## 6. Project Architecture

```text
industry_intelligence_agent/
├── app.py
├── configs/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── exports/
│   └── reports/
├── scripts/
│   └── run_pipeline.py
└── src/
    ├── company_registry.py
    ├── news_collector.py
    ├── annual_report_reader.py
    ├── kri_extractor.py
    ├── summarizer.py
    ├── report_generator.py
    ├── excel_report_generator.py
    └── pipeline.py
```

Main module responsibilities:

- `company_registry.py`: load/search company profile data
- `news_collector.py`: load sample news or collect RSS articles
- `annual_report_reader.py`: extract and chunk annual report text
- `kri_extractor.py`: extract KRI evidence from text
- `report_generator.py`: create Markdown, JSON, and final Chinese summary
- `excel_report_generator.py`: create Excel workbook for analysis
- `pipeline.py`: orchestrate the full MVP workflow

## 7. KRI Framework

KRI means **Key Risk Indicator**. In this project, KRI extraction means finding evidence sentences that may indicate business risk.

The MVP covers 12 risk categories:

- liquidity risk
- leverage risk
- profitability risk
- cash flow risk
- inventory risk
- receivables risk
- supply chain risk
- customer concentration risk
- regulatory risk
- geopolitical risk
- cyber / digital risk
- ESG / sustainability risk

Example KRI evidence output:

```text
kri_category: supply chain risk
matched_keyword: shortage
evidence_sentence: Material supplier shortages may delay production.
severity_hint: high
risk_score_hint: 3
```

Important guardrail:

This is **evidence extraction for human review**, not a final credit decision, investment recommendation, or production risk scoring model.

## 8. Python Data Analysis Skills Demonstrated

The MVP uses Python to:

- read and clean CSV data with `pandas`
- normalize company registry fields
- filter news by keyword
- extract PDF or sample annual report text
- split text into analysis-ready chunks
- extract KRI evidence using keyword rules
- create dashboard-ready summary tables
- export CSV, JSON, Markdown, and Excel files
- structure outputs for Streamlit, Excel, or PowerPoint use

## 9. Excel Reporting

The generated workbook is:

```text
data/reports/industry_intelligence_demo.xlsx
```

Workbook sheets:

- `Company_Profile`
- `News_Articles`
- `KRI_Evidence`
- `Summary_By_Company`
- `Dashboard_View`

Excel skills shown:

- filters and freeze panes
- auto-adjusted column widths
- conditional formatting for severity and risk level
- `COUNTIFS` to count KRI rows by company and severity
- `SUMIFS` to total numeric risk score hints
- `XLOOKUP` to map company names to industry categories

Business value:

The Excel workbook turns raw extracted evidence into a format that consultants and business users can review, filter, validate, and discuss.

## 10. Responsible AI / LLM Guardrails

The MVP is intentionally simple and does not require paid APIs.

LLM-assisted summarization is treated as optional. The project is designed around these guardrails:

- summarize only provided evidence
- do not invent facts
- distinguish facts from interpretation
- show recommended follow-up separately
- use KRI extraction as evidence for review, not final scoring
- keep human validation in the workflow

This positioning is important because consulting deliverables must be explainable, source-aware, and careful with unsupported claims.

## 11. Traditional Chinese Final Demo Page

The pipeline generates:

```text
data/reports/final_demo_summary_zh.md
```

This one-page Traditional Chinese summary is designed for the final page of an interview presentation.

It explains:

- what I built
- what problem it solves
- what technologies I used
- how it connects to Deloitte Digital Technology
- the one-sentence takeaway

## 12. How to Run on Windows PowerShell

From the `industry_intelligence_agent` folder:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the full sample-data MVP:

```powershell
python scripts/run_pipeline.py --company "TSMC" --industry "semiconductor" --use-sample-data true --export-excel true --language zh-TW
```

Optional Streamlit demo:

```powershell
streamlit run app.py
```

## 13. Output Files

The main generated outputs are:

```text
data/exports/company_profile.csv
data/exports/news_articles.csv
data/exports/kri_evidence.csv
data/exports/dashboard_ready.csv
data/reports/industry_intelligence_brief.md
data/reports/industry_intelligence_brief.json
data/reports/final_demo_summary_zh.md
data/reports/industry_intelligence_demo.xlsx
```

What each output is for:

- `company_profile.csv`: company profile for analysis
- `news_articles.csv`: business/news signals
- `kri_evidence.csv`: extracted KRI evidence for human review
- `dashboard_ready.csv`: summary table for dashboard or Excel
- `industry_intelligence_brief.md`: consulting-style written report
- `industry_intelligence_brief.json`: structured report output
- `final_demo_summary_zh.md`: Traditional Chinese final interview page
- `industry_intelligence_demo.xlsx`: Excel workbook with formulas and formatting

## 14. Interview Talking Points

- I built a working MVP, not only a static analysis document.
- The project shows how Python can automate first-pass industry research.
- The KRI Evidence Table demonstrates business risk thinking in a structured way.
- The Excel workbook shows practical workplace analysis skills, including formulas and conditional aggregation.
- The final Traditional Chinese summary shows I can translate technical analysis into business communication.
- The responsible AI design avoids overclaiming: evidence first, interpretation second, human review required.
- The same workflow could support a dashboard prototype, client interview preparation, or digital transformation opportunity mapping.

## 15. Future Improvements

This is an interview MVP, not a production platform. Future improvements could include:

- connect to official Taiwan open data and MOPS sources
- add real annual report examples
- add financial ratios and operating indicators
- add charts to the Streamlit app
- add PowerPoint export
- add optional LLM summarization with citations
- add automated tests for every module
- add source quality scoring and stronger evidence validation
