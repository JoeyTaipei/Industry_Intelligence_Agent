"""Generate a read-aloud interview script PDF in Traditional Chinese.

Uses Microsoft JhengHei (msjh.ttc) for proper Traditional Chinese rendering on Windows.
"""

from __future__ import annotations

import pathlib

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ── Font setup ────────────────────────────────────────────────────────────────
FONT_PATH      = "C:/Windows/Fonts/msjh.ttc"
FONT_PATH_BOLD = "C:/Windows/Fonts/msjhbd.ttc"

pdfmetrics.registerFont(TTFont("MSJH",     FONT_PATH,      subfontIndex=0))
pdfmetrics.registerFont(TTFont("MSJH-Bold", FONT_PATH_BOLD, subfontIndex=0))

ZH      = "MSJH"
ZH_BOLD = "MSJH-Bold"

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = PROJECT_ROOT / "data" / "report" / "interview_spoken_script.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

W = A4[0] - 4 * cm
styles = getSampleStyleSheet()

# ── Style factory ──────────────────────────────────────────────────────────────
def _s(name: str, font: str = ZH, size: int = 10, leading: int = 16,
       color=colors.black, align=TA_LEFT, space_before: int = 0,
       space_after: int = 5, left_indent: int = 0, bg=None,
       border_color=None, border_width: float = 0,
       border_padding: int = 0) -> ParagraphStyle:
    kw = dict(
        fontName=font, fontSize=size, leading=leading, textColor=color,
        alignment=align, spaceBefore=space_before, spaceAfter=space_after,
        leftIndent=left_indent,
    )
    if bg:
        kw["backColor"] = bg
    if border_color:
        kw["borderColor"] = border_color
        kw["borderWidth"] = border_width
        kw["borderPadding"] = border_padding
    return ParagraphStyle(f"custom_{name}", parent=styles["Normal"], **kw)


COVER_TITLE = _s("ct",  ZH_BOLD, 24, 32, colors.HexColor("#17324d"), TA_CENTER, space_after=6)
COVER_SUB   = _s("cs",  ZH,      13, 20, colors.HexColor("#2e6da4"), TA_CENTER, space_after=4)
COVER_NOTE  = _s("cn",  ZH,       9, 13, colors.HexColor("#888888"), TA_CENTER, space_after=3)
COVER_BODY  = _s("cb",  ZH,      10, 16, colors.HexColor("#444444"), TA_CENTER, space_after=4)

H1 = _s("h1", ZH_BOLD, 14, 21, colors.HexColor("#17324d"), space_before=10, space_after=5)
H2 = _s("h2", ZH_BOLD, 11, 16, colors.HexColor("#2e6da4"), space_before=7,  space_after=4)

BODY   = _s("body",   ZH,      9.5, 15)
SCRIPT = _s("script", ZH,      10.5, 18, left_indent=10, space_after=8,
             bg=colors.HexColor("#eef4ff"),
             border_color=colors.HexColor("#2e6da4"), border_width=2.5, border_padding=10)
WARN   = _s("warn",   ZH,       9,  13, colors.HexColor("#a04000"),
             bg=colors.HexColor("#fff8f0"),
             border_color=colors.HexColor("#e0a060"), border_width=1, border_padding=6)
Q_ST   = _s("q",      ZH_BOLD, 10,  15, colors.HexColor("#c0392b"), space_before=10, space_after=2)
A_ST   = _s("a",      ZH,      10,  15, left_indent=12, space_after=8)
NUM    = _s("num",    ZH,       9.5, 15, left_indent=14, space_after=4)
CAP    = _s("cap",    ZH,       8,  11, colors.HexColor("#777777"), space_after=3)

TH_ST  = _s("th", ZH_BOLD, 8.3, 12, colors.white)
TD_ST  = _s("td", ZH,      8.1, 12)


# ── Builders ──────────────────────────────────────────────────────────────────
def p(t: str)      -> Paragraph: return Paragraph(t, BODY)
def script(t: str) -> Paragraph: return Paragraph(t, SCRIPT)
def h1(t: str)     -> Paragraph: return Paragraph(t, H1)
def h2(t: str)     -> Paragraph: return Paragraph(t, H2)
def warn(t: str)   -> Paragraph: return Paragraph(t, WARN)
def cap(t: str)    -> Paragraph: return Paragraph(t, CAP)
def q(t: str)      -> Paragraph: return Paragraph(f"❓ 面試官：{t}", Q_ST)
def a(t: str)      -> Paragraph: return Paragraph(f"你說：{t}", A_ST)
def sp(n: int = 8) -> Spacer:    return Spacer(1, n)

def hr() -> HRFlowable:
    return HRFlowable(width=W, thickness=0.5,
                      color=colors.HexColor("#c9d3df"), spaceBefore=4, spaceAfter=6)

def tbl(rows: list[list[str]], widths: list[float],
        hbg: str = "#17324d") -> Table:
    cells = []
    for i, row in enumerate(rows):
        st = TH_ST if i == 0 else TD_ST
        cells.append([Paragraph(c, st) for c in row])
    t = Table(cells, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor(hbg)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ("GRID",           (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d3df")),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("LEFTPADDING",    (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 5),
    ]))
    return t


# ── Content ───────────────────────────────────────────────────────────────────
story = []

# Cover
story += [
    sp(50),
    Paragraph("面試前大聲念", COVER_TITLE),
    Paragraph("Industry Intelligence Agent 口語腳本", COVER_SUB),
    sp(6),
    Paragraph("Deloitte Digital Technology Intern  ·  Joey Wu  ·  2026", COVER_NOTE),
    sp(12),
    Paragraph("怎麼用這份文件", _s("cbt", ZH_BOLD, 11, 16, colors.HexColor("#555555"), TA_CENTER)),
    sp(4),
    Paragraph(
        "每一段藍色框框就是你要念出來的內容。旁邊的小字是給你的提示，不用念出來。"
        "面試前一天把整份念一遍，面試當天再把數字那一頁默念一次就夠了。",
        COVER_BODY,
    ),
    PageBreak(),
]

# ── 1. 開場白 ─────────────────────────────────────────────────────────────────
story += [
    h1("第一段：開場白（念 30 秒）"),
    hr(),
    cap("面試官說「介紹一下你的專案」或「tell me about yourself」時念這段。"),
    sp(),
    script(
        "我做的這個專案叫 Industry Intelligence Agent，是一個用 Python 和 Streamlit 建立的產業情報分析工具。"
        "它的核心功能是把公司新聞、年報文字和產業趨勢，自動整理成 KRI 風險證據清單，"
        "然後產生一份中英雙語的顧問式報告和互動儀表板。"
        "Demo 場景是台灣半導體和 AI server 產業，以台積電為主，用的是 2026 年的真實新聞數據。"
    ),
    warn("說完之後停頓一下，讓面試官接話。不要急著繼續講。"),
    PageBreak(),
]

# ── 2. 解決什麼問題 ───────────────────────────────────────────────────────────
story += [
    h1("第二段：解決什麼問題（念 1 分鐘）"),
    hr(),
    cap("面試官問「為什麼做這個？」或「這個工具的價值是什麼？」時念這段。"),
    sp(),
    script(
        "顧問在客戶訪談前，需要快速回答三個問題：\n"
        "一，這家公司最近有什麼市場訊號？\n"
        "二，年報裡管理層自己說了哪些風險？\n"
        "三，哪些風險需要優先追問？\n\n"
        "以前這些工作要手動搜尋新聞、讀年報、整理筆記，可能要花半天到一天。"
        "我的工具把這個流程自動化——輸入公司名稱、上傳 PDF、按一個按鈕，"
        "五分鐘內就能拿到結構化的 KRI 風險證據清單和報告。\n\n"
        "重點不是取代顧問的判斷，而是讓顧問更快拿到第一輪 evidence，"
        "把時間省下來做更高價值的事：跟客戶訪談、設計解決方案、建立 business case。"
    ),
    PageBreak(),
]

# ── 3. 技術方法 ───────────────────────────────────────────────────────────────
story += [
    h1("第三段：技術方法——KRI 怎麼抽（念 1 分鐘）"),
    hr(),
    cap("面試官問「技術上怎麼做的？」或「KRI 是什麼？」時念這段。"),
    sp(),
    script(
        "KRI 是 Key Risk Indicator，關鍵風險指標。它跟 KPI 不一樣——"
        "KPI 衡量現在的表現，KRI 是提前預警的訊號。\n\n"
        "舉例來說，台積電今年第一季營收年增百分之四十五點二，這是 KPI。"
        "但是台灣進口百分之九十七的能源、LNG 只有十一天的庫存，"
        "這是 supply chain risk 的 KRI 訊號——它在財務數字出問題之前就已經在發出警告了。\n\n"
        "我的系統有十二個 KRI 類別，每個類別有五到八個關鍵字。"
        "程式掃過新聞和年報的每一句話，只要包含關鍵字，就把那句話抽出來當作 evidence。"
        "然後再根據句子裡有沒有出現像 significant、material、severe 這些字，"
        "判斷嚴重度是高、中、還是低，分數是三、二、一。"
    ),
    sp(6),
    p("12 個 KRI 類別一覽："),
    tbl([
        ["類別", "核心關鍵字（舉例）", "Demo 發現"],
        ["supply chain risk",           "shortage, logistics, delivery delay",    "荷姆茲海峽封閉、氦氣翻倍"],
        ["geopolitical risk",           "tariff, export controls, cross-strait",  "中國晶片 50% 關稅"],
        ["customer concentration risk", "major customer, top 5 customers",        "TSMC 通知 NVIDIA/Broadcom 產能受限"],
        ["ESG / sustainability risk",   "energy usage, carbon, emissions",        "台灣 97% 能源進口、11 天 LNG"],
        ["regulatory risk",             "regulation, compliance, sanction",       "稀土出口管制（鎵、鍺、石墨）"],
        ["profitability risk",          "gross margin, pricing pressure",          "Arizona 廠比台灣貴 30%"],
        ["inventory risk",              "inventory, obsolete, stock level",       "關稅不確定影響訂單時序"],
        ["cash flow risk",              "cash flow, capex, free cash flow",       "美國廠大規模投資義務"],
        ["liquidity risk",              "liquidity, working capital",             "訂單波動造成 WC 壓力"],
        ["receivables risk",            "accounts receivable, bad debt",          "大客戶付款條件差異"],
        ["cyber / digital risk",        "cyber, data breach, OT",                "智慧工廠 OT/IT 整合"],
        ["leverage risk",               "debt, borrowings, covenant",             "大規模資本支出融資"],
    ], [3.8*cm, 5*cm, 7.6*cm]),
    PageBreak(),
]

# ── 4. 必背數字 ───────────────────────────────────────────────────────────────
story += [
    h1("第四段：面試必背數字（可以直接引用）"),
    hr(),
    cap("這些數字在面試中說出來，立刻讓回答有說服力。來源都是 2026 年真實新聞。"),
    sp(),
    tbl([
        ["數字", "事實", "來源"],
        ["+45.2%",   "台積電 2026 年 3 月營收年增",              "HeyGoTrade, Apr 2026"],
        ["415.2B NTD", "台積電 3 月月營收金額",                  "HeyGoTrade, Apr 2026"],
        ["+28%",     "台積電股利增加幅度",                        "247 Wall St, Feb 2026"],
        [">65%",     "台積電全球先進製程市占率",                  "Yahoo Finance, Apr 2026"],
        ["97%",      "台灣能源進口依存度",                        "Yahoo Finance, Apr 2026"],
        ["11 天",    "台灣 LNG 庫存（無進口情況下）",             "Yahoo Finance, Apr 2026"],
        ["50%",      "美國對中國半導體進口關稅（2026-01 起）",    "Tom's Hardware, Apr 2026"],
        ["15%",      "台灣享有的美國優惠關稅上限",                "CNBC, Jan 2026"],
        ["USD 250B", "台灣承諾在美投資金額",                      "CNBC, Jan 2026"],
        ["+30%",     "TSMC Arizona 廠比台灣廠貴多少",             "247 Wall St, Feb 2026"],
        ["USD 465B", "TSMC Arizona 總投資目標（11 座廠）",         "abhs.in, Apr 2026"],
        ["2x",       "氦氣價格漲幅（卡達供應中斷後）",            "HeyGoTrade, Apr 2026"],
        ["30%",      "美中貨物總關稅（暫停至 2026-11）",          "Tax Foundation, May 2026"],
        ["Jun 2027", "美國對中國晶片新關稅生效日",                "Tom's Hardware, Apr 2026"],
    ], [2.2*cm, 8.6*cm, 5.6*cm]),
    sp(6),
    script(
        "念法範例：「我的 demo 用的全是真實數據。台積電今年三月營收年增百分之四十五點二，"
        "但同時台灣有兩個高嚴重度的 KRI——"
        "能源進口依存度百分之九十七，還有荷姆茲海峽封閉後 LNG 只剩十一天的庫存。"
        "這說明強勁的財務表現背後，有很具體的供應鏈脆弱性需要追問。」"
    ),
    PageBreak(),
]

# ── 5. 商業影響 ───────────────────────────────────────────────────────────────
story += [
    h1("第五段：商業影響——連結到收入和成本（念 1 分鐘）"),
    hr(),
    cap("面試官問「這些風險對業務有什麼影響？」或「你怎麼把分析變成 insight？」時念這段。"),
    sp(),
    script(
        "KRI evidence 抽出來之後，我做了一個商業影響分析，把所有風險分成五個維度。\n\n"
        "第一，營收影響。客戶集中度高，單一客戶訂單異動會直接衝擊營收穩定性。"
        "需要確認前五大客戶的佔比，以及訂單取消或延遲的條款。\n\n"
        "第二，成本影響。關稅、法規合規、Arizona 廠的建置成本，"
        "都可能提高 COGS、壓縮毛利率。要追蹤公司有沒有辦法把成本轉嫁給客戶。\n\n"
        "第三，供應鏈和營運影響。供應鏈中斷可能造成交期延誤、庫存不足。"
        "需要評估替代料源，以及安全庫存的水位夠不夠。\n\n"
        "第四，法規地緣政治影響。出口管制、稀土限制，會增加合規成本和市場准入風險。\n\n"
        "第五，客戶需求影響。大客戶突然改訂單、需求預測不準，會放大整個收入的波動。\n\n"
        "每個維度都對應到可以量化追蹤的 KPI："
        "庫存天數 DIO、應收帳款天數 DSO、毛利率、現金轉換週期 CCC。"
    ),
    PageBreak(),
]

# ── 6. 建議下一步 ─────────────────────────────────────────────────────────────
story += [
    h1("第六段：建議下一步——展示顧問思維（念 1 分鐘）"),
    hr(),
    cap("面試官問「如果你是顧問你會怎麼做？」或「分析之後然後呢？」時念這段。"),
    sp(),
    script(
        "我整理了五組建議，這是最能展示顧問思維的部分。\n\n"
        "第一組，立即檢查。確認 revenue by region、供應商集中度、gross margin 的趨勢。"
        "這三個是最快能判斷風險嚴不嚴重的切入點。\n\n"
        "第二組，數據分析。追蹤庫存天數 DIO、應收帳款天數 DSO、現金轉換週期 CCC，"
        "同時做關稅情境的敏感度分析——如果關稅再漲一成，毛利率影響是多少。\n\n"
        "第三組，Dashboard 監控。建立一個 KRI severity dashboard，"
        "高嚴重度項目用紅色警示、每週更新，讓管理層可以即時看到風險訊號的變化。\n\n"
        "第四組，管理層決策議題。問三個問題："
        "哪些風險已有對策？資本支出和供應鏈多元化的優先順序？"
        "哪些 KPI 目前已在月度 review 中追蹤？\n\n"
        "第五組，人工覆核。優先覆核四筆高嚴重度的 KRI evidence，"
        "回到原始新聞 URL 和年報段落，確認語境正確、沒有斷章取義。"
    ),
    PageBreak(),
]

# ── 7. Q&A ────────────────────────────────────────────────────────────────────
story += [
    h1("第七段：建議如何確定對企業有效（念 1 分鐘）"),
    hr(),
    cap("面試官問「你怎麼知道你的建議真的有用？」或「怎麼驗證分析結果？」時念這段。這是最難的問題，也是最能拉開差距的回答。"),
    sp(),
    script(
        "我在報告的建議下一步設計了一個驗證框架。每一條建議都有三個要素：\n\n"
        "第一，一個可量化的衡量 KPI。"
        "例如 supply chain risk 的建議是確認替代料源，對應的 KPI 是供應商交期達成率和 single-source 零組件數量。"
        "不是說「看一下供應鏈」，而是要記錄現在供應商交期達成率是多少，這樣才有 before 的基準。\n\n"
        "第二，一個可以向管理層驗證的問題。"
        "例如「目前有幾個零組件無替代來源？」這個問題不是我能從新聞裡找到答案的，"
        "需要管理層確認。如果管理層說「我們已經有替代料源了」，那這個風險的優先順序就下降。"
        "如果說「我們沒有想過這個問題」，那就是一個真正的 gap。\n\n"
        "第三，一個 30/60 天的 review 機制。"
        "30 天後確認前三項行動是否已啟動；60 天後比對 KPI 基準線是否移動；"
        "同時重新執行 KRI extraction，看高嚴重度的項目有沒有減少。\n\n"
        "這三個要素加在一起，讓建議從『感覺有用』變成『可以被驗證有用』。"
        "這也是為什麼我說這是 evidence-based prioritization，不是財務模型——"
        "建議的有效性要靠客戶資料和管理層確認，不是靠我的分析單獨決定。"
    ),
    sp(6),
    p("每個 KRI 類別的建議結構："),
    tbl([
        ["KRI 類別", "建議行動", "衡量 KPI", "管理層問題", "預期產出"],
        ["supply chain risk",
         "確認替代料源清單，為 single-source 供應商建立切換計畫",
         "供應商交期達成率、安全庫存天數、single-source 零組件數",
         "目前有幾個零組件無替代來源？",
         "識別 single-source 零組件並啟動替代評估"],
        ["geopolitical risk",
         "計算各關稅情境下 COGS 增量與毛利率敏感度",
         "關稅影響 COGS 增量（USD）、毛利率敏感度",
         "是否已做過關稅情境 stress test？",
         "完成情境模型，識別最脆弱產品線"],
        ["customer concentration risk",
         "計算前五大客戶各自營收佔比，確認訂單取消條款",
         "前五大客戶佔比 %、訂單能見度（週數）",
         "若最大客戶縮減 20%，revenue 影響是多少？",
         "建立客戶集中度熱力圖，設定多元化觸發閾值"],
        ["profitability risk",
         "拆解 COGS 成本驅動因子（材料/人力/製造費用）",
         "毛利率 %（季度趨勢）、COGS per unit",
         "毛利率下降主因是材料成本、匯率還是訂單量？",
         "識別主要成本壓力，評估定價轉嫁可行性"],
        ["inventory risk",
         "計算庫存天數（DIO），識別高齡庫存與跌價風險",
         "DIO（目標 vs 實際）、高齡庫存佔比 %",
         "超過 90 天的庫存品項佔比是多少？",
         "建立庫存健康儀表板，設定跌價準備觸發規則"],
    ], [3.0*cm, 4.2*cm, 3.8*cm, 3.6*cm, 3.5*cm]),
    sp(6),
    p("驗證建議有效果的時間軸："),
    tbl([
        ["時間點", "驗證動作", "判斷標準"],
        ["執行前",  "記錄所有 KPI 的現況數字（DIO、DSO、毛利率等）", "建立 before 基準線"],
        ["第 1 週",  "確認優先矩陣前三項行動是否已分配負責人", "有人負責 = 行動已啟動"],
        ["第 30 天", "確認前三項行動是否已實際執行", "60% 以上完成 = 進度正常"],
        ["第 60 天", "比對 KPI 基準線，重新執行 KRI extraction", "高嚴重度 KRI 應減少或有說明"],
        ["第 90 天", "確認原本「僅在新聞出現」的 KRI 是否已在年報或管理層報告揭露", "認知差距縮小 = 建議有效"],
    ], [2.0*cm, 8.5*cm, 5.9*cm]),
    PageBreak(),
]

story += [
    h1("第八段：面試官常問——口語版回答"),
    hr(),
    cap("把這些問答念熟，不是背稿，是讓回答自然流出來。"),
    sp(),

    q("介紹一下你自己 / 你的專案？"),
    a("我在成功大學資管系就讀，有 Python 和資料分析的背景。"
      "我做了一個叫 Industry Intelligence Agent 的工具，"
      "它可以把新聞和年報自動整理成 KRI 風險證據，產生中英雙語的顧問式報告。"
      "Demo 場景是台灣半導體和 AI server，以台積電為主，用的是 2026 年的真實新聞。"),
    hr(),

    q("KRI 跟 KPI 有什麼差別？"),
    a("KPI 量現在——台積電今年第一季營收年增 45.2%。"
      "KRI 是提前預警——台灣 LNG 只有 11 天庫存是 supply chain risk 的訊號，"
      "在財務數字出問題之前就已經在發出警告。"
      "我的系統萃取 KRI，讓顧問在問題變成損失之前就有證據可以追問。"),
    hr(),

    q("這個工具準確度怎麼樣？"),
    a("我用 rule-based keyword matching，透明、可解釋、不是黑盒子。"
      "Demo 裡 8 筆 KRI 全部手動對照過真實新聞來源，確認語境正確。"
      "如果要在 production 提升 recall，下一步是加一層 LLM classifier"
      "來處理語意比較模糊的句子。"),
    hr(),

    q("為什麼選 Streamlit 不選 Power BI？"),
    a("Streamlit 讓我把 Python 分析和 UI 直接接在一起，不需要中間的 export 步驟。"
      "如果要交付給客戶端的 business user，Power BI 更合適——"
      "我已經準備好 dashboard-ready CSV，可以直接 import 進去。"),
    hr(),

    q("你在這個專案學到什麼？"),
    a("技術上學了 PDF 文字擷取、RSS 新聞收集和 Altair 圖表。"
      "更重要的是學到怎麼把分析輸出設計成顧問可以用的格式——"
      "分成來源事實、分析解讀、建議追問三層，跟顧問報告的結構是一致的。"),
    hr(),

    q("如果有更多時間，你會改善什麼？"),
    a("三件事。一是加 LLM classifier 提升 KRI 的 recall，處理語意模糊的句子。"
      "二是接 TWSE API 或 Bloomberg，讓 KRI 訊號能直接連結到實際的財務比率。"
      "三是做時間序列追蹤，看風險訊號在每一季報告中怎麼演變。"),
    hr(),

    q("這跟 Deloitte 的工作有什麼關係？"),
    a("Deloitte 的顧問在客戶訪談前需要做產業 research。"
      "這個工具自動化了 evidence 收集和風險分類的部分，"
      "讓顧問能把時間用在更高價值的事：驗證假設、設計解決方案、跟客戶建立關係。"
      "KRI Evidence Table 可以直接當成訪談前的假設清單使用。"),
    hr(),

    q("你怎麼確定這些建議真的對企業有幫助？"),
    a("這是一個很好的問題，因為它點出了分析工具最核心的限制。"
      "我的設計是這樣的——每一條建議都有三個要素：\n"
      "第一，一個可量化的衡量 KPI。例如 supply chain risk 的建議對應的 KPI 是供應商交期達成率，"
      "執行建議前先記錄現在的數字，作為 before 的基準。\n"
      "第二，一個可以向管理層驗證的問題。例如『目前有幾個零組件無替代來源？』"
      "如果管理層說已經有替代料源了，這個風險的優先順序就下降；"
      "如果說沒想過，那就是真正的 gap。\n"
      "第三，一個 30/60 天的 review 機制。60 天後重新執行 KRI extraction，"
      "看高嚴重度項目有沒有減少，或者原本只在新聞裡出現的風險有沒有被管理層揭露。\n"
      "這讓建議從『感覺有用』變成『可以被驗證有用』。"),
    PageBreak(),
]

# ── 8. 速記卡 ─────────────────────────────────────────────────────────────────
story += [
    h1("最後一頁：面試當天進場前默念"),
    hr(),
    cap("面試前 5 分鐘把這張卡掃一眼，確保數字能自然說出來。"),
    sp(),
    tbl([
        ["記這個",       "說出來的樣子"],
        ["+45.2%",      "台積電今年三月營收年增四十五點二個百分點"],
        ["97% 能源",    "台灣百分之九十七的能源靠進口"],
        ["11 天",       "LNG 庫存只剩十一天，這是高嚴重度的 supply chain risk KRI"],
        ["50% 關稅",    "美國對中國半導體課百分之五十的關稅，2026 年元月起生效"],
        ["15%",         "台灣享有不超過百分之十五的美國優惠關稅"],
        ["+30% 成本",   "Arizona 廠比台灣廠建置成本貴百分之三十"],
        ["4 High KRI",  "本次分析有四筆高嚴重度 KRI，supply chain、geopolitical、customer concentration、ESG"],
        ["12 類別",     "系統有十二個 KRI 類別，每類五到八個關鍵字"],
        ["5 維度",      "商業影響分五組：營收、成本、供應鏈、法規地緣、客戶需求"],
        ["3 要素",      "每條建議必有：衡量 KPI + 管理層驗證問題 + 30/60 天 review 機制"],
        ["30/60 天",    "30 天確認行動啟動；60 天比對 KPI 基準線；重新執行 KRI extraction"],
    ], [3.5*cm, 12.9*cm]),
    sp(10),
    script(
        "面試結束前可以說這句：\n\n"
        "「這個專案讓我理解到，資料分析的價值不只是技術本身，"
        "而是怎麼把輸出設計成讓 business stakeholder 能直接行動的格式。"
        "我希望在 Deloitte 能把這個思維用在實際的客戶專案上。」"
    ),
]

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm,   bottomMargin=2*cm,
)
doc.build(story)
print(f"Written: {OUT}")
print(f"Size:    {OUT.stat().st_size:,} bytes")
