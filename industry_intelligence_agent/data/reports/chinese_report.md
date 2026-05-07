# 產業情報與 KRI 風險分析報告

**公司：** Apple
**Ticker：** AAPL
**產業關鍵字：** consumer electronics semiconductor supply chain
**產生時間：** 2026-05-07T04:08:16.104939+00:00

## 1. Executive Summary 中文摘要
- 本報告為 Industry Intelligence Agent MVP 產出，目的在協助顧問快速整理新聞、年報與 KRI 風險證據，不是 production 系統。
- 本次分析包含 3 則網路新聞、0 段年報重點，以及 18 筆 KRI evidence。
- 嚴重度分布：高 0 筆、中 16 筆、低 2 筆。
- 主要風險主題：supply chain risk (6)、operational disruption risk (3)、trade/tariff risk (2)、cost pressure risk (2)、cybersecurity risk (2)
- 風險分數不是財務模型，severity 只是人工覆核的優先順序提示，最終決策仍需要 human review。

## 2. 資料來源
- 網路新聞：3 則，來源為 Google News RSS 或 sample fallback。
- 年報證據：0 段，優先擷取 Risk Factors 與 Management Discussion。
- 近期新聞標題：
  - Apple supply chain faces tariff and China exposure questions
  - Semiconductor shortages could delay product launches
  - Cybersecurity and supplier concentration remain board-level risks

## 3. 主要產業趨勢
- 從 KRI evidence 觀察，主要風險趨勢集中在：supply chain risk (6)、operational disruption risk (3)、trade/tariff risk (2)、cost pressure risk (2)、cybersecurity risk (2)。
- 近期新聞可作為市場外部訊號，需與年報揭露交叉驗證。

## 4. 年報 Risk Factors 重點
- 尚未上傳或成功解析年報 PDF。

## 5. KRI Evidence Table
| source_type | kri_category | severity_hint | risk_score_hint | detected_countries | detected_percentages | evidence_sentence |
| --- | --- | --- | --- | --- | --- | --- |
| sample_news | trade/tariff risk | low | 1 | China |  | Apple supply chain faces tariff and China exposure questions. |
| sample_news | supply chain risk | low | 1 | China |  | Apple supply chain faces tariff and China exposure questions. |
| sample_news | trade/tariff risk | medium | 2 | Taiwan, China |  | Consumer electronics companies may face tariff uncertainty, cost pressure, and supply chain disruption linked to China, Taiwan, and semiconductor component sourcing. |
| sample_news | supply chain risk | medium | 2 | Taiwan, China |  | Consumer electronics companies may face tariff uncertainty, cost pressure, and supply chain disruption linked to China, Taiwan, and semiconductor component sourcing. |
| sample_news | cost pressure risk | medium | 2 | Taiwan, China |  | Consumer electronics companies may face tariff uncertainty, cost pressure, and supply chain disruption linked to China, Taiwan, and semiconductor component sourcing. |
| sample_news | supply chain risk | medium | 2 |  |  | Semiconductor shortages could delay product launches. |
| sample_news | operational disruption risk | medium | 2 |  |  | Semiconductor shortages could delay product launches. |
| sample_news | supply chain risk | medium | 2 |  |  | A shortage of advanced chips and raw materials could delay production schedules and increase costs for global electronics brands. |
| sample_news | raw material risk | medium | 2 |  |  | A shortage of advanced chips and raw materials could delay production schedules and increase costs for global electronics brands. |
| sample_news | cost pressure risk | medium | 2 |  |  | A shortage of advanced chips and raw materials could delay production schedules and increase costs for global electronics brands. |
| sample_news | operational disruption risk | medium | 2 |  |  | A shortage of advanced chips and raw materials could delay production schedules and increase costs for global electronics brands. |
| sample_news | supply chain risk | medium | 2 |  |  | Cybersecurity and supplier concentration remain board-level risks. |
| sample_news | supplier concentration risk | medium | 2 |  |  | Cybersecurity and supplier concentration remain board-level risks. |
| sample_news | cybersecurity risk | medium | 2 |  |  | Cybersecurity and supplier concentration remain board-level risks. |
| sample_news | supply chain risk | medium | 2 | Taiwan, China, United States, EU |  | Companies with concentrated suppliers in Asia may face operational disruption, cybersecurity risk, and regulatory pressure across the United States, EU, China, and Taiwan. |
| sample_news | regulatory risk | medium | 2 | Taiwan, China, United States, EU |  | Companies with concentrated suppliers in Asia may face operational disruption, cybersecurity risk, and regulatory pressure across the United States, EU, China, and Taiwan. |
| sample_news | cybersecurity risk | medium | 2 | Taiwan, China, United States, EU |  | Companies with concentrated suppliers in Asia may face operational disruption, cybersecurity risk, and regulatory pressure across the United States, EU, China, and Taiwan. |
| sample_news | operational disruption risk | medium | 2 | Taiwan, China, United States, EU |  | Companies with concentrated suppliers in Asia may face operational disruption, cybersecurity risk, and regulatory pressure across the United States, EU, China, and Taiwan. |

## 6. 商業影響
- trade/tariff risk：關稅與貿易政策可能影響成本結構、售價、供應鏈配置與毛利率。
- supply chain risk：供應鏈延遲或短缺可能影響交期、庫存策略與營收認列。
- cost pressure risk：成本壓力可能壓縮毛利率，需追蹤價格轉嫁能力。
- operational disruption risk：需進一步評估財務與營運影響。
- raw material risk：需進一步評估財務與營運影響。
- supplier concentration risk：供應商集中可能降低議價能力並提高營運中斷風險。
- cybersecurity risk：需進一步評估財務與營運影響。
- regulatory risk：需進一步評估財務與營運影響。

## 7. 建議客戶下一步
- 回到新聞 URL 與年報原文，驗證 high/medium KRI evidence 的來源與語境。
- 將 KRI 類別映射到可量化 KPI，例如毛利率、庫存天數、供應商交期、現金流、負債比率。
- 與管理層訪談確認哪些風險已被內部追蹤，哪些只是外部市場訊號。
- 若要 production 化，加入來源可信度、時間序列、人工覆核狀態與權限控管。
- 納入追蹤：請確認 trade/tariff risk 的來源可靠性、財務影響、管理層是否已揭露，以及是否需要客戶訪談追問。
- 納入追蹤：請確認 supply chain risk 的來源可靠性、財務影響、管理層是否已揭露，以及是否需要客戶訪談追問。
- 納入追蹤：請確認 cost pressure risk 的來源可靠性、財務影響、管理層是否已揭露，以及是否需要客戶訪談追問。

## 8. 限制與治理
- 本工具是 MVP，不是 production 風險管理平台。
- risk_score_hint 不是財務模型，不代表損失金額、違約機率或投資建議。
- severity_hint 是 prioritization hint，只用來協助人工排序與覆核。
- Google News RSS 與年報 PDF 解析可能受資料品質、網路狀態、PDF 格式影響。
- 最終商業判斷需由顧問、財務/法務/風險團隊進行 human review，並回到原始來源驗證。