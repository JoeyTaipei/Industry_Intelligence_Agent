# Industry Intelligence Agent

**Industry Intelligence Agent turns news, annual reports, company registry data, and industry trend notes into KRI evidence, Excel reports, and consulting-style insights.**

**中文：一個用 Python 建立的產業情報分析 MVP，可將新聞、年報、公司基本資料與產業趨勢整理成 KRI 風險證據、Excel 報表與顧問式商業洞察。**

Python MVP for a Deloitte Digital Technology Intern interview.

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

The main project lives in:

```text
industry_intelligence_agent/
```

Start here:

- [Project README](industry_intelligence_agent/README.md)
- [Pipeline script](industry_intelligence_agent/scripts/run_pipeline.py)
- [Streamlit app](industry_intelligence_agent/app.py)
- [Chinese project pitch](docs/project_pitch_zh.md)
- [Deloitte fit mapping](docs/deloitte_fit_zh.md)
- [Interview talking points](docs/interview_talking_points_zh.md)

Quick run from `industry_intelligence_agent/`:

```powershell
python scripts/run_pipeline.py --company "TSMC" --industry "semiconductor" --use-sample-data true --export-excel true --language zh-TW
```

This MVP demonstrates Python data analysis, KRI/business risk evidence extraction, dashboard-ready CSV exports, Excel reporting, and consulting-style Traditional Chinese communication.
