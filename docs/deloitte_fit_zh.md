# Deloitte Digital Technology JD 對應表

| JD 要求 | 我的專案如何對應 | 可展示的 output file | 面試時怎麼說 |
|---|---|---|---|
| 整理資料分析與產業趨勢的文件與內容 | 專案把公司 registry、新聞、年報文字與產業趨勢 notes 整理成 structured data 與 consulting-style brief。 | `industry_intelligence_agent/data/reports/industry_intelligence_brief.md` | 我把分散資料先標準化，再轉成可以閱讀、分析與簡報使用的格式，讓產業研究更有結構。 |
| 撰寫數據分析程式 | 使用 Python、pandas、CSV/JSON export、SQLite-ready design 與 command-line pipeline，自動產生公司資料、新聞、KRI evidence 與 dashboard table。 | `industry_intelligence_agent/scripts/run_pipeline.py`, `industry_intelligence_agent/data/exports/dashboard_ready.csv` | 這不是單純手動整理資料，而是把分析流程寫成可重複執行的 Python pipeline。 |
| 支援數位轉型與 AI 應用 | 將供應鏈、資安、working capital、ESG 等 business signals 轉成 digital transformation opportunity map，例如 dashboard、early warning、process monitoring。 | `industry_intelligence_agent/data/reports/industry_intelligence_brief.md` | 我會把風險 evidence 連回 business implication，再思考哪些地方可以用 data dashboard 或 AI-assisted workflow 改善。 |
| 資料分析與產業研究能力 | Demo scenario 聚焦 Taiwan semiconductor / AI server，展示如何把產業趨勢、公司資訊與風險證據放在同一份 brief 中。 | `industry_intelligence_agent/data/exports/news_articles.csv`, `industry_intelligence_agent/data/exports/kri_evidence.csv` | 我用資料表支撐商業觀察，避免只停留在文字摘要。 |
| Excel 與 business reporting 能力 | Excel workbook 包含多個分析 sheet、filters、freeze panes、conditional formatting、COUNTIFS、SUMIFS、XLOOKUP-style formula。 | `industry_intelligence_agent/data/reports/industry_intelligence_demo.xlsx` | 我希望展示 Python 可以產出乾淨資料，也能接到顧問日常常用的 Excel 分析場景。 |
| 負責任使用 GenAI / LLM 概念 | LLM 設計為 optional，prompt guardrails 要求只摘要提供 evidence、不發明事實、不足資料要明講，最終決策需 human review。 | `industry_intelligence_agent/src/summarizer.py`, `industry_intelligence_agent/README.md` | 我把 AI 放在輔助整理與摘要的位置，不把 MVP 包裝成自動決策系統。 |

## 重要說明

此專案是 interview MVP，主要使用 sample/public-style data 展示流程與分析思維。KRI evidence 是給顧問或分析師審閱的線索，不代表最終風險判斷或信用決策。
