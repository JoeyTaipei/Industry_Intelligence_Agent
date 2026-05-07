"""Generate a read-aloud interview script PDF in Traditional Chinese.

Intended use: print or read on screen before the Deloitte interview.
Written as spoken language, not formal text.
"""

from __future__ import annotations

import pathlib

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = PROJECT_ROOT / "data" / "report" / "interview_spoken_script.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

CJK = "MSung-Light"
pdfmetrics.registerFont(UnicodeCIDFont(CJK))

W = A4[0] - 4 * cm
styles = getSampleStyleSheet()


def s(base: str, **kw) -> ParagraphStyle:
    defaults = {"fontName": CJK, "wordWrap": "CJK", "alignment": TA_LEFT}
    defaults.update(kw)
    return ParagraphStyle(f"{base}_sp_{id(kw)}", parent=styles[base], **defaults)


COVER_TITLE = s("Title",   fontSize=26, leading=34, textColor=colors.HexColor("#17324d"),
                spaceAfter=8, alignment=TA_CENTER)
COVER_SUB   = s("Normal",  fontSize=13, leading=20, textColor=colors.HexColor("#2e6da4"),
                spaceAfter=6, alignment=TA_CENTER)
COVER_NOTE  = s("Normal",  fontSize=9,  leading=13, textColor=colors.HexColor("#888888"),
                spaceAfter=4, alignment=TA_CENTER)

H1  = s("Heading1", fontSize=14, leading=20, textColor=colors.HexColor("#17324d"),
         spaceBefore=10, spaceAfter=5)
H2  = s("Heading2", fontSize=11, leading=16, textColor=colors.HexColor("#2e6da4"),
         spaceBefore=7,  spaceAfter=4)

BODY   = s("Normal",  fontSize=9.5,  leading=15,  spaceAfter=5)
SCRIPT = s("Normal",  fontSize=10.5, leading=17,  spaceAfter=7,
           leftIndent=10, borderColor=colors.HexColor("#2e6da4"),
           borderWidth=2, borderPadding=8,
           backColor=colors.HexColor("#f0f6ff"))
Q_STYLE = s("Normal", fontSize=10, leading=15, textColor=colors.HexColor("#c0392b"),
             spaceBefore=8, spaceAfter=2, fontName=CJK)
A_STYLE = s("Normal", fontSize=10, leading=15, spaceAfter=8,
             leftIndent=12, fontName=CJK)
NUM     = s("Normal",  fontSize=10, leading=16,  leftIndent=14,
            firstLineIndent=-10, spaceAfter=4)
CAPTION = s("Normal",  fontSize=8,  leading=11,
            textColor=colors.HexColor("#777777"), spaceAfter=3)
WARN    = s("Normal",  fontSize=9,  leading=13,
            textColor=colors.HexColor("#a04000"), spaceAfter=4,
            backColor=colors.HexColor("#fff8f0"), borderPadding=6)


def p(t: str) -> Paragraph: return Paragraph(t, BODY)
def script(t: str) -> Paragraph: return Paragraph(t, SCRIPT)
def h1(t: str) -> Paragraph: return Paragraph(t, H1)
def h2(t: str) -> Paragraph: return Paragraph(t, H2)
def num(t: str) -> Paragraph: return Paragraph(t, NUM)
def cap(t: str) -> Paragraph: return Paragraph(t, CAPTION)
def warn(t: str) -> Paragraph: return Paragraph(t, WARN)
def q(t: str) -> Paragraph: return Paragraph(f"❓ 面試官：{t}", Q_STYLE)
def a(t: str) -> Paragraph: return Paragraph(f"你說：{t}", A_STYLE)
def sp(n: int = 8) -> Spacer: return Spacer(1, n)
def hr() -> HRFlowable:
    return HRFlowable(width=W, thickness=0.5,
                      color=colors.HexColor("#c9d3df"), spaceBefore=5, spaceAfter=7)


def tbl(rows, widths, hbg="#17324d"):
    cells = []
    for i, row in enumerate(rows):
        st = ParagraphStyle(f"tc{i}", parent=styles["Normal"], fontName=CJK,
                            wordWrap="CJK", fontSize=8.5, leading=12,
                            textColor=colors.white if i == 0 else colors.black)
        cells.append([Paragraph(c, st) for c in row])
    t = Table(cells, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(hbg)),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d3df")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    return t


story = []

# ── COVER ────────────────────────────────────────────────────────────────────
story += [
    sp(50),
    Paragraph("面試前大聲念", COVER_TITLE),
    Paragraph("Industry Intelligence Agent 口語腳本", COVER_SUB),
    sp(6),
    Paragraph("Deloitte Digital Technology Intern  ·  Joey Wu  ·  2026", COVER_NOTE),
    sp(10),
    Paragraph("怎麼用這份文件", s("Heading2", fontSize=11, alignment=TA_CENTER,
                                   textColor=colors.HexColor("#555555"))),
    sp(4),
    Paragraph(
        "每一段灰藍色框框就是你要念出來的內容。旁邊的小字是給你的提示，不用念出來。"
        "面試前一天把整份念一遍，面試當天再把數字那一頁默念一次就夠了。",
        s("Normal", fontSize=10, alignment=TA_CENTER, leading=16,
          textColor=colors.HexColor("#444444"))
    ),
    PageBreak(),
]

# ── SECTION 1: 開場白 ─────────────────────────────────────────────────────────
story += [
    h1("第一段：開場白（念 30 秒）"),
    hr(),
    cap("當面試官說「介紹一下你的專案」或「tell me about yourself」時念這段。"),
    sp(),
    script(
        "我做的這個專案叫 Industry Intelligence Agent，是一個用 Python 和 Streamlit 建立的產業情報分析工具。"
        "它的核心功能是把公司新聞、年報文字、和產業趨勢自動整理成 KRI 風險證據清單，"
        "然後產生一份中英雙語的顧問式報告和互動儀表板。"
        "Demo 場景是台灣半導體和 AI server 產業，以台積電為主，用的是 2026 年的真實新聞數據。"
    ),
    sp(4),
    warn("記住：說完這句之後停頓一下，讓面試官接話。不要急著繼續講。"),
    PageBreak(),
]

# ── SECTION 2: 解決什麼問題 ───────────────────────────────────────────────────
story += [
    h1("第二段：解決什麼問題（念 1 分鐘）"),
    hr(),
    cap("當面試官問「為什麼做這個？」或「這個工具的價值是什麼？」時念這段。"),
    sp(),
    script(
        "顧問在客戶訪談前，需要快速回答三個問題：一，這家公司最近有什麼市場訊號？"
        "二，年報裡管理層自己說了哪些風險？三，哪些風險需要優先追問？"
        "\n\n"
        "以前這些工作要手動搜尋新聞、讀年報、整理筆記，可能要花半天到一天。"
        "我的工具把這個流程自動化——輸入公司名稱、上傳 PDF、按一個按鈕，"
        "五分鐘內就能拿到結構化的 KRI 風險證據清單和報告。"
        "\n\n"
        "重點不是取代顧問的判斷，而是讓顧問更快拿到第一輪 evidence，"
        "把時間省下來做更高價值的事——跟客戶訪談、設計解決方案、build business case。"
    ),
    PageBreak(),
]

# ── SECTION 3: KRI 怎麼做 ─────────────────────────────────────────────────────
story += [
    h1("第三段：技術方法——KRI 怎麼抽（念 1 分鐘）"),
    hr(),
    cap("當面試官問「技術上怎麼做的？」或「KRI 是什麼？」時念這段。"),
    sp(),
    script(
        "KRI 是 Key Risk Indicator，關鍵風險指標。它跟 KPI 不一樣——"
        "KPI 衡量現在的表現，KRI 是提前預警的訊號。"
        "\n\n"
        "舉例來說，台積電今年第一季營收年增百分之四十五點二，這是 KPI。"
        "但是台灣進口百分之九十七的能源、LNG 只有十一天的庫存，"
        "這是 supply chain risk 的 KRI 訊號——它在財務數字出問題之前就已經在發出警告了。"
        "\n\n"
        "我的系統有十二個 KRI 類別，每個類別有五到八個關鍵字。"
        "程式掃過新聞和年報的每一句話，只要包含關鍵字，就把那句話抽出來當作 evidence。"
        "然後再根據句子裡有沒有出現像 significant、material、severe 這些字，"
        "判斷嚴重度是高、中、還是低。"
    ),
    sp(6),
    p("12 個 KRI 類別："),
    tbl([
        ["類別", "核心關鍵字（舉例）", "Demo 發現"],
        ["supply chain risk",           "shortage, logistics, delivery delay",    "荷姆茲海峽封閉、氦氣翻倍"],
        ["geopolitical risk",           "tariff, export controls, cross-strait",  "中國晶片 50% 關稅"],
        ["customer concentration risk", "major customer, top 5 customers",        "TSMC 通知 NVIDIA、Broadcom 產能受限"],
        ["ESG / sustainability risk",   "energy usage, carbon, emissions",        "台灣 97% 能源進口、11 天 LNG"],
        ["regulatory risk",             "regulation, compliance, sanction",       "稀土出口管制（鎵、鍺、石墨）"],
        ["profitability risk",          "gross margin, pricing pressure",          "Arizona 廠比台灣貴 30%"],
        ["inventory risk",              "inventory, obsolete, stock level",       "關稅不確定影響訂單時序"],
        ["cash flow risk",              "cash flow, capex, free cash flow",       "美國廠投資義務"],
        ["liquidity risk",              "liquidity, working capital",             "訂單波動造成 WC 壓力"],
        ["receivables risk",            "accounts receivable, bad debt",          "大客戶付款條件差異"],
        ["cyber / digital risk",        "cyber, data breach, OT",                "智慧工廠 OT/IT 整合"],
        ["leverage risk",               "debt, borrowings, covenant",             "大規模資本支出融資"],
    ], [3.8*cm, 5*cm, 7.6*cm]),
    PageBreak(),
]

# ── SECTION 4: 真實數字 ───────────────────────────────────────────────────────
story += [
    h1("第四段：面試必背數字（可以直接引用）"),
    hr(),
    cap("這些數字在面試中說出來，立刻讓回答有說服力。來源都是 2026 年真實新聞。"),
    sp(),
    tbl([
        ["數字", "事實", "來源"],
        ["+45.2%",   "台積電 2026 年 3 月營收年增",             "HeyGoTrade, 2026-04"],
        ["415.2B NTD","台積電 2026 年 3 月月營收",              "HeyGoTrade, 2026-04"],
        ["+28%",     "台積電股利增加幅度",                       "247 Wall St, 2026-02"],
        [">65%",     "台積電全球先進製程市占率",                 "Yahoo Finance, 2026-04"],
        ["97%",      "台灣能源進口依存度",                       "Yahoo Finance, 2026-04"],
        ["11 天",    "台灣 LNG 庫存（無進口情況下）",            "Yahoo Finance, 2026-04"],
        ["50%",      "美國對中國半導體進口關稅（2026-01 起）",   "Tom's Hardware, 2026-04"],
        ["≤15%",     "台灣享有的美國優惠關稅上限",               "CNBC, 2026-01"],
        ["USD 250B", "台灣承諾在美投資金額",                     "CNBC, 2026-01"],
        ["+30%",     "TSMC Arizona 廠比台灣廠貴多少",            "247 Wall St, 2026-02"],
        ["USD 465B", "TSMC Arizona 總投資目標（11 座廠）",        "abhs.in, 2026-04"],
        ["2027-06",  "美國對中國晶片新關稅生效日",               "Tom's Hardware, 2026-04"],
        ["30%",      "美中貨物總關稅（暫停至 2026-11）",          "Tax Foundation, 2026-05"],
        ["2x",       "氦氣價格漲幅（卡達供應中斷後）",           "HeyGoTrade, 2026-04"],
    ], [2.2*cm, 8.8*cm, 5.4*cm]),
    sp(6),
    script(
        "念法範例：「我的 demo 用的全是真實數據。台積電今年三月營收年增百分之四十五點二，"
        "但同時台灣有兩個高嚴重度的 KRI——能源進口依存度百分之九十七，"
        "還有荷姆茲海峽封閉後 LNG 只剩十一天的庫存。"
        "這說明強勁的財務表現背後，有很具體的供應鏈脆弱性需要追問。」"
    ),
    PageBreak(),
]

# ── SECTION 5: 商業影響 ───────────────────────────────────────────────────────
story += [
    h1("第五段：商業影響——連結到收入和成本（念 1 分鐘）"),
    hr(),
    cap("當面試官問「這些風險對業務有什麼影響？」或「你怎麼把分析變成 insight？」時念這段。"),
    sp(),
    script(
        "KRI evidence 抽出來之後，我做了一個商業影響分析，把所有風險分成五個維度："
        "\n\n"
        "第一，營收影響。客戶集中度高，單一客戶訂單異動會直接衝擊營收穩定性。"
        "需要確認前五大客戶的佔比，以及訂單取消或延遲的條款。"
        "\n\n"
        "第二，成本影響。關稅、法規合規、Arizona 廠的建置成本，"
        "都可能提高 COGS、壓縮毛利率。要追蹤公司有沒有辦法把成本轉嫁給客戶。"
        "\n\n"
        "第三，供應鏈和營運影響。供應鏈中斷可能造成交期延誤、庫存不足。"
        "需要評估替代料源，以及安全庫存的水位夠不夠。"
        "\n\n"
        "第四，法規地緣政治影響。出口管制、稀土限制，會增加合規成本和市場准入風險。"
        "\n\n"
        "第五，客戶需求影響。需求預測不準確或大客戶突然改訂單，會放大整個收入的波動。"
        "\n\n"
        "每個維度都對應到可以量化追蹤的 KPI：庫存天數、應收帳款天數、毛利率、現金轉換週期。"
    ),
    PageBreak(),
]

# ── SECTION 6: 建議下一步 ────────────────────────────────────────────────────
story += [
    h1("第六段：建議下一步——展示顧問思維（念 1 分鐘）"),
    hr(),
    cap("這段最能展示顧問思維。面試官問「如果你是顧問你會怎麼做？」時念這段。"),
    sp(),
    script(
        "我整理了五組建議：\n\n"
        "第一組，立即檢查。確認 revenue by region、供應商集中度、gross margin 的趨勢。"
        "這三個是最快能判斷風險嚴不嚴重的數據切入點。"
        "\n\n"
        "第二組，數據分析。追蹤庫存天數 DIO、應收帳款天數 DSO、現金轉換週期 CCC，"
        "同時做關稅情境的敏感度分析——如果關稅再漲百分之十，毛利率影響是多少。"
        "\n\n"
        "第三組，Dashboard 監控。建立一個 KRI severity dashboard，"
        "高嚴重度的項目用紅色警示、每週更新，讓管理層可以即時看到風險訊號的變化。"
        "\n\n"
        "第四組，管理層決策議題。問三個問題："
        "哪些風險已經有對策了？資本支出和供應鏈多元化的優先順序是什麼？"
        "目前哪些 KPI 已經在月度 review 中追蹤？"
        "\n\n"
        "第五組，人工覆核。優先覆核這次分析裡四筆高嚴重度的 KRI evidence，"
        "回到原始新聞 URL 和年報段落，確認語境正確、沒有斷章取義。"
    ),
    PageBreak(),
]

# ── SECTION 7: 面試官 Q&A ─────────────────────────────────────────────────────
story += [
    h1("第七段：面試官常問——口語版回答"),
    hr(),
    cap("把這些問答念熟，不是背稿，是讓回答自然流出來。"),
    sp(),

    q("介紹一下你自己／你的專案？"),
    a("我在 NCKU 資管系就讀，有 Python 和資料分析的背景。"
      "我做了一個叫 Industry Intelligence Agent 的工具，"
      "它可以把新聞和年報自動整理成 KRI 風險證據，產生中英雙語的顧問式報告。"
      "Demo 場景是台灣半導體和 AI server，以台積電為主，用的是 2026 年的真實新聞。"),
    hr(),

    q("KRI 跟 KPI 有什麼差別？"),
    a("KPI 量現在——台積電今年第一季營收年增 45.2%。"
      "KRI 是提前預警——台灣 LNG 只有 11 天庫存是 supply chain risk 的訊號，"
      "在財務數字出問題之前就已經發出警告。"
      "我的系統萃取 KRI，讓顧問在問題變成損失之前就有證據可以追問。"),
    hr(),

    q("這個工具準確度怎麼樣？"),
    a("我用 rule-based keyword matching，透明、可解釋、不是黑盒子。"
      "Demo 裡 8 筆 KRI 全部手動對照過真實新聞來源，確認語境正確。"
      "如果要在 production 提升 recall，下一步是加一層 LLM classifier"
      "來處理語意比較模糊的句子。"),
    hr(),

    q("為什麼選 Streamlit 不選 Power BI？"),
    a("Streamlit 讓我把 Python 分析和 UI 直接接在一起，不需要中間的 export 步驟，"
      "開發和 demo 速度快很多。"
      "如果要交付給客戶端的 business user，Power BI 更合適——"
      "我已經準備好 dashboard-ready CSV，可以直接 import 進去。"),
    hr(),

    q("你在這個專案學到什麼？"),
    a("技術上學了 PDF 文字擷取、RSS 新聞收集、Altair 圖表和 reportlab PDF 生成。"
      "更重要的是學到怎麼把分析輸出設計成顧問可以用的格式——"
      "每一個輸出都分成「來源事實」、「分析解讀」、「建議追問」三層，"
      "這跟顧問報告的結構是一致的，也防止過度解讀資料。"),
    hr(),

    q("如果有更多時間，你會改善什麼？"),
    a("三件事。第一，加 LLM classifier 提升 KRI 的 recall，"
      "處理語意模糊的句子。"
      "第二，接 TWSE API 或 Bloomberg，把 KRI 訊號連結到實際的財務比率，"
      "讓「庫存天數」、「毛利率」這些數字能直接比對。"
      "第三，做時間序列追蹤，看風險訊號在每一季的報告中怎麼演變。"),
    hr(),

    q("這跟 Deloitte 的工作有什麼關係？"),
    a("Deloitte 的顧問在客戶訪談前需要做產業 research。"
      "這個工具自動化了 evidence 收集和風險分類的部分，"
      "讓顧問能把時間用在更高價值的事：驗證假設、設計解決方案、跟客戶建立關係。"
      "KRI Evidence Table 可以直接當成訪談前的假設清單使用。"),
    PageBreak(),
]

# ── SECTION 8: 數字速記卡 ─────────────────────────────────────────────────────
story += [
    h1("最後一頁：面試當天默念這張卡"),
    hr(),
    cap("面試前 5 分鐘，把這些數字掃一眼，確保能自然說出來。"),
    sp(),
    tbl([
        ["記這個", "說出來的樣子"],
        ["+45.2%",   "台積電今年三月營收年增四十五點二個百分點"],
        ["97% 能源", "台灣百分之九十七的能源靠進口"],
        ["11 天",    "LNG 庫存只剩十一天，這是 supply chain risk 的高嚴重度 KRI"],
        ["50% 關稅", "美國對中國半導體課百分之五十的關稅"],
        ["≤15%",     "台灣享有不超過百分之十五的優惠關稅"],
        ["+30% 成本","Arizona 廠比台灣廠貴百分之三十"],
        ["4 High",   "本次分析有四筆高嚴重度 KRI，優先覆核"],
        ["12 類別",  "系統有十二個 KRI 類別，每類五到八個關鍵字"],
    ], [3.5*cm, 12.9*cm]),
    sp(10),
    script(
        "最後一句話，面試結束前可以說：\n\n"
        "「這個專案讓我理解到，資料分析的價值不只是技術本身，"
        "而是怎麼把輸出設計成讓 business stakeholder 能直接行動的格式。"
        "我希望在 Deloitte 能把這個思維用在實際的客戶專案上。」"
    ),
]

# ── BUILD ─────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)
doc.build(story)
print(f"Written: {OUT}")
print(f"Size:    {OUT.stat().st_size:,} bytes")
