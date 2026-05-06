# Industry Intelligence Agent 中文介紹稿

## 30 秒中文介紹

Industry Intelligence Agent 是我為 Deloitte Digital Technology Intern 面試準備的 Python MVP。它可以把公司基本資料、新聞、年報文字與產業趨勢整理成 KRI 風險證據、dashboard-ready CSV、Excel workbook 與顧問式報告。這個專案重點不是取代顧問判斷，而是示範如何用資料分析流程加速產業研究、風險整理與商業洞察產出。

## 60 秒中文介紹

這個專案模擬顧問團隊需要快速理解台灣半導體與 AI server 產業的情境。使用者輸入公司名稱與產業關鍵字後，系統會載入公司 registry、新聞資料、年報或 sample annual report text，接著用 keyword-based KRI extraction 把流動性、供應鏈、地緣政治、資安、ESG 等風險訊號整理成 evidence table。最後輸出 Markdown/JSON report、CSV exports 與 Excel workbook，方便接到 dashboard、PowerPoint 或面試展示。

我把 LLM 設計成 optional，且要求只根據提供的 evidence 摘要，不產生未被資料支持的結論。這個 MVP 使用 sample/public-style data，所有風險判讀仍需要 human review。

## HR 版

我做的是一個能把產業資料整理成商業洞察的 Python demo。它展示我可以：

- 用 Python 和 pandas 整理資料
- 將新聞、年報與公司資料轉成結構化表格
- 產出 Excel workbook 與 dashboard-ready data
- 用繁體中文寫出容易理解的顧問式摘要
- 理解 Digital Technology 專案中資料、AI 與 business insight 的連結

## 技術面試官版

技術上，這個專案採用簡單模組化設計，包含 company registry loader、news collector、annual report reader、KRI extractor、report generator、Excel report generator 與 pipeline CLI。MVP 先用 local CSV、RSS/sample news、PDF text extraction 與 keyword-based extraction，避免過度工程化。輸出包含 CSV、JSON、Markdown 與 Excel workbook，Excel 內有 filters、freeze panes、conditional formatting、COUNTIFS、SUMIFS、XLOOKUP-style formula，展示 Python 與 Excel 分析流程可以串接。

## 顧問/商業面試官版

這個專案的商業價值在於把分散的產業資訊轉成可討論的 business signals。它可以幫助顧問團隊快速回答：

- 這家公司所在產業有哪些趨勢？
- 哪些風險訊號值得追蹤？
- 哪些 KRI 可以放進 dashboard？
- 哪些問題應該在 client interview 中進一步確認？
- 哪些營運風險可能轉成 digital transformation opportunity？

它是一個 interview MVP，不是 production risk engine；目的是展示資料整理、分析思維與顧問式溝通能力。
