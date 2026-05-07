"""Technical interview Q&A PDF with code blocks.

Covers: pandas, KRI extraction, PDF parsing, RSS, Streamlit, Altair, pipeline design.
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
    HRFlowable, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

pdfmetrics.registerFont(TTFont("ZH",  "C:/Windows/Fonts/msjh.ttc",   subfontIndex=0))
pdfmetrics.registerFont(TTFont("ZHB", "C:/Windows/Fonts/msjhbd.ttc", subfontIndex=0))

OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "report" / "technical_interview_questions.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

W = A4[0] - 3.6 * cm
base = getSampleStyleSheet()

def _s(tag, font="ZH", size=9.5, lead=14, color=colors.black,
       align=TA_LEFT, sb=2, sa=3, li=0, bg=None, bc=None, bw=0, bp=0):
    kw = dict(fontName=font, fontSize=size, leading=lead, textColor=color,
              alignment=align, spaceBefore=sb, spaceAfter=sa, leftIndent=li)
    if bg: kw["backColor"] = bg
    if bc: kw.update(borderColor=bc, borderWidth=bw, borderPadding=bp)
    return ParagraphStyle(tag, parent=base["Normal"], **kw)

CT   = _s("ct",  "ZHB", 20, 26, colors.HexColor("#17324d"), TA_CENTER, sb=0, sa=3)
CS   = _s("cs",  "ZH",  11, 16, colors.HexColor("#2e6da4"), TA_CENTER, sb=0, sa=2)
CN   = _s("cn",  "ZH",   8, 11, colors.HexColor("#999999"), TA_CENTER, sb=0, sa=2)
H1   = _s("h1",  "ZHB", 12, 17, colors.HexColor("#17324d"), sb=9, sa=2)
H2   = _s("h2",  "ZHB", 10, 14, colors.HexColor("#2e6da4"), sb=6, sa=2)
BOD  = _s("bod", "ZH",   9.5, 14, sb=0, sa=2)
CAP  = _s("cap", "ZH",   7.5, 11, colors.HexColor("#888888"), sb=0, sa=1)
Q_S  = _s("q",   "ZHB",  9.8, 14, colors.HexColor("#17324d"),
           sb=7, sa=1, bg=colors.HexColor("#f0f4f8"),
           bc=colors.HexColor("#4a7ab5"), bw=1.5, bp=5)
A_S  = _s("a",   "ZH",   9.5, 14, sb=1, sa=1, li=8)
ANS  = _s("ans", "ZH",   9.5, 14, sb=0, sa=3, li=8,
           bg=colors.HexColor("#fafbfc"))
NOTE = _s("nt",  "ZH",   8.5, 13, colors.HexColor("#5a7a5a"), sb=0, sa=3, li=8,
          bg=colors.HexColor("#f0f7f0"),
          bc=colors.HexColor("#7ab57a"), bw=1, bp=4)
CODE_S = ParagraphStyle("code", parent=base["Code"],
    fontName="Courier", fontSize=8, leading=11.5,
    backColor=colors.HexColor("#f3f5f7"),
    borderColor=colors.HexColor("#c8d0da"), borderWidth=0.5, borderPadding=7,
    spaceBefore=2, spaceAfter=5, leftIndent=8, rightIndent=8)
TH = _s("th", "ZHB", 7.8, 11, colors.white, sb=0, sa=0)
TD = _s("td", "ZH",  7.8, 11, sb=0, sa=0)


def s(n=4):   return Spacer(1, n)
def p(t):     return Paragraph(t, BOD)
def h1(t):    return Paragraph(t, H1)
def h2(t):    return Paragraph(t, H2)
def cap(t):   return Paragraph(t, CAP)
def q(t):     return Paragraph(f"Q: {t}", Q_S)
def a(t):     return Paragraph(t, ANS)
def note(t):  return Paragraph(f"面試補充：{t}", NOTE)
def code(t):  return Preformatted(t.strip("\n"), CODE_S)

def div():
    return HRFlowable(width=W, thickness=0.3,
                      color=colors.HexColor("#d4dce8"), spaceBefore=5, spaceAfter=2)

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

# ── Cover ─────────────────────────────────────────────────────────────────────
story += [
    s(30),
    Paragraph("技術面試題目整理", CT),
    Paragraph("Industry Intelligence Agent — 技術問題 + Code Block", CS),
    s(3),
    Paragraph("Deloitte Digital Technology Intern · Joey Wu · 2026", CN),
    s(8),
    Paragraph(
        "每個問題分為：Q（面試官問）→ 答案 → Code Block → 面試補充。\n"
        "Code 要能看懂邏輯，不需要背，但關鍵行要能解釋。",
        _s("cb", "ZH", 9.5, 15, colors.HexColor("#444444"), TA_CENTER, sb=0, sa=0)
    ),
    PageBreak(),
]

# ══════════════════════════════════════════════════════════════════════════════
# A. pandas 資料處理
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("A  pandas 資料處理"), div()]

story += [
    q("你的 KRI DataFrame 有哪些欄位？怎麼建出來的？"),
    a("每一筆 KRI evidence 是一個 dict，最後用 pd.DataFrame(records) 一次建起來。"),
    code("""\
records = []
for sentence in sentences:
    for category, keywords in kri_dictionary.items():
        for keyword in keywords:
            if keyword.lower() in sentence.lower():
                records.append({
                    "kri_category":     category,
                    "matched_keyword":  keyword,
                    "evidence_sentence": sentence,
                    "severity_hint":    _severity_hint(sentence),
                    "source_type":      source_type,
                })
                break          # 同一類別一句只記一次
kri_df = pd.DataFrame(records)"""),
    note("關鍵是 break：同一類別一句話只記一次，避免同類別多個關鍵字重複建 row。"),
    div(),

    q("怎麼把 KRI 依嚴重度排序，然後取前 10 筆？"),
    a("用 map 把 severity 轉成數字再 sort，最後 head(10)。"),
    code("""\
SEV_ORDER = {"high": 0, "medium": 1, "low": 2}
kri_df["_rank"] = kri_df["severity_hint"].str.lower().map(SEV_ORDER).fillna(3)
top10 = kri_df.sort_values("_rank").head(10).drop(columns=["_rank"])"""),
    note("fillna(3) 讓沒有 severity 的 row 排在最後，不會讓程式 crash。"),
    div(),

    q("怎麼做 COUNTIFS 等效的 KRI 樞紐表？"),
    a("groupby 兩個欄位後 unstack，再補齊缺少的嚴重度欄。"),
    code("""\
pivot = (
    kri_df
    .groupby(["kri_category", "severity_hint"])
    .size()
    .unstack(fill_value=0)
)
for col in ["high", "medium", "low"]:
    if col not in pivot.columns:
        pivot[col] = 0
pivot = pivot[["high", "medium", "low"]]
pivot["total"] = pivot.sum(axis=1)
pivot = pivot.sort_values("total", ascending=False)"""),
    note("這等於 Excel 的 COUNTIFS(category_col, A, severity_col, \"high\")，一次算完所有組合。"),
    div(),

    q("怎麼讀有中文的 CSV 並避免亂碼？"),
    a("用 utf-8-sig 讀取（處理 BOM）；寫出時也用 utf-8-sig。"),
    code("""\
import pandas as pd

# 讀取
df = pd.read_csv("kri_evidence.csv", encoding="utf-8-sig", dtype=str).fillna("")

# 寫出
df.to_csv("output.csv", index=False, encoding="utf-8-sig")"""),
    note("utf-8-sig 會自動處理 Excel 加的 BOM（Byte Order Mark），避免第一格亂碼。"),
    div(),

    q("怎麼 concat 多個 DataFrame 並去重？"),
    a("pd.concat 後用 drop_duplicates，指定關鍵欄位。"),
    code("""\
frames = [news_kri_df, annual_kri_df]   # 可能某個為空
kri_df = pd.concat(frames, ignore_index=True)
kri_df = kri_df.drop_duplicates(
    subset=["source_type", "kri_category", "evidence_sentence"]
)"""),
    note("ignore_index=True 讓 index 重新從 0 開始，避免重複 index 造成後續 bug。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# B. KRI 萃取邏輯
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("B  KRI 萃取邏輯"), div()]

story += [
    q("severity 是怎麼判斷的？"),
    a("用兩組關鍵字清單，先比對 HIGH，再比對 MEDIUM，否則是 LOW。"),
    code("""\
HIGH_WORDS = ["significant", "material", "severe", "critical",
              "sharp decline", "liquidity pressure", "insolvency"]
MED_WORDS  = ["decline", "shortage", "delay", "loss", "uncertainty",
              "pressure", "disruption", "volatile", "risk", "challenge"]

def _severity_hint(sentence: str) -> str:
    s = sentence.lower()
    if any(w in s for w in HIGH_WORDS):
        return "high"
    if any(w in s for w in MED_WORDS):
        return "medium"
    return "low" """),
    note("嚴重度是 prioritization hint，不是財務模型。面試時主動說這句話。"),
    div(),

    q("怎麼把長文章切成句子？"),
    a("用 regex 在句號、問號、驚嘆號後面切，再過濾太短的句子。"),
    code("""\
import re

def split_sentences(text: str) -> list[str]:
    # 在 .!? 後面的空白或換行切開
    raw = re.split(r"(?<=[.!?])\\s+|\\n+", text)
    return [s.strip() for s in raw if len(s.strip()) >= 20]"""),
    note("len >= 20 過濾掉單字碎片和頁碼，不會讓短到沒意義的文字變成 evidence。"),
    div(),

    q("如果同一句話同時命中兩個 KRI 類別，怎麼處理？"),
    a("外層 for 跑 category，內層 for 跑 keyword，命中就 break keyword loop，但不 break category loop。所以一句話會對多個類別各產生一筆 record。"),
    code("""\
for category, keywords in kri_dict.items():
    for keyword in keywords:
        if keyword.lower() in sentence.lower():
            records.append({...})
            break    # 跳出 keyword loop，但繼續下一個 category
            # 不 break category loop，讓同一句命中多類別"""),
    note("這是設計決策：同一句話可能同時是 supply chain risk 也是 geopolitical risk，兩個都要記。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# C. PDF 年報處理
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("C  PDF 年報處理"), div()]

story += [
    q("怎麼從 PDF 擷取文字？"),
    a("先用 pdfplumber，如果沒有文字再試 PyMuPDF（fitz）。"),
    code("""\
def extract_text(pdf_path: str) -> str:
    # 嘗試 pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = "\\n\\n".join(p.extract_text() or "" for p in pdf.pages)
        if text.strip():
            return text
    except Exception:
        pass

    # 嘗試 PyMuPDF
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            return "\\n\\n".join(p.get_text("text") for p in doc)
    except Exception:
        return "" """),
    note("兩個 library 都有可能失敗：pdfplumber 對某些 PDF 格式有問題；PyMuPDF 是備援。"),
    div(),

    q("怎麼把長文本切成 chunk 讓 KRI 擷取更準確？"),
    a("用 sliding window：每 900 個 word 一個 chunk，overlap 120 個 word。"),
    code("""\
def chunk_text(text: str, chunk_size=900, overlap=120) -> list[dict]:
    words = text.split()
    chunks, start, idx = [], 0, 1
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append({
            "chunk_id": idx,
            "text": " ".join(words[start:end]),
        })
        if end >= len(words):
            break
        start = end - overlap   # 往前回 overlap 個 word
        idx += 1
    return chunks"""),
    note("overlap 讓跨 chunk 邊界的句子不會被切斷，KRI extraction 不會漏掉關鍵字。"),
    div(),

    q("怎麼找 Risk Factors 這種章節的位置？"),
    a("用 regex 找各個 section heading 在文本中的起始位置，再截取到下一個 heading。"),
    code("""\
import re

ANCHORS = {
    "risk_factors": [r"\\brisk factors\\b", r"\\bitem 1a\\.?\\s+risk factors\\b"],
    "management_discussion": [r"\\bmd&a\\b", r"\\bmanagement.{1,15}discussion\\b"],
}

def find_sections(text: str) -> dict[str, str]:
    lower = text.lower()
    hits = []
    for section, patterns in ANCHORS.items():
        for pat in patterns:
            m = re.search(pat, lower, re.IGNORECASE)
            if m:
                hits.append((m.start(), section))
                break
    hits.sort()
    result = {}
    for i, (start, name) in enumerate(hits):
        end = hits[i+1][0] if i+1 < len(hits) else len(text)
        result[name] = text[start:end][:8000]   # 最多 8000 字
    return result"""),
    note("Apple 10-K 的 Risk Factors 可能是 Item 1A.，regex 要能同時 match 兩種格式。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# D. RSS 新聞收集
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("D  RSS 新聞收集"), div()]

story += [
    q("怎麼用 feedparser 抓 Google News RSS？"),
    a("用 urllib.parse.quote_plus 把查詢字串 encode，再用 feedparser 解析。"),
    code("""\
from urllib.parse import quote_plus
import feedparser

def fetch_google_news(query: str, max_articles=10) -> list[dict]:
    url = (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:max_articles]:
        results.append({
            "title":          entry.get("title", ""),
            "url":            entry.get("link",  ""),
            "published_date": entry.get("published", ""),
            "summary":        entry.get("summary", ""),
        })
    return results"""),
    note("feedparser 不會拋 exception，就算 URL 錯了也只會回傳空 entries。要檢查 len(feed.entries)。"),
    div(),

    q("RSS 失敗時怎麼 graceful fallback？"),
    a("先嘗試 RSS，如果 entries 是空的就 fall back 到 demo CSV。"),
    code("""\
def fetch_news(query: str, demo_csv: str) -> pd.DataFrame:
    try:
        articles = fetch_google_news(query)
        if articles:
            return pd.DataFrame(articles)
    except Exception:
        pass                          # 任何錯誤都 fall back

    # Fall back: 載入預建 demo 資料
    if pathlib.Path(demo_csv).exists():
        return pd.read_csv(demo_csv, dtype=str).fillna("")
    return pd.DataFrame(columns=["title", "url", "summary"])"""),
    note("Fall back 到 demo CSV 確保面試 demo 不會因為網路問題失敗，這是 defensive programming。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# E. Streamlit 常見模式
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("E  Streamlit 常見模式"), div()]

story += [
    q("怎麼用 session_state 保存分析結果，讓頁面重跑不會消失？"),
    a("按鈕觸發分析後把結果存進 st.session_state，tab 裡面從 session_state 讀。"),
    code("""\
if st.button("Run Analysis"):
    kri_df = extract_kri(...)
    st.session_state["kri_df"] = kri_df   # 存起來

# 後面的 tab 不管有沒有按按鈕都能讀
kri_df = st.session_state.get("kri_df", pd.DataFrame())
st.dataframe(kri_df)"""),
    note("Streamlit 每次互動都重跑整個 script。session_state 是唯一跨重跑保存狀態的方式。"),
    div(),

    q("怎麼處理使用者上傳的 PDF？"),
    a("用 tempfile 把 UploadedFile 的 bytes 存到暫存檔，處理完再刪除。"),
    code("""\
import tempfile, pathlib

uploaded = st.file_uploader("上傳年報", type=["pdf"])
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = pathlib.Path(tmp.name)
    try:
        result = read_annual_report_pdf(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)   # 確保暫存檔被刪除"""),
    note("finally 確保就算 read_annual_report_pdf 丟 exception，暫存檔還是會被刪掉。"),
    div(),

    q("怎麼用 @st.cache_data 避免重複抓同一份新聞？"),
    a("加 decorator，Streamlit 會用 function 參數做 cache key，相同參數直接回傳快取。"),
    code("""\
@st.cache_data(show_spinner=False)
def load_news_cached(query: str, max_articles: int) -> pd.DataFrame:
    return fetch_google_news(query, max_articles)

# 第一次呼叫：真的去抓
# 同樣 query + max_articles：直接回傳快取，不再發 HTTP request
news_df = load_news_cached("TSMC tariff", 10)"""),
    note("cache_data 適合 pure function。如果 function 有 side effect（例如寫檔）就不要 cache。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# F. Altair 圖表
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("F  Altair 圖表"), div()]

story += [
    q("怎麼做 KRI 嚴重度的 bar chart？"),
    a("先把 severity_hint 做 value_counts，再用 mark_bar encode x/y/color。"),
    code("""\
import altair as alt

sev_df = (
    kri_df["severity_hint"].str.lower()
    .value_counts()
    .reindex(["high", "medium", "low"], fill_value=0)
    .reset_index()
)
sev_df.columns = ["severity", "count"]
sev_df["label"] = sev_df["severity"].map(
    {"high": "High", "medium": "Medium", "low": "Low"}
)

chart = (
    alt.Chart(sev_df)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("label:N", sort=["High", "Medium", "Low"], title=""),
        y=alt.Y("count:Q", title="筆數"),
        color=alt.Color("label:N",
            scale=alt.Scale(
                domain=["High", "Medium", "Low"],
                range=["#d62728", "#ff7f0e", "#2ca02c"]
            ), legend=None),
        tooltip=["label:N", "count:Q"],
    )
    .properties(height=200)
)
st.altair_chart(chart, use_container_width=True)"""),
    note(":N 表示 nominal（類別資料），:Q 表示 quantitative（數值）。Altair 靠這個推斷 scale 型別。"),
    div(),

    q("怎麼做 KRI 類別的圓餅 / 甜甜圈圖？"),
    a("用 mark_arc，設 innerRadius 就變甜甜圈圖，theta encode 數值。"),
    code("""\
cat_df = kri_df["kri_category"].value_counts().reset_index()
cat_df.columns = ["category", "count"]

chart = (
    alt.Chart(cat_df)
    .mark_arc(innerRadius=50, outerRadius=100)
    .encode(
        theta=alt.Theta("count:Q"),
        color=alt.Color("category:N",
            scale=alt.Scale(scheme="tableau20"),
            legend=alt.Legend(title="KRI 類別")),
        tooltip=["category:N", "count:Q"],
    )
    .properties(height=240)
)
st.altair_chart(chart, use_container_width=True)"""),
    note("innerRadius=0 就是一般 pie chart，innerRadius > 0 是 donut chart。"),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# G. Python 語言基礎
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("G  Python 語言基礎"), div()]

story += [
    q("dict.fromkeys 是什麼？你在哪裡用到？"),
    a("dict.fromkeys(iterable) 建一個 key 來自 iterable 的 dict，value 預設 None。配合 list() 可以去重並保留順序。"),
    code("""\
# 去重並保留插入順序（比 set 好因為 set 不保序）
seen_cats = list(dict.fromkeys(["supply chain", "geopolitical", "supply chain"]))
# → ["supply chain", "geopolitical"]

# 等效但更直觀的寫法（Python 3.7+ dict 保序）
seen_cats = list(dict.fromkeys(kri_df["kri_category"].tolist()))"""),
    div(),

    q("什麼是 dataclass？你的 FinancialIndicator 怎麼設計的？"),
    a("@dataclass 自動產生 __init__、__repr__ 等 method，省去手寫。"),
    code("""\
from dataclasses import dataclass, field
from typing import Any

@dataclass
class FinancialIndicator:
    name:   str
    value:  float | int | str
    period: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name":   self.name,
            "value":  self.value,
            "period": self.period,
            "source": self.source,
        }

# 使用
fi = FinancialIndicator("latest_close", 920.5, "2026-04-25", "stooq")
print(fi.to_dict())"""),
    div(),

    q("Python 的 try/except/finally 在你的專案怎麼用？"),
    a("PDF 解析可能失敗，用 finally 確保暫存檔被清除，不管有沒有 exception。"),
    code("""\
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(uploaded.getbuffer())
        tmp_path = pathlib.Path(f.name)
    result = read_annual_report_pdf(tmp_path)   # 可能拋 exception
except Exception as e:
    st.warning(f"PDF 解析失敗：{e}")
    result = {}
finally:
    if tmp_path:
        tmp_path.unlink(missing_ok=True)         # 一定執行，確保清除暫存"""),
    div(),

    q("f-string 和 str.format 的差別？什麼時候用哪個？"),
    a("f-string 更簡潔，是現代 Python 首選。format 在需要延遲 evaluate 時才用。"),
    code("""\
name = "TSMC"
score = 95.2

# f-string（Python 3.6+，推薦）
msg = f"{name} relevance score: {score:.1f}"

# str.format（需要模板時用）
template = "{company} relevance score: {score:.1f}"
msg = template.format(company=name, score=score)

# % 格式（舊式，不推薦）
msg = "%s relevance score: %.1f" % (name, score)"""),
    div(),
]

# ══════════════════════════════════════════════════════════════════════════════
# H. 系統設計問題
# ══════════════════════════════════════════════════════════════════════════════
story += [h1("H  系統設計問題"), div()]

story += [
    q("你的 pipeline 怎麼做到「有資料繼續、沒資料不 crash」？"),
    a("每個步驟都先確認資料是否為空，然後再處理。回傳統一的空物件格式，不回傳 None。"),
    code("""\
def safe_extract_kri(news_df, annual_chunks, company, industry):
    frames = []
    if not news_df.empty:                      # 有新聞才抽
        frames.append(extract_kri_mentions(news_df, ...))
    if annual_chunks:                          # 有年報才抽
        frames.append(extract_kri_mentions(annual_chunks, ...))
    if not frames:                             # 都沒有：回傳空 DataFrame，不 crash
        return pd.DataFrame(columns=KRI_COLUMNS)
    return pd.concat(frames, ignore_index=True)"""),
    note("這個模式讓下游程式不用判斷 None，只需判斷 df.empty，大幅減少 bug。"),
    div(),

    q("如何設計讓 KRI 字典可以不改 code 就新增類別？"),
    a("字典放在函數內或 YAML 檔，code 只負責 iterate，不 hardcode 類別名稱。"),
    code("""\
def load_kri_dictionary() -> dict[str, list[str]]:
    return {
        "supply chain risk": [
            "shortage", "logistics", "delivery delay", "raw material",
        ],
        "geopolitical risk": [
            "tariff", "export controls", "cross-strait", "war",
        ],
        # 要新增類別：只在這裡加，其他 code 不需要動
    }

def extract_kri(text: str) -> list[dict]:
    dictionary = load_kri_dictionary()    # 動態載入
    for category, keywords in dictionary.items():
        ...                               # 同一段 code 處理所有類別"""),
    note("這是 Open/Closed Principle：對擴充開放（加新類別），對修改封閉（不改 extraction 邏輯）。"),
    div(),

    q("如果要把這個系統從 Streamlit 換成 API，架構要怎麼改？"),
    a("把 business logic 完全分離到 src/ 目錄，app.py 只負責 UI。換成 FastAPI 只需要換掉 app.py，src/ 不動。"),
    code("""\
# 現在的結構（已經做到）
# app.py      — Streamlit UI layer
# src/        — Business logic（KRI 抽取、報告產生、PDF 解析）

# 換成 FastAPI 只需要：
from fastapi import FastAPI
from src.kri_extractor import extract_kri_mentions
from src.report_generator import generate_chinese_report

app = FastAPI()

@app.post("/analyze")
def analyze(company: str, text: str):
    kri_df = extract_kri_mentions(text, ...)
    report = generate_chinese_report(...)
    return {"kri": kri_df.to_dict(), "report": report}"""),
    note("面試時說「src/ 和 app.py 完全解耦，換 UI 層不需要動業務邏輯」，展示架構思維。"),
    div(),
]

# ── 速查表 ────────────────────────────────────────────────────────────────────
story += [
    h1("速查：常用 pandas 操作"),
    div(),
    tbl([
        ["操作", "Code", "說明"],
        ["讀 CSV",            "pd.read_csv(path, dtype=str).fillna('')",    "dtype=str 避免自動轉型"],
        ["寫 CSV（中文）",    "df.to_csv(path, encoding='utf-8-sig')",       "Excel 開不亂碼"],
        ["過濾 rows",         "df[df['severity'] == 'high']",                "布林 indexing"],
        ["計算各值數量",      "df['col'].value_counts()",                    "最常用的聚合"],
        ["pivot 計數",        "df.groupby(['A','B']).size().unstack()",       "COUNTIFS 等效"],
        ["concat + 去重",     "pd.concat(frames).drop_duplicates(subset=[])", "合併多個 df"],
        ["排序",              "df.sort_values('col', ascending=False)",       "降序"],
        ["取前 N 筆",         "df.head(10)",                                  "預覽 / 限制輸出"],
        ["新增欄",            "df['new'] = df['a'].map({'x':1,'y':2})",       "map 做 label encode"],
        ["轉 dict list",      "df.to_dict(orient='records')",                "給 JSON / API 用"],
    ], [2.8*cm, 6.5*cm, 7.1*cm]),
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
