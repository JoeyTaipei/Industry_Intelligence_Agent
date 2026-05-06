# Industry Intelligence Agent 面試回答重點

## 我做了什麼

我建立了一個 Python-based MVP，可以讀取公司基本資料、新聞、年報文字與產業趨勢，抽取 KRI 風險證據，並輸出 Markdown report、JSON、CSV、dashboard-ready table 與 Excel workbook。

## 解決什麼問題

顧問團隊常需要在短時間內理解產業、公司與風險，但資料分散在新聞、年報、政府或公開資料、研究 notes 裡。本專案把這些資料整理成可分析、可視覺化、可簡報的格式。

## KRI 是什麼

KRI 是 Key Risk Indicator，中文可以理解為「關鍵風險指標」。在這個 MVP 中，KRI 不是最終風險分數，而是從文字中抽出的 evidence，例如 supplier shortage、customer concentration、liquidity pressure、geopolitical uncertainty 或 cybersecurity risk。這些 evidence 可以協助分析師決定哪些風險需要進一步追蹤。

## Excel reporting 展示什麼

Excel workbook 展示 Python 輸出的資料可以進入實際商業分析流程。內容包含：

- Company_Profile、News_Articles、KRI_Evidence、Summary_By_Company、Dashboard_View sheets
- filters 與 freeze panes，方便閱讀
- conditional formatting，快速辨識 high/medium/low risk
- COUNTIFS 統計不同公司與嚴重程度的 KRI 數量
- SUMIFS 彙總 risk score
- XLOOKUP-style formula 將公司對應回產業

## 為什麼是 MVP 不是 production

這個專案刻意保持簡單，因為面試 demo 的重點是展示資料分析、產業研究與顧問式溝通能力。MVP 使用 sample/public-style data、keyword-based extraction 與 optional LLM summary design。若要 production 化，還需要資料品質控管、權限管理、完整測試、來源驗證、monitoring、資安設計與人工審核流程。

## 如果有真實客戶資料，下一步怎麼做

如果有真實客戶資料，我會先確認資料權限與保密要求，再建立 source inventory、data schema、quality checks 與 review workflow。接著會把 KRI dictionary 調整成符合客戶產業的版本，加入真實財務與營運指標，並設計 dashboard prototype 與 management interview questions。

## 15 個可能面試問題與回答重點

### 1. 這個專案一句話是什麼？
用 Python 把公司與產業資料轉成 KRI evidence、Excel 報表與顧問式商業洞察的 interview MVP。

### 2. 為什麼選這個題目？
因為 Deloitte Digital Technology 需要把資料分析、產業理解與數位轉型連在一起，這個題目能同時展示技術與 business thinking。

### 3. 你解決的 business problem 是什麼？
協助顧問快速整理分散資料，找出產業趨勢、公司風險與後續訪談問題。

### 4. 你用了哪些 Python 技術？
pandas、requests/feedparser-ready design、PDF text extraction、CSV/JSON export、openpyxl Excel generation、logging、argparse pipeline。

### 5. 你怎麼做 KRI extraction？
MVP 使用 keyword dictionary 與 sentence-level matching，抽出風險類別、關鍵字、evidence sentence、severity hint 與 risk score hint。

### 6. 這個 KRI 分數可以直接決策嗎？
不行。它是 evidence extraction for human review，不是 final credit decision 或 production risk model。

### 7. 你如何避免 AI overclaim？
LLM 是 optional，設計要求只根據提供 evidence 摘要，不足資料要說明，並區分 facts、interpretation 與 follow-up。

### 8. Excel 報表展示什麼能力？
展示我能把 Python output 轉成 business users 熟悉的 workbook，並使用 COUNTIFS、SUMIFS、XLOOKUP-style formula 與 conditional formatting。

### 9. 這個專案如何對應 Deloitte JD？
它對應整理資料分析與產業趨勢內容，也對應撰寫數據分析程式，並能支援 digital transformation discussion。

### 10. 為什麼不用複雜 agent framework？
MVP 階段我選擇簡單、可解釋、可執行的 pipeline，避免過度工程化，先證明 end-to-end workflow。

### 11. 如果要 production 化會加什麼？
會加入 source validation、data governance、role-based access、完整測試、monitoring、human approval workflow 與更嚴謹的 LLM/RAG evaluation。

### 12. 這個專案最能展示你的哪個能力？
把技術資料處理轉成 business insight，並用顧問能理解的方式輸出。

### 13. 你怎麼選 demo scenario？
選 Taiwan semiconductor / AI server，因為它有清楚的產業趨勢、供應鏈風險、地緣政治與 digital transformation 議題。

### 14. 如果新聞 RSS 失敗怎麼辦？
Pipeline 會 fallback 到 sample news，確保 demo 不會因外部網路或 RSS 問題中斷。

### 15. 你希望面試官看到什麼？
我不只會寫 script，也能理解 business context、產出乾淨資料、設計 Excel/reporting output，並負責任地思考 AI 應用。
