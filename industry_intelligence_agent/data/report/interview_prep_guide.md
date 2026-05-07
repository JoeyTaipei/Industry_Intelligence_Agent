# Industry Intelligence Agent 面試準備指南

更新日期：2026-05-07

這份文件的目的不是背稿，而是讓你真的理解整個專案。讀完後，你要能用 2 到 3 分鐘講清楚「我做了什麼」，再用 5 到 8 分鐘回答「資料怎麼抽、風險怎麼判、分析怎麼變成商業洞察」。

## 1. 專案一句話

Industry Intelligence Agent 是一個用 Python 建立的產業情報分析 MVP。它把公司基本資料、新聞、年報文字和產業趨勢整理成 KRI 風險證據、dashboard-ready CSV、Excel workbook、Streamlit 儀表板，以及中英雙語顧問式報告。

面試時可以這樣講：

> 我做的是一個產業情報代理人。輸入公司、產業關鍵字和年報 PDF 後，系統會收集新聞、讀取年報、抽取 KRI 風險證據、判斷嚴重度，最後產生儀表板、Excel 和顧問式 brief。它的價值是把顧問前期 research 從零散資料整理成可驗證、可追問、可交付的分析輸出。

## 2. 專案解決什麼問題

顧問團隊在做 client proposal、訪談前準備或產業研究時，通常要快速回答：

- 這家公司是誰，屬於什麼產業？
- 最近有哪些新聞訊號？
- 年報裡管理層自己揭露了哪些風險？
- 哪些風險需要優先追問？
- 哪些議題可以延伸成數位轉型機會？

這個專案把上述工作拆成可重複的資料流程：收資料、清資料、抽證據、分類、打嚴重度、彙總成 dashboard/report。重點不是取代人的判斷，而是讓人更快拿到第一輪 evidence。

## 3. 架構總覽

```text
User / Interview Demo
  |
  v
app.py (Streamlit UI)
  |
  +-- company_registry.py       公司基本資料查找
  +-- news_collector.py         RSS 或 demo news 收集
  +-- annual_report_reader.py   PDF 年報文字抽取、清理、切 chunk
  +-- industry_trend_reader.py  趨勢、成長因子、風險句抽取
  +-- kri_extractor.py          KRI 字典比對、證據句抽取、嚴重度 scoring
  +-- report_generator.py       Markdown / JSON / dashboard-ready table
  +-- excel_report_generator.py Excel workbook、COUNTIFS、SUMIFS
  |
  v
data/exports + data/reports + Streamlit dashboard
```

你可以把它理解成三層：

- Input layer：公司資料、新聞、年報、產業趨勢。
- Extraction layer：把文字轉成結構化證據列，例如 `kri_category`、`severity_hint`、`evidence_sentence`。
- Delivery layer：把證據整理成 dashboard、Excel、Markdown/JSON 報告，讓顧問或 business user 能看懂。

## 4. 真正的資料流

CLI pipeline 的主流程在 `src/pipeline.py`，核心邏輯長這樣：

```python
registry_df = load_company_registry(registry_path)
company_profile = get_company_profile(registry_df, company_name=company)

news_df = _load_or_collect_news(
    company=company_profile.get("company_name", company),
    industry=industry,
    sample_news_path=sample_news_path,
    project_root=project_root,
    use_sample_data=use_sample_data,
)

annual_text = _load_annual_report_text(
    annual_report=annual_report,
    company_name=company_profile.get("company_name", company),
    industry=industry,
    project_root=project_root,
    use_sample_data=use_sample_data,
)

annual_text = clean_annual_report_text(annual_text)
annual_chunks = chunk_text(annual_text)
trend_notes = _load_or_generate_trend_notes(company, industry, project_root)
kri_df = _extract_all_kri(news_df, annual_text, company, industry)
dashboard_df = build_dashboard_kpi_kri_table(news_df, kri_df, trend_notes)
```

這段的重點：

- `company_profile` 是分析的 company anchor。
- `news_df` 是外部市場訊號。
- `annual_text` 是公司自己揭露的管理層語言。
- `kri_df` 是核心成果，代表「從文字中抽出來的風險證據」。
- `dashboard_df` 是給 Streamlit、Excel、Power BI 類工具使用的彙總表。

## 5. Streamlit app 怎麼跑

`app.py` 是互動式 demo 的入口。使用者在 sidebar 輸入 company、ticker、industry，上傳年報 PDF，按下 Run Analysis。

```python
if st.button("Run Analysis", type="primary"):
    run_analysis(inputs)

if st.button("Generate Report"):
    generate_report(inputs["use_llm"], lang="zh" if lang == "中文" else "en")
```

`run_analysis()` 做五件事：

- 讀公司基本資料。
- 讀上傳的 PDF 年報。
- 如果使用 demo mode，載入 `data/demo` 裡已準備好的新聞、KRI、趨勢資料。
- 如果不用 demo mode，就從 RSS 抓新聞，再從新聞與年報重新抽 KRI。
- 把結果放進 `st.session_state`，後面的 tabs 都讀同一份結果。

`generate_report()` 則把 session state 裡的 evidence 交給 `report_generator.py` 產生 Markdown/JSON brief。

## 6. 公司基本資料怎麼找

公司資料邏輯在 `src/company_registry.py`。它先把不同 CSV 欄位名稱標準化，再用 ticker、company id、company name 查找。

```python
STANDARD_COLUMNS = [
    "company_id",
    "ticker",
    "company_name",
    "industry",
    "address",
    "unified_business_number",
    "chairman",
    "general_manager",
    "listing_date",
    "source",
]
```

查找不是只做完全相等，它會先 normalize：

```python
def _normalize_text(value):
    text = str(value or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(
        r"\b(company|corporation|corp|co|ltd|limited|inc|holding|holdings)\b",
        " ",
        text,
    )
    text = re.sub(r"[\s\.\,\-_/()]+", "", text)
    return text
```

所以 `TSMC` 可以對到 `Taiwan Semiconductor Manufacturing Company`，`Foxconn` 可以對到 `Hon Hai Precision Industry`。這對 demo 很重要，因為使用者不一定輸入完整公司名稱。

## 7. 新聞怎麼抽

新聞模組在 `src/news_collector.py`。它支援兩種模式：

- demo mode：讀本機 CSV，確保面試時離線也能跑。
- live mode：讀 `configs/rss_sources.yaml`，用 RSS 抓文章。

RSS 抓完後，真正的 filter 在這裡：

```python
def filter_articles_by_keyword(df, keyword):
    terms = [term.lower() for term in keyword.split() if term.strip()]

    searchable_text = (
        df["title"].fillna("").astype(str)
        + " "
        + df["summary"].fillna("").astype(str)
    ).str.lower()

    mask = searchable_text.apply(
        lambda text: any(term in text for term in terms)
    )

    return df.loc[mask, ARTICLE_COLUMNS].drop_duplicates(
        subset=["url", "title"]
    )
```

重要細節：

- 它不是要求整句完全符合，而是把 keyword 拆成 terms，做 OR match。
- 例如 `Taiwan semiconductor AI` 只要 title/summary 出現 Taiwan、semiconductor 或 AI，就可能被保留。
- 這樣 recall 比較高，適合 MVP 和 RSS 場景，但 precision 需要後續人審。
- `drop_duplicates(["url", "title"])` 避免同一篇新聞重複進入分析。

## 8. 年報 PDF 怎麼抽

年報模組在 `src/annual_report_reader.py`。它的處理順序是：

```text
PDF file
  -> pdfplumber extract_text()
  -> clean_annual_report_text()
  -> identify_annual_report_sections()
  -> chunk_text(chunk_size=1200, overlap=150)
  -> structured dict
```

核心抽文字邏輯：

```python
with pdfplumber.open(str(path)) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_parts.append(page_text)
```

清理邏輯做三件重要的事：

```python
cleaned = text.replace("\x00", " ")
cleaned = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", cleaned)
cleaned = re.sub(r"(?m)^\s*\d+\s*$", "", cleaned)
```

- 移除 PDF 裡常見的 null character。
- 把 `manu-\nfacturing` 這種斷字接回 `manufacturing`。
- 移除單獨頁碼，避免頁碼被當成句子。

再來用 section anchors 找年報章節：

```python
SECTION_PATTERNS = {
    "business_overview": [r"\bbusiness overview\b", r"\bour business\b"],
    "risk_factors": [r"\brisk factors\b", r"\bprincipal risks\b"],
    "financial_overview": [r"\bfinancial overview\b"],
    "management_discussion": [r"\bmanagement discussion\b", r"\bmd&a\b"],
}
```

最後切 chunk：

```python
def chunk_text(text, chunk_size=1200, overlap=150):
    words = text.split()
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append({
            "chunk_id": chunk_id,
            "start_word": start,
            "end_word": end,
            "text": " ".join(words[start:end]),
        })
        start = end - overlap
```

為什麼要 overlap？因為風險描述常常跨段落，如果完全硬切，一句重要風險可能被切到兩個 chunk 中間。150 words overlap 可以保留上下文，未來接 LLM 或 semantic search 時也更穩。

## 9. KRI 到底怎麼抽

KRI 是 Key Risk Indicator。這個專案不是用黑盒模型直接判斷風險，而是先用透明的 keyword dictionary 抽「證據句」，再交給人判斷。

KRI 字典在 `src/kri_extractor.py`：

```python
def load_kri_dictionary():
    return {
        "liquidity risk": [
            "liquidity",
            "working capital",
            "current ratio",
            "short-term funding",
        ],
        "supply chain risk": [
            "supply chain",
            "supplier",
            "shortage",
            "logistics",
            "raw material",
            "delivery delay",
        ],
        "geopolitical risk": [
            "geopolitical",
            "trade restriction",
            "export control",
            "tariff",
            "cross-strait",
        ],
    }
```

實際抽取邏輯：

```python
for sentence in sentences:
    lower_sentence = sentence.lower()

    for category, keywords in dictionary.items():
        for keyword in keywords:
            if keyword.lower() in lower_sentence:
                records.append({
                    "source_id": source_id,
                    "company_name": company_name or "",
                    "industry": industry or "",
                    "source_type": source_type,
                    "kri_category": category,
                    "matched_keyword": keyword,
                    "evidence_sentence": sentence,
                    "severity_hint": _severity_hint(sentence),
                    "risk_score_hint": 0,
                })
                break
```

重要細節：

- 單位是 sentence，不是整篇文章。這樣輸出會是可審核的 evidence sentence。
- 一句話可以命中多個 category，但同一 category 只記一個 keyword，避免 duplicate 太吵。
- `source_type` 會標記 evidence 來自 `news` 或 `annual_report`，後面可以比較「市場新聞說的風險」和「公司年報自己揭露的風險」。
- `risk_score_hint` 一開始填 0，真正分數由 `score_kri_mentions()` 統一處理。

## 10. 嚴重度怎麼判

嚴重度不是財務模型，而是 prioritization hint。它用句子裡的風險語氣判斷 high、medium、low：

```python
HIGH_SEVERITY_WORDS = [
    "significant",
    "material",
    "severe",
    "critical",
    "default",
    "sharp decline",
    "liquidity pressure",
]

MEDIUM_SEVERITY_WORDS = [
    "decline",
    "shortage",
    "delay",
    "loss",
    "uncertainty",
    "pressure",
    "disruption",
    "volatile",
    "risk",
]
```

判斷方式：

```python
def _severity_hint(sentence):
    lower_sentence = sentence.lower()

    if any(word in lower_sentence for word in HIGH_SEVERITY_WORDS):
        return "high"

    if any(word in lower_sentence for word in MEDIUM_SEVERITY_WORDS):
        return "medium"

    return "low"
```

分數映射：

```python
result["risk_score_hint"] = result["severity_hint"].map({
    "high": 3,
    "medium": 2,
    "low": 1,
})
```

面試時要講清楚：這不是最終風險評分，只是讓 analyst 決定哪些 evidence 先看。真正決策仍需要 source quality、materiality、財務數字和管理層訪談。

## 11. 產業趨勢怎麼抽

`src/industry_trend_reader.py` 用一樣透明的 rule-based extractor。它把文字分成句子後，依照不同 keyword list 抽成結構化欄位：

```python
return {
    "main_trends": _extract_keyword_sentences(cleaned, TREND_KEYWORDS),
    "growth_drivers": _extract_keyword_sentences(cleaned, GROWTH_DRIVER_KEYWORDS),
    "risks": _extract_keyword_sentences(cleaned, RISK_KEYWORDS),
    "key_companies": _extract_key_companies(cleaned),
    "data_indicators": _extract_data_indicators(cleaned),
    "digital_transformation_opportunities": _extract_keyword_sentences(
        cleaned,
        DIGITAL_TRANSFORMATION_KEYWORDS,
    ),
}
```

例如：

- `TREND_KEYWORDS` 抓 trend、automation、AI、cloud、sustainability。
- `GROWTH_DRIVER_KEYWORDS` 抓 growth、demand、investment、capacity。
- `RISK_KEYWORDS` 抓 risk、uncertainty、regulation、geopolitical、shortage。
- `DATA_INDICATOR_KEYWORDS` 抓 revenue、CAGR、market size、gross margin、capex、%、billion。

這裡的價值是把文章或年報中的長文字拆成顧問報告會用的幾類訊號，而不是只產生一段 summary。

## 12. 分析怎麼從 evidence 變成 insight

`src/report_generator.py` 做的事是把 evidence 分成三層，避免 hallucination：

- 來源事實：公司基本資料、新聞摘要、年報片段、KRI evidence sentence。
- 分析解讀：風險優先順序、商業影響、數位轉型機會。
- 建議追問：管理層訪談問題、資料驗證步驟、下一步分析。

dashboard-ready summary 的邏輯：

```python
high = _count_severity(kri_df, "high")
medium = _count_severity(kri_df, "medium")
low = _count_severity(kri_df, "low")

overall = "High" if high > 0 else "Medium" if medium > 0 else "Low"

return pd.DataFrame([{
    "total_news_count": len(news_df),
    "total_kri_count": len(kri_df),
    "high_severity_kri_count": high,
    "medium_severity_kri_count": medium,
    "low_severity_kri_count": low,
    "overall_risk_level": overall,
}])
```

這代表分析不是神秘的：先計算高/中/低 KRI 數量，再決定整體風險等級，最後給出 follow-up。這很適合面試，因為你可以清楚說明每個結果怎麼來。

## 13. KRI Pivot Table 怎麼分析

Streamlit dashboard 裡的 KRI pivot table 相當於 Excel COUNTIFS：

```python
pivot = (
    kri_df.groupby(["kri_category", "severity_hint"])
    .size()
    .unstack(fill_value=0)
)
```

Excel 等效概念：

```excel
=COUNTIFS(kri_category, "supply chain risk", severity, "high")
```

怎麼解讀：

- 某 category 的 high 數量高：優先做 management interview 和 source validation。
- 某 category 在新聞出現、年報也出現：市場和管理層都承認該風險，可信度提高。
- 某 category 只在新聞出現、年報沒出現：可能是外部市場訊號，也可能是管理層揭露落差，需要追問。
- 某 category 都是 low：可以先 monitoring，不一定是立即風險。

## 14. Excel 報表展示什麼能力

Excel 產生器在 `src/excel_report_generator.py`。它不是只把 CSV dump 成 Excel，而是做了可分析 workbook：

- sheet：Company_Profile、News_Articles、KRI_Evidence、Summary_By_Company、Dashboard_View。
- freeze panes、filter、欄寬調整。
- conditional formatting：high/medium/low 不同底色。
- 公式：COUNTIFS、SUMIFS、XLOOKUP。

公式例子：

```python
ws.cell(
    row=row,
    column=start_col,
    value='=COUNTIFS(KRI_Evidence!B:B,A2,KRI_Evidence!H:H,"high")',
)

ws.cell(
    row=row,
    column=start_col + 2,
    value="=SUMIFS(KRI_Evidence!I:I,KRI_Evidence!B:B,A2)",
)
```

面試時可說：Python 負責自動化資料整理，Excel 負責讓 business user 可以 review、filter、validate。這很符合顧問交付情境。

## 15. LLM 在哪裡

這個專案預設不需要 LLM。`src/summarizer.py` 支援 optional LLM mode，但只有在 `use_llm=True` 且 `OPENAI_API_KEY` 存在時才會呼叫 API。

```python
if use_llm and _can_use_llm():
    return _generate_llm_brief(input_data, brief_type="company")

return _generate_rule_based_brief(input_data, brief_type="company")
```

LLM prompt 的 guardrails：

```text
- Only summarize the evidence provided below.
- Do not invent facts, numbers, companies, risks, or sources.
- If evidence is insufficient, say evidence is insufficient.
- Cite source titles, URLs, or source IDs wherever available.
- Clearly label facts as Fact and judgment as Interpretation.
```

所以這個專案的定位是 evidence-grounded analysis，不是讓 LLM 自由生成。

## 16. 你要怎麼 demo

建議 demo 順序：

1. 打開 Streamlit，先說這是 interview mode，所以可以用本機 demo data，不怕網路失敗。
2. 在 sidebar 指出 company、ticker、industry、annual report upload。
3. 按 Run Analysis，展示五個 tabs。
4. 在 KRI tab 停久一點，因為這是核心：evidence table、severity、pivot table。
5. 到 Industry Trends tab，說明趨勢如何連到 digital transformation opportunities。
6. 到 Brief tab，展示 report 不是純摘要，而是 facts、interpretation、follow-up。
7. 最後提 Excel workbook，說可以交給 business user 或顧問團隊 review。

## 17. 面試最重要的講法

### Q: 這個專案最核心的價值是什麼？

它把顧問前期研究流程結構化。以前 analyst 可能要手動看新聞、年報、公司資料，再整理風險表。這個 MVP 把資料收集、KRI 抽取、嚴重度優先排序和報告生成自動化，讓人把時間花在 validation 和 business interpretation。

### Q: 你怎麼確定抽出來的東西可信？

我沒有把它包裝成最終判斷，而是 evidence extraction。每一列都有 `source_type`、`source_id`、`matched_keyword`、`evidence_sentence`。所以 reviewer 可以回到原文檢查。報告也把 fact、interpretation、recommended follow-up 分開。

### Q: 為什麼不用一開始就全部用 LLM？

因為面試 MVP 要可解釋、可重現、離線也能跑。rule-based extraction 的好處是透明，面試官可以看到風險分類和嚴重度是怎麼來的。LLM 可以作為第二層 enhancement，用來提高 ambiguous sentence 的 recall，但不能取代 evidence guardrails。

### Q: 最大限制是什麼？

第一，keyword matching 可能漏掉語意相近但沒有命中 keyword 的句子。第二，severity 是根據語氣字詞，不是完整財務模型。第三，demo data 需要人確認來源品質。這些限制也指向下一步：加 LLM classifier、source quality score、financial ratio integration、time-series trend。

### Q: 跟 Deloitte Digital Technology 有什麼關係？

Deloitte 的工作常常要把資料、流程、風險和數位轉型連起來。這個專案展示我能用 Python 做資料處理，也能把技術輸出變成 business insight，例如 KRI dashboard、management interview questions、supplier risk monitoring、working capital dashboard。

## 18. 如何執行

在 Windows PowerShell：

```powershell
cd C:\Projects\Industry_intelligenceAgent\industry_intelligence_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

重新產生這份 guide：

```powershell
cd C:\Projects\Industry_intelligenceAgent\industry_intelligence_agent
python scripts\generate_interview_pdf.py
```

跑完整 pipeline：

```powershell
python scripts\run_pipeline.py --company "TSMC" --industry "semiconductor" --use-sample-data true --export-excel true --language zh-TW
```

## 19. 重要檔案地圖

```text
industry_intelligence_agent/
  app.py
    Streamlit demo 入口，處理 UI、session state、tabs、dashboard。

  src/company_registry.py
    公司資料 CSV 標準化、名稱 normalize、ticker/name search。

  src/news_collector.py
    demo CSV 或 RSS news collection，keyword filter，去重。

  src/annual_report_reader.py
    pdfplumber 抽文字，清理 PDF 斷字和頁碼，找章節，切 chunks。

  src/kri_extractor.py
    12 類 KRI dictionary，sentence extraction，severity hint，risk_score_hint。

  src/industry_trend_reader.py
    從文字抽 main trends、growth drivers、risks、data indicators、DT opportunities。

  src/report_generator.py
    產生 Markdown/JSON brief，建立 dashboard-ready KPI/KRI table。

  src/excel_report_generator.py
    產生 Excel workbook，加公式、篩選、凍結窗格、條件格式。

  src/pipeline.py
    CLI end-to-end orchestrator，把所有模組串起來並輸出 CSV/JSON/MD/XLSX。
```

## 20. 可以改進的方向

- 加 LLM classifier：處理 keyword 沒命中的語意風險句。
- 加 source quality score：依來源可信度、日期、是否有 URL 調整權重。
- 加財務資料：把 KRI 接到 revenue、gross margin、inventory days、DSO、cash flow。
- 加 time-series：追蹤同一類 KRI 在不同月份是否升溫。
- 加 PowerPoint export：更像 consulting deliverable。
- 加 tests：尤其是 PDF parsing、KRI extraction、report generation。

## 21. 你最後要記住的核心

這個專案不是在炫技，而是在展示一個完整的分析工作流：

```text
raw text and tables
  -> cleaned evidence
  -> KRI category and severity
  -> dashboard and Excel
  -> consulting brief
  -> human validation and next questions
```

如果面試官問很細，你就回到這條線：我怎麼收資料、怎麼抽句子、怎麼分類、怎麼打優先順序、怎麼把它變成 business decision support。
