"""面試前大聲念 v2 — 口語腳本，內容緊湊連續版。

Uses Microsoft JhengHei (msjh.ttc) for Traditional Chinese on Windows.
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

# ── Fonts ─────────────────────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont("ZH",  "C:/Windows/Fonts/msjh.ttc",   subfontIndex=0))
pdfmetrics.registerFont(TTFont("ZHB", "C:/Windows/Fonts/msjhbd.ttc", subfontIndex=0))

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "report" / "interview_spoken_script.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

W = A4[0] - 3.6 * cm
base = getSampleStyleSheet()

def _s(tag, font="ZH", size=9.8, lead=15, color=colors.black,
       align=TA_LEFT, sb=2, sa=3, li=0, bg=None, bc=None, bw=0, bp=0):
    kw = dict(fontName=font, fontSize=size, leading=lead, textColor=color,
              alignment=align, spaceBefore=sb, spaceAfter=sa, leftIndent=li)
    if bg: kw["backColor"] = bg
    if bc: kw.update(borderColor=bc, borderWidth=bw, borderPadding=bp)
    return ParagraphStyle(tag, parent=base["Normal"], **kw)

# Styles — tight spacing throughout
CT  = _s("ct",  "ZHB", 22, 28, colors.HexColor("#17324d"), TA_CENTER, sb=0, sa=4)
CS  = _s("cs",  "ZH",  12, 18, colors.HexColor("#2e6da4"), TA_CENTER, sb=0, sa=3)
CN  = _s("cn",  "ZH",   8, 12, colors.HexColor("#999999"), TA_CENTER, sb=0, sa=2)

H1  = _s("h1",  "ZHB", 12, 18, colors.HexColor("#17324d"), sb=8, sa=2)
CAP = _s("cap", "ZH",   7.5, 11, colors.HexColor("#888888"), sb=0, sa=2)
BOD = _s("bod", "ZH",   9.5, 14, sb=0, sa=2)

# Blue script box — the words to say out loud
SCR = _s("scr", "ZH", 10, 16, sb=2, sa=4, li=0,
         bg=colors.HexColor("#eef4ff"),
         bc=colors.HexColor("#3a7bd5"), bw=2, bp=8)

WARN = _s("wrn", "ZH", 8.5, 13, colors.HexColor("#a04000"),
          sb=1, sa=3, bg=colors.HexColor("#fff8f0"),
          bc=colors.HexColor("#e0a060"), bw=1, bp=5)

Q_S = _s("q", "ZHB", 9.8, 14, colors.HexColor("#c0392b"), sb=7, sa=1)
A_S = _s("a", "ZH",  9.8, 14, sb=0, sa=5, li=10)

TH  = _s("th", "ZHB", 7.8, 11, colors.white, sb=0, sa=0)
TD  = _s("td", "ZH",  7.8, 11, sb=0, sa=0)


def s(t):    return Spacer(1, t)
def p(t):    return Paragraph(t, BOD)
def scr(t):  return Paragraph(t, SCR)
def h1(t):   return Paragraph(t, H1)
def cap(t):  return Paragraph(t, CAP)
def warn(t): return Paragraph(t, WARN)
def q(t):    return Paragraph(f"❓ {t}", Q_S)
def a(t):    return Paragraph(f"→ {t}", A_S)

def div():
    return HRFlowable(width=W, thickness=0.4,
                      color=colors.HexColor("#d0dae8"), spaceBefore=6, spaceAfter=3)

def tbl(rows, widths, hbg="#17324d"):
    cells = [[Paragraph(c, TH if i == 0 else TD) for c in row]
             for i, row in enumerate(rows)]
    t = Table(cells, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0),  colors.HexColor(hbg)),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f4f7fb")]),
        ("GRID",           (0,0), (-1,-1), 0.25, colors.HexColor("#c9d3df")),
        ("VALIGN",         (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",     (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 3),
        ("LEFTPADDING",    (0,0), (-1,-1), 5),
        ("RIGHTPADDING",   (0,0), (-1,-1), 5),
    ]))
    return t


story = []

# ── 封面（單頁）────────────────────────────────────────────────────────────────
story += [
    s(36),
    Paragraph("面試前大聲念 v2", CT),
    Paragraph("Industry Intelligence Agent 口語腳本", CS),
    s(4),
    Paragraph("Deloitte Digital Technology Intern · Joey Wu · 2026", CN),
    s(10),
    Paragraph(
        "藍色框框 = 你要念的話。小灰字 = 提示，不用念。\n"
        "面試前一天整份念一遍，當天進場前只看最後一頁速記卡。",
        _s("cb", "ZH", 9.5, 15, colors.HexColor("#444444"), TA_CENTER, sb=0, sa=0)
    ),
    PageBreak(),
]

# ── 1. 開場白 ──────────────────────────────────────────────────────────────────
story += [
    h1("1  開場白（30 秒）"),
    cap("面試官說「介紹你的專案」或「tell me about yourself」時用這段。"),
    scr(
        "我做的這個專案叫 Industry Intelligence Agent，是一個用 Python 和 Streamlit 建的產業情報分析工具。"
        "核心功能是把新聞、年報文字、產業趨勢自動整理成 KRI 風險證據清單，"
        "然後產生一份中英雙語的顧問式報告和互動儀表板。"
        "Demo 場景是台灣半導體和 AI server 產業，以台積電為主，用的是 2026 年的真實新聞。"
    ),
    warn("說完就停，讓面試官接話，不要急著繼續。"),
    div(),
]

# ── 2. 解決什麼問題 ────────────────────────────────────────────────────────────
story += [
    h1("2  解決什麼問題（1 分鐘）"),
    cap("面試官問「為什麼做這個？」或「這工具的價值是什麼？」時用這段。"),
    scr(
        "顧問在客戶訪談前要快速回答三個問題：這家公司最近有什麼市場訊號？"
        "年報裡管理層自己說了哪些風險？哪些風險要優先追問？\n\n"
        "以前這些工作要手動搜新聞、讀年報、整理筆記，可能花半天到一天。"
        "我的工具把這個流程自動化——輸入公司名稱、上傳 PDF、按一個按鈕，"
        "五分鐘內就能拿到結構化的 KRI 風險證據和報告。\n\n"
        "重點不是取代顧問的判斷，而是讓顧問更快拿到第一輪 evidence，"
        "省下來的時間用在跟客戶訪談、設計解決方案、建立 business case。"
    ),
    div(),
]

# ── 3. KRI 怎麼做 ──────────────────────────────────────────────────────────────
story += [
    h1("3  技術方法：KRI 怎麼抽（1 分鐘）"),
    cap("面試官問「技術上怎麼做的？」或「KRI 是什麼？」時用這段。"),
    scr(
        "KRI 是 Key Risk Indicator，關鍵風險指標。它跟 KPI 不一樣——"
        "KPI 量現在的表現，KRI 是提前預警的訊號。\n\n"
        "舉例：台積電今年第一季營收年增 45.2%，這是 KPI。"
        "但是台灣進口 97% 的能源、LNG 只剩 11 天庫存，"
        "這是 supply chain risk 的 KRI 訊號——在財務數字出問題之前就在發出警告了。\n\n"
        "我的系統有 12 個 KRI 類別，每類有五到八個關鍵字。"
        "程式掃過新聞和年報每一句話，包含關鍵字就抽出來當 evidence。"
        "再根據有沒有出現 significant、material、severe 這些字，"
        "判斷嚴重度高中低，分數 3、2、1。"
    ),
    s(3),
    tbl([
        ["KRI 類別", "關鍵字舉例", "Demo 發現"],
        ["supply chain risk",           "shortage, delivery delay",        "荷姆茲海峽封閉、氦氣翻倍"],
        ["geopolitical risk",           "tariff, export controls",         "中國晶片 50% 關稅"],
        ["customer concentration risk", "major customer, top 5 customers", "NVIDIA/Broadcom 產能受限"],
        ["ESG / sustainability risk",   "energy usage, carbon",            "97% 能源進口、11 天 LNG"],
        ["regulatory risk",             "regulation, sanction",            "稀土出口管制（鎵、鍺）"],
        ["profitability risk",          "gross margin, pricing pressure",  "Arizona 廠比台灣貴 30%"],
        ["inventory risk",              "inventory, stock level",          "關稅不確定影響訂單時序"],
        ["cash flow / liquidity risk",  "capex, working capital",          "美國廠大規模投資義務"],
        ["receivables risk",            "accounts receivable, bad debt",   "大客戶付款條件差異"],
        ["cyber / digital risk",        "cyber, OT, data breach",          "智慧工廠 OT/IT 整合"],
        ["leverage risk",               "debt, borrowings, covenant",      "大規模資本支出融資"],
    ], [3.8*cm, 4.8*cm, 7.8*cm]),
    div(),
]

# ── 4. 真實數字 ────────────────────────────────────────────────────────────────
story += [
    h1("4  面試必背數字（直接引用）"),
    cap("說這些數字加上來源，回答立刻有說服力。"),
    tbl([
        ["數字", "事實", "來源"],
        ["+45.2%",   "台積電 2026/3 月營收年增",             "HeyGoTrade"],
        ["415B NTD", "台積電 3 月月營收",                    "HeyGoTrade"],
        [">65%",     "台積電全球先進製程市占率",              "Yahoo Finance"],
        ["97%",      "台灣能源進口依存度",                    "Yahoo Finance"],
        ["11 天",    "台灣 LNG 庫存（無進口）",               "Yahoo Finance"],
        ["50%",      "美對中國半導體關稅（2026/1 起）",       "Tom's Hardware"],
        ["≤15%",     "台灣優惠關稅上限（US-Taiwan 協議）",    "CNBC"],
        ["USD 250B", "台灣承諾在美投資",                      "CNBC"],
        ["+30%",     "Arizona 廠比台灣廠建置成本貴多少",       "247 Wall St"],
        ["+28%",     "台積電股利增幅",                        "247 Wall St"],
        ["2x",       "氦氣漲幅（卡達供應中斷後）",            "HeyGoTrade"],
        ["Jun 2027", "美對中國晶片新關稅生效",                "Tom's Hardware"],
    ], [2.2*cm, 8.4*cm, 5.8*cm]),
    s(3),
    scr(
        "引用範例：「我的 demo 全是真實數據。台積電三月營收年增 45.2%，"
        "但同時台灣有兩個高嚴重度 KRI——能源 97% 靠進口、LNG 只剩 11 天庫存。"
        "這說明強勁財務表現背後有很具體的供應鏈脆弱性需要追問。」"
    ),
    div(),
]

# ── 5. 商業影響 ────────────────────────────────────────────────────────────────
story += [
    h1("5  商業影響：連結收入和成本（1 分鐘）"),
    cap("面試官問「這些風險對業務有什麼影響？」或「分析怎麼變成 insight？」時用這段。"),
    scr(
        "KRI evidence 抽出來之後，我把所有風險分成五個商業影響維度。\n\n"
        "第一，營收影響。客戶集中度高，單一客戶訂單異動直接衝擊營收穩定性，"
        "要確認前五大客戶佔比和訂單取消條款。\n\n"
        "第二，成本影響。關稅、法規合規、Arizona 廠建置成本都可能拉高 COGS、壓縮毛利率，"
        "要追蹤公司有沒有辦法把成本轉嫁給客戶。\n\n"
        "第三，供應鏈和營運影響。供應鏈中斷可能造成交期延誤、庫存不足，"
        "要評估替代料源和安全庫存水位。\n\n"
        "第四，法規地緣政治影響。出口管制和稀土限制增加合規成本和市場准入風險。\n\n"
        "第五，客戶需求影響。大客戶突然改訂單、需求預測不準，放大收入波動。\n\n"
        "每個維度對應可量化的 KPI：庫存天數 DIO、應收帳款天數 DSO、毛利率、現金轉換週期 CCC。"
    ),
    div(),
]

# ── 6. 建議下一步 ──────────────────────────────────────────────────────────────
story += [
    h1("6  建議下一步：展示顧問思維（1 分鐘）"),
    cap("面試官問「如果你是顧問你會怎麼做？」時用這段。"),
    scr(
        "我整理了五組建議，這最能展示顧問思維。\n\n"
        "第一，立即檢查（本週）。確認 revenue by region、供應商集中度、gross margin 趨勢，"
        "這三個是最快判斷風險嚴不嚴重的切入點。\n\n"
        "第二，數據分析（本月）。追蹤庫存天數 DIO、應收帳款天數 DSO、現金轉換週期 CCC，"
        "加上關稅情境敏感度分析——關稅再漲一成毛利率影響多少。\n\n"
        "第三，Dashboard 監控。建立 KRI severity dashboard，高嚴重度項目紅色警示每週更新。\n\n"
        "第四，管理層決策議題。問三個問題：哪些風險已有對策？"
        "資本支出和供應鏈多元化的優先順序？哪些 KPI 在月度 review 中追蹤？\n\n"
        "第五，人工覆核。優先覆核四筆高嚴重度 KRI evidence，"
        "回到原始新聞 URL 和年報段落，確認語境正確、沒有斷章取義。"
    ),
    div(),
]

# ── 7. 建議如何確認有效 ────────────────────────────────────────────────────────
story += [
    h1("7  建議如何確認對企業有效（1 分鐘）"),
    cap("「你怎麼知道建議真的有用？」——這是最難的問題，也是最能拉開差距的回答。"),
    scr(
        "每一條建議設計了三個要素，讓它從『感覺有用』變成『可以被驗證有用』。\n\n"
        "第一，一個可量化的衡量 KPI。"
        "例如 supply chain risk 的建議對應 KPI 是供應商交期達成率和 single-source 零組件數量，"
        "執行前先記下現況數字，作為 before 的基準。\n\n"
        "第二，一個可向管理層驗證的問題。"
        "例如『目前有幾個零組件無替代來源？』管理層說有了，這個風險優先順序下降；"
        "說沒想過，那就是真正的 gap。\n\n"
        "第三，30/60 天 review。30 天確認前三項行動是否已啟動；"
        "60 天比對 KPI 基準線是否移動，同時重新執行 KRI extraction 看高嚴重度有沒有減少。\n\n"
        "這就是為什麼我說這是 evidence-based prioritization，不是財務模型——"
        "建議的有效性要靠客戶資料和管理層確認，不是我的分析單獨決定。"
    ),
    s(3),
    tbl([
        ["時間點", "做什麼", "判斷標準"],
        ["執行前",  "記錄 DIO、DSO、毛利率等 KPI 現況",           "建立 before 基準"],
        ["第 1 週", "確認優先矩陣前三項是否已分配負責人",          "有人負責 = 啟動"],
        ["第 30 天","確認前三項行動是否實際執行",                  "60% 完成 = 進度正常"],
        ["第 60 天","比對 KPI 基準線 + 重跑 KRI extraction",       "高嚴重度應減少或有說明"],
        ["第 90 天","確認僅在新聞出現的 KRI 是否已被管理層揭露",   "認知差距縮小 = 有效"],
    ], [1.9*cm, 8.5*cm, 5.9*cm]),
    div(),
]

# ── 8. Q&A ────────────────────────────────────────────────────────────────────
story += [
    h1("8  面試官常問 Q&A"),
    cap("念熟不是背稿，讓回答自然流出來就好。"),

    q("介紹你自己 / 你的專案？"),
    a("我在成功大學資管系，有 Python 和資料分析的背景。"
      "我做了一個叫 Industry Intelligence Agent 的工具，"
      "可以把新聞和年報自動整理成 KRI 風險證據，產生中英雙語的顧問式報告。"
      "Demo 是台灣半導體 AI server，以台積電為主，用 2026 年真實新聞。"),

    q("KRI 跟 KPI 差在哪？"),
    a("KPI 量現在——台積電今年三月營收年增 45.2%。"
      "KRI 是提前預警——台灣 LNG 只剩 11 天庫存是 supply chain risk 的訊號，"
      "在財務數字出問題之前就在發警告。"
      "我的系統萃取 KRI，讓顧問在問題變成損失之前就有證據追問。"),

    q("準確度怎麼樣？"),
    a("rule-based keyword matching，透明可解釋、不是黑盒子。"
      "Demo 的 8 筆 KRI 全部手動對照過真實新聞來源。"
      "如果要在 production 提升 recall，下一步是加 LLM classifier 處理語意模糊的句子。"),

    q("為什麼用 Streamlit 不用 Power BI？"),
    a("Streamlit 讓 Python 分析和 UI 直接接在一起，不需要中間 export 步驟。"
      "如果要交付給客戶端 business user，Power BI 更合適——"
      "我已經準備好 dashboard-ready CSV，可以直接 import。"),

    q("你在這個專案學到什麼？"),
    a("技術上學了 PDF 文字擷取、RSS 新聞收集和 Altair 圖表。"
      "更重要的是學到怎麼把分析輸出設計成顧問可以用的格式——"
      "分成來源事實、分析解讀、建議追問三層，跟顧問報告結構一致。"),

    q("如果有更多時間，你會改善什麼？"),
    a("三件事：一，LLM classifier 提升 KRI recall；"
      "二，接 TWSE API 或 Bloomberg 讓 KRI 訊號連結實際財務比率；"
      "三，時間序列追蹤，看風險訊號在每季報告中怎麼演變。"),

    q("這跟 Deloitte 的工作有什麼關係？"),
    a("Deloitte 顧問在客戶訪談前需要做產業 research。"
      "這個工具自動化了 evidence 收集和風險分類，"
      "讓顧問把時間用在更高價值的事：驗證假設、設計解決方案、跟客戶建關係。"
      "KRI Evidence Table 可以直接當訪談前的假設清單。"),

    q("你怎麼確定建議真的對企業有幫助？"),
    a("每條建議有三個要素：一，可量化的衡量 KPI，先記下 before 基準；"
      "二，可向管理層驗證的問題，確認是已知風險還是真正的 gap；"
      "三，30/60 天 review，60 天後重跑 KRI extraction 看高嚴重度有沒有減少。"
      "這讓建議從感覺有用變成可以被驗證有用。"),

    div(),
]

# ── 速記卡（最後一頁）──────────────────────────────────────────────────────────
story += [
    h1("進場前默念這張卡"),
    cap("掃一眼，確保數字能自然說出來。"),
    tbl([
        ["記這個",      "說出來的樣子"],
        ["+45.2%",     "台積電三月營收年增四十五點二個百分點"],
        ["97% 能源",   "台灣百分之九十七的能源靠進口"],
        ["11 天",      "LNG 只剩十一天，高嚴重度 supply chain risk KRI"],
        ["50% 關稅",   "美國對中國半導體課五十個百分點，2026 年元月起生效"],
        ["≤15%",       "台灣享有不超過百分之十五的美國優惠關稅"],
        ["+30% 成本",  "Arizona 廠比台灣廠貴三十個百分點"],
        ["4 High KRI", "supply chain、geopolitical、customer concentration、ESG"],
        ["12 類別",    "十二個 KRI 類別，每類五到八個關鍵字"],
        ["5 維度",     "商業影響：營收、成本、供應鏈、法規地緣、客戶需求"],
        ["3 要素",     "每條建議：衡量 KPI + 管理層驗證問題 + 30/60 天 review"],
    ], [3.2*cm, 13.2*cm]),
    s(6),
    scr(
        "面試結束前說這句：\n"
        "「這個專案讓我理解到，資料分析的價值不只是技術本身，"
        "而是怎麼把輸出設計成讓 business stakeholder 能直接行動的格式。"
        "我希望在 Deloitte 能把這個思維用在實際的客戶專案上。」"
    ),
]

# ── Build ──────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=1.8*cm, leftMargin=1.8*cm,
    topMargin=1.6*cm,   bottomMargin=1.6*cm,
)
doc.build(story)
print(f"Written: {OUT}")
print(f"Size:    {OUT.stat().st_size:,} bytes")
