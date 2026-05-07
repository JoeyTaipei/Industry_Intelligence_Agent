"""Generate interview preparation PDF using reportlab."""

import pathlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_LEFT

OUTPUT = pathlib.Path(__file__).parent.parent / "data" / "report" / "interview_prep_guide.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

W = A4[0] - 4 * cm
styles = getSampleStyleSheet()


def _s(base_name: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(f"{base_name}_c", parent=styles[base_name], **kw)


TITLE_S  = _s("Title",    fontSize=22, textColor=colors.HexColor("#1a3a5c"), spaceAfter=6)
SUBT_S   = _s("Title",    fontSize=16, textColor=colors.HexColor("#2e6da4"), spaceAfter=4)
H1_S     = _s("Heading1", fontSize=15, textColor=colors.HexColor("#1a3a5c"), spaceBefore=14, spaceAfter=4)
H2_S     = _s("Heading2", fontSize=12, textColor=colors.HexColor("#2e6da4"), spaceBefore=10, spaceAfter=3)
BODY_S   = _s("Normal",   fontSize=9.5, leading=14, spaceAfter=4)
BULLET_S = _s("Normal",   fontSize=9.5, leading=14, leftIndent=14, spaceAfter=3)
CODE_S   = _s("Code",     fontSize=8.5, backColor=colors.HexColor("#f4f4f4"), leading=12)
CAPTION_S= _s("Normal",   fontSize=8,   textColor=colors.grey, spaceAfter=2)


def hr():      return HRFlowable(width=W, thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=6, spaceBefore=6)
def h1(t):     return Paragraph(t, H1_S)
def h2(t):     return Paragraph(t, H2_S)
def p(t):      return Paragraph(t, BODY_S)
def b(t):      return Paragraph(f"<bullet>•</bullet> {t}", BULLET_S)
def code(t):   return Paragraph(t, CODE_S)
def sp(n=8):   return Spacer(1, n)


def tbl(data, col_widths, header_bg="#1a3a5c"):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(header_bg)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


story = []

# ── TITLE PAGE ────────────────────────────────────────────────────────────────
story += [
    sp(40),
    Paragraph("Industry Intelligence Agent", TITLE_S),
    Paragraph("Interview Preparation Guide", SUBT_S),
    sp(6),
    Paragraph("Deloitte Digital Technology Intern  |  Joey Wu  |  2026", CAPTION_S),
    hr(),
    sp(8),
    p("This guide summarises project architecture, KRI methodology, real news data with "
      "key numbers, the KRI pivot table, interview Q&A, and Deloitte JD mapping. "
      "<b>Bold numbers are directly quotable in interviews.</b>"),
    PageBreak(),
]

# ── 1. WHAT IS THIS PROJECT ────────────────────────────────────────────────────
story += [
    h1("1. What Is This Project?"),
    hr(),
    p("A Python-based Industry Intelligence Agent that reads news RSS feeds, annual report PDFs, "
      "and company registry data, extracts Key Risk Indicators (KRI), generates a bilingual "
      "consulting-style Industry Intelligence Brief, and visualises results in a Streamlit dashboard."),
    sp(),
    tbl([
        ["Dimension", "Details"],
        ["Target audience",  "Consulting/strategy teams needing rapid industry risk overview"],
        ["Primary output",   "KRI Evidence Table + Industry Intelligence Brief (ZH/EN)"],
        ["Demo scenario",    "Taiwan semiconductor/AI server ecosystem (TSMC, MediaTek, Quanta...)"],
        ["Tech stack",       "Python, pandas, Streamlit, Altair, pdfplumber, feedparser, reportlab"],
        ["Code size",        "~1,200 lines (src/ + app.py)"],
    ], [4*cm, 12.4*cm]),
    sp(),
    h2("One-sentence pitch"),
    p('"I built a tool that turns raw news and annual reports into structured risk evidence '
      'and a bilingual consulting brief - the kind of first-cut analysis a junior consultant '
      'would spend days on manually."'),
]

# ── 2. ARCHITECTURE ────────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("2. System Architecture & Data Flow"),
    hr(),
    tbl([
        ["Step", "Module", "What It Does"],
        ["1. Input",           "app.py sidebar",                 "Company name, ticker, industry, PDF upload"],
        ["2. Company Registry","src/company_registry.py",        "Lookup profile from CSV (name, ticker, industry)"],
        ["3. News Collection", "src/news_collector.py",          "Fetch RSS feeds, filter by keyword, score relevance"],
        ["4. PDF Parsing",     "src/annual_report_reader.py",    "Extract text chunks from annual report PDF"],
        ["5. KRI Extraction",  "src/kri_extractor.py",           "Keyword match -> 12 risk categories + severity score"],
        ["6. Trend Notes",     "src/industry_trend_reader.py",   "Convert combined text to structured trend JSON"],
        ["7. Report",          "src/report_generator.py",        "Generate ZH/EN Markdown brief from all evidence"],
        ["8. Dashboard",       "app.py",                         "Streamlit: metrics, Altair charts, pivot table, download"],
    ], [2.5*cm, 4.5*cm, 9.4*cm]),
    sp(),
    h2("Key Design Principle: Guardrails"),
    b("Facts from sources - company registry, news summaries, annual report sentences"),
    b("Analytical interpretation - risk prioritisation, business implications"),
    b("Recommended follow-up - client interview questions and data validation"),
    p("Every output is labelled by type. This prevents hallucination and mirrors consulting "
      "report standards."),
]

# ── 3. KRI METHODOLOGY ────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("3. KRI Extraction Methodology"),
    hr(),
    h2("KRI vs KPI"),
    p("<b>KPI</b> measures current performance (e.g. TSMC revenue +45.2% YoY). "
      "<b>KRI</b> is an early warning signal of risk before it hits financials "
      "(e.g. 'Helium prices doubled' = supply chain risk). "
      "This system extracts KRI evidence from text using 12-category keyword dictionaries."),
    sp(),
    h2("12 KRI Categories"),
    tbl([
        ["Category",                   "Key Trigger Words",                              "Demo Evidence"],
        ["supply chain risk",          "shortage, logistics, supplier, delivery delay",   "Strait of Hormuz closed; helium 2x price"],
        ["geopolitical risk",          "tariff, export controls, cross-strait, war",      "US 50% tariff China chips; Taiwan 15%"],
        ["customer concentration risk","major customer, top 5 customers, key customer",   "TSMC capacity alert: NVIDIA & Broadcom"],
        ["ESG / sustainability risk",  "energy usage, carbon, emissions, renewable",      "97% energy imported; 11-day LNG reserve"],
        ["regulatory risk",            "regulation, compliance, sanction, fine",          "China: Ga, Ge, graphite export controls"],
        ["profitability risk",         "gross margin, pricing pressure, cost increase",   "Arizona fab +30% cost vs Taiwan"],
        ["inventory risk",             "inventory, obsolete, stock level, turnover",      "Tariff uncertainty -> order timing shifts"],
        ["cash flow risk",             "cash flow, capex, free cash flow",               "USD 165B+ US investment commitments"],
        ["liquidity risk",             "liquidity, working capital, current ratio",       "Volatile orders -> WC pressure"],
        ["receivables risk",           "accounts receivable, bad debt, credit loss",      "Enterprise payment terms vary"],
        ["cyber / digital risk",       "cyber, data breach, ransomware, OT",             "Connected factories -> OT attack surface"],
        ["leverage risk",              "debt, borrowings, interest expense, covenant",    "Large capex financed via debt markets"],
    ], [3.8*cm, 4.5*cm, 7.6*cm]),
    sp(),
    h2("Severity Scoring"),
    tbl([
        ["Level", "Trigger Words", "Score"],
        ["HIGH (3)",   '"significant", "material", "severe", "critical", "sharp decline", "liquidity pressure"', "3"],
        ["MEDIUM (2)", '"decline", "shortage", "delay", "loss", "uncertainty", "pressure", "disruption"',       "2"],
        ["LOW (1)",    "Any KRI keyword without HIGH or MEDIUM words",                                           "1"],
    ], [2*cm, 12*cm, 1.4*cm]),
]

# ── 4. KRI PIVOT TABLE ────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("4. The KRI Pivot Table - COUNTIFS Equivalent"),
    hr(),
    h2("What it is"),
    p("The KRI Category x Severity Pivot Table shows how many evidence sentences belong to each "
      "risk category at each severity level. It is the single most important output for prioritising "
      "analyst review - equivalent to running Excel COUNTIFS across 36 combinations at once."),
    sp(),
    p("Excel equivalent: =COUNTIFS(kri_category, \"supply chain risk\", severity, \"high\")"),
    sp(),
    h2("Demo Output (8 KRI rows from real news)"),
    tbl([
        ["KRI Category",              "High", "Medium", "Low", "Total", "Priority"],
        ["supply chain risk",         "1",    "0",      "0",   "1",     "1st - validate immediately"],
        ["geopolitical risk",         "1",    "0",      "0",   "1",     "1st - validate immediately"],
        ["customer concentration risk","1",   "0",      "0",   "1",     "1st - validate immediately"],
        ["ESG / sustainability risk",  "1",   "0",      "0",   "1",     "1st - validate immediately"],
        ["regulatory risk",           "0",    "1",      "0",   "1",     "2nd - monitor closely"],
        ["profitability risk",         "0",   "1",      "0",   "1",     "2nd - monitor closely"],
        ["inventory risk",            "0",    "1",      "0",   "1",     "2nd - monitor closely"],
        ["cyber / digital risk",      "0",    "0",      "1",   "1",     "3rd - review in next cycle"],
    ], [4.5*cm, 1.5*cm, 1.8*cm, 1.5*cm, 1.8*cm, 5.3*cm]),
    sp(),
    h2("How to explain it in an interview"),
    b("HIGH severity -> validate first with management interview + financial data"),
    b("MEDIUM severity -> dashboard monitoring candidates"),
    b("Appears in news AND annual report -> management has already acknowledged the risk"),
    b("Appears only in news (not annual report) -> potential management cognition gap"),
    b("High total across categories -> systemic risk environment, not isolated events"),
]

# ── 5. KEY NUMBERS ────────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("5. Key Numbers to Quote in Interviews"),
    hr(),
    p("<b>All sourced from real news (Jan-May 2026). Cite the source when you quote.</b>"),
    sp(),
    tbl([
        ["Fact",                                      "Number",        "Source"],
        ["TSMC March 2026 revenue YoY",              "+45.2%",        "HeyGoTrade, Apr 2026"],
        ["TSMC March 2026 revenue",                  "NTD 415.2B",    "HeyGoTrade, Apr 2026"],
        ["TSMC dividend increase",                   "+28%",          "247 Wall St, Feb 2026"],
        ["TSMC global advanced node market share",   ">65%",          "Yahoo Finance, Apr 2026"],
        ["Taiwan energy import dependency",          "97%",           "Yahoo Finance, Apr 2026"],
        ["Taiwan LNG reserve (no imports)",          "11 days",       "Yahoo Finance, Apr 2026"],
        ["Strait of Hormuz closure date",            "March 4, 2026", "HeyGoTrade, Apr 2026"],
        ["Helium price increase",                    "2x (doubled)",  "HeyGoTrade, Apr 2026"],
        ["US tariff on Chinese semiconductor imports","50%",          "Tom's Hardware, Apr 2026"],
        ["Taiwan reciprocal tariff rate (US deal)",  "<=15%",         "CNBC, Jan 2026"],
        ["Taiwan US investment commitment",          "USD 250B",      "CNBC, Jan 2026"],
        ["TSMC Arizona fab cost premium vs Taiwan",  "+30%",          "247 Wall St, Feb 2026"],
        ["TSMC Arizona total investment target",     "USD 465B / 11 fabs","abhs.in, Apr 2026"],
        ["New China chip tariffs effective date",    "June 2027",     "Tom's Hardware, Apr 2026"],
        ["US-China total tariff on Chinese goods",  "30%",           "Tax Foundation, May 2026"],
    ], [7*cm, 3.2*cm, 6.2*cm]),
]

# ── 6. DELOITTE JD MAPPING ────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("6. Deloitte JD Mapping"),
    hr(),
    tbl([
        ["JD Requirement (ZH)", "How This Project Demonstrates It"],
        ["整理資料分析與產業趨勢內容",
         "KRI evidence table, industry trend notes, and stacked pivot chart from real news data"],
        ["撰寫數據分析程式",
         "Python pipeline: pandas wrangling, keyword NLP, severity scoring, Altair chart generation (~1,200 lines)"],
        ["支援數位轉型與 AI 應用",
         "Digital Transformation Opportunity Map with 5 concrete use cases (demand planning, supplier risk, WC dashboard, ESG)"],
        ["將技術分析轉成 business insight",
         "Bilingual ZH/EN brief separating facts / interpretation / recommended follow-up (consulting standard)"],
        ["溝通能力",
         "Can demo the Streamlit app, explain KRI methodology, and quote key numbers in 2-3 minutes"],
    ], [5*cm, 11.4*cm]),
]

# ── 7. INTERVIEW Q&A ──────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("7. Interview Q&A - Talking Points"),
    hr(),
    h2("Q: Tell me about your project."),
    p("An automated Industry Intelligence Agent. Given a company name and PDF annual report, "
      "it extracts 12 types of KRI from news and text, scores them by severity, generates a "
      "bilingual consulting brief, and visualises in an interactive dashboard. "
      "Demo focuses on TSMC and the Taiwan semiconductor/AI server ecosystem using real 2026 news."),
    sp(),
    h2("Q: What is KRI and how is it different from KPI?"),
    p("KPI measures current performance - TSMC revenue was +45.2% YoY in March 2026. "
      "KRI is an early warning signal. 'Helium prices doubled' is a KRI for supply chain risk. "
      "My system extracts KRI from text using 12 keyword categories and scores severity as "
      "High/Medium/Low based on word strength."),
    sp(),
    h2("Q: How accurate is your KRI extraction?"),
    p("Rule-based keyword matching - transparent, not a black box. For the demo, all 8 KRI rows "
      "were verified against real news (CNBC, Tom's Hardware, Yahoo Finance). "
      "In production, an LLM layer would improve recall on ambiguous sentences."),
    sp(),
    h2("Q: Why Streamlit, not Power BI?"),
    p("Streamlit lets me wire Python analysis directly to the UI. For a client deliverable, "
      "Power BI would be appropriate - I built dashboard-ready CSV export precisely for that handoff."),
    sp(),
    h2("Q: What is the KRI Pivot Table?"),
    p("It is a COUNTIFS-equivalent summary: for each of 12 risk categories, it shows how many "
      "evidence sentences are High/Medium/Low severity. Single most useful output for prioritising "
      "analyst review. Categories with HIGH count get validated first with management interviews. "
      "Categories only appearing in news (not annual report) suggest a management cognition gap."),
    sp(),
    h2("Q: What would you improve with more time?"),
    p("(1) LLM classifier to improve KRI recall on ambiguous text. "
      "(2) Financial data integration (TWSE API, Bloomberg) linking KRI signals to actual ratios. "
      "(3) Time-series view tracking how risk signals evolve across quarterly reports."),
    sp(),
    h2("Q: How does this relate to Deloitte's work?"),
    p("Deloitte advisory starts with rapid industry and company analysis before client interviews. "
      "This tool automates evidence-gathering and risk-categorisation, so consultants focus on "
      "validating findings, designing solutions, and building the business case. "
      "The KRI Evidence Table becomes a pre-interview hypothesis list."),
]

# ── 8. HOW TO RUN ─────────────────────────────────────────────────────────────
story += [
    PageBreak(),
    h1("8. How to Run"),
    hr(),
    code("cd c:\\Projects\\Industry_intelligenceAgent\\industry_intelligence_agent"),
    code("streamlit run app.py"),
    sp(),
    p("Opens at http://localhost:8501. Default loads TSMC demo data with real 2026 news. "
      "To analyse Apple: uncheck 'Use demo data', change Company to Apple, upload 10-K PDF."),
    sp(),
    h2("Active File Structure (after cleanup)"),
    tbl([
        ["Path",                      "Purpose"],
        ["app.py",                    "Streamlit UI - main entry point"],
        ["src/kri_extractor.py",      "KRI keyword extraction + severity scoring"],
        ["src/report_generator.py",   "ZH/EN Markdown brief generation"],
        ["src/news_collector.py",     "RSS feed fetching + keyword filter"],
        ["src/annual_report_reader.py","PDF text extraction and chunking"],
        ["src/summarizer.py",         "LLM or rule-based company brief generation"],
        ["data/demo/",                "Pre-built demo data (real news, KRI, trends)"],
        ["data/report/",              "Generated PDF (this file)"],
        ["configs/rss_sources.yaml",  "RSS feed URLs - editable without code change"],
    ], [5.5*cm, 10.9*cm]),
]

doc = SimpleDocTemplate(
    str(OUTPUT), pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
)
doc.build(story)
print(f"PDF created: {OUTPUT}")
print(f"Size: {OUTPUT.stat().st_size:,} bytes")
