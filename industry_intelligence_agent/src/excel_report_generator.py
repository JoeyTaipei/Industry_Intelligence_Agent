"""Excel workbook generator for the Industry Intelligence Agent MVP.

The workbook is designed for interview demonstration. It shows that the output
can move from Python data processing into Excel analysis using filters, freeze
panes, conditional formatting, and business formulas.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


logger = logging.getLogger(__name__)


def generate_excel_report(
    company_profile_df: pd.DataFrame,
    news_df: pd.DataFrame,
    kri_df: pd.DataFrame,
    dashboard_df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Create `industry_intelligence_demo.xlsx` with analysis-ready sheets."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    summary_df = _build_summary_by_company(company_profile_df, news_df, kri_df)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        company_profile_df.to_excel(writer, sheet_name="Company_Profile", index=False)
        news_df.to_excel(writer, sheet_name="News_Articles", index=False)
        kri_df.to_excel(writer, sheet_name="KRI_Evidence", index=False)
        summary_df.to_excel(writer, sheet_name="Summary_By_Company", index=False)
        dashboard_df.to_excel(writer, sheet_name="Dashboard_View", index=False, startrow=2)

    workbook = load_workbook(path)
    for sheet_name in workbook.sheetnames:
        if sheet_name == "Dashboard_View":
            _add_dashboard_note(workbook[sheet_name])
            _format_sheet(workbook[sheet_name], header_row=3)
        else:
            _format_sheet(workbook[sheet_name])

    _add_summary_formulas(workbook["Summary_By_Company"])
    _add_dashboard_formulas(workbook["Dashboard_View"], header_row=3)
    _add_conditional_formatting(workbook["KRI_Evidence"])
    _add_conditional_formatting(workbook["Dashboard_View"], header_row=3)

    workbook.save(path)
    logger.info("Saved Excel report to %s", path)
    return path


def _build_summary_by_company(
    company_profile_df: pd.DataFrame,
    news_df: pd.DataFrame,
    kri_df: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row per company for Excel summary formulas."""
    if company_profile_df.empty:
        company_profile_df = pd.DataFrame([{"company_name": "Target Company", "industry": ""}])

    rows: list[dict[str, Any]] = []
    for _, company in company_profile_df.iterrows():
        name = company.get("company_name", "")
        rows.append(
            {
                "company_name": name,
                "industry": company.get("industry", ""),
                "total_news_count": _count_matches(news_df, "company_name", name),
                "total_kri_count": _count_matches(kri_df, "company_name", name),
                "high_severity_kri_count": _count_matches(kri_df, "severity_hint", "high", company_name=name),
                "medium_severity_kri_count": _count_matches(kri_df, "severity_hint", "medium", company_name=name),
                "low_severity_kri_count": _count_matches(kri_df, "severity_hint", "low", company_name=name),
                "risk_score_sum": _risk_score_sum(kri_df, name),
            }
        )
    return pd.DataFrame(rows)


def _add_summary_formulas(ws) -> None:
    """Add Excel formulas for COUNTIFS, SUMIFS, and lookup-style mapping.

    The formulas are intentionally visible so interviewers can see practical
    Excel analysis skills in addition to Python.
    """
    headers = [cell.value for cell in ws[1]]
    start_col = len(headers) + 1
    formula_headers = [
        "excel_countifs_high",
        "excel_countifs_medium",
        "excel_sumifs_risk_score",
        "excel_xlookup_industry_demo",
    ]
    for offset, header in enumerate(formula_headers):
        ws.cell(row=1, column=start_col + offset, value=header)

    for row in range(2, ws.max_row + 1):
        company_cell = f"A{row}"
        # COUNTIFS counts rows in KRI_Evidence matching both company and severity.
        ws.cell(row=row, column=start_col, value=f'=COUNTIFS(KRI_Evidence!B:B,{company_cell},KRI_Evidence!H:H,"high")')
        ws.cell(row=row, column=start_col + 1, value=f'=COUNTIFS(KRI_Evidence!B:B,{company_cell},KRI_Evidence!H:H,"medium")')
        # SUMIFS sums numeric risk_score_hint for each company.
        ws.cell(row=row, column=start_col + 2, value=f"=SUMIFS(KRI_Evidence!I:I,KRI_Evidence!B:B,{company_cell})")
        # XLOOKUP-style mapping. If XLOOKUP is unavailable, user can replace with VLOOKUP.
        ws.cell(row=row, column=start_col + 3, value=f"=XLOOKUP({company_cell},Company_Profile!C:C,Company_Profile!D:D,\"Not found\")")


def _add_dashboard_note(ws) -> None:
    """Add an interview-facing Chinese note to the Dashboard_View sheet."""
    note = "說明：此 Excel 由 Python 自動產生，展示顧問與 business users 可用的 KRI 風險證據、新聞訊號與 dashboard-ready 分析結果；本 MVP 使用 sample/public-style data，最終判斷需人工審閱。"
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)
    ws["A1"] = note
    ws["A1"].font = Font(bold=True, color="1F4E78")
    ws["A1"].fill = PatternFill(start_color="D9EAF7", end_color="D9EAF7", fill_type="solid")


def _add_dashboard_formulas(ws, header_row: int = 1) -> None:
    """Add simple formulas to Dashboard_View for demo purposes."""
    headers = [cell.value for cell in ws[header_row]]
    start_col = len(headers) + 1
    ws.cell(row=header_row, column=start_col, value="excel_follow_up_flag")
    ws.cell(row=header_row, column=start_col).fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    ws.cell(row=header_row, column=start_col).font = Font(color="FFFFFF", bold=True)
    for row in range(header_row + 1, ws.max_row + 1):
        # If high severity count is greater than zero, flag for follow-up.
        ws.cell(row=row, column=start_col, value=f'=IF(E{row}>0,"Priority follow-up","Monitor")')
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(ws.max_column)}{ws.max_row}"
    ws.column_dimensions[get_column_letter(start_col)].width = 24


def _format_sheet(ws, header_row: int = 1) -> None:
    """Add filters, freeze panes, header style, and column widths."""
    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(ws.max_column)}{ws.max_row}"
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    for cell in ws[header_row]:
        cell.fill = header_fill
        cell.font = header_font

    for column_cells in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        width = min(max(max_length + 2, 12), 45)
        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = width


def _add_conditional_formatting(ws, header_row: int = 1) -> None:
    """Highlight severity and risk level cells."""
    red_fill = PatternFill(start_color="F4CCCC", end_color="F4CCCC", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    green_fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")

    for column in range(1, ws.max_column + 1):
        header = str(ws.cell(row=header_row, column=column).value or "").lower()
        if "severity" in header or "risk_level" in header:
            letter = get_column_letter(column)
            cell_range = f"{letter}{header_row + 1}:{letter}{ws.max_row}"
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"high"'], fill=red_fill))
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"medium"'], fill=yellow_fill))
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"low"'], fill=green_fill))
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"High"'], fill=red_fill))
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"Medium"'], fill=yellow_fill))
            ws.conditional_formatting.add(cell_range, CellIsRule(operator="equal", formula=['"Low"'], fill=green_fill))


def _count_matches(df: pd.DataFrame, column: str, value: str, company_name: str | None = None) -> int:
    if df.empty or column not in df.columns:
        return 0
    mask = df[column].fillna("").astype(str).str.lower() == str(value).lower()
    if company_name and "company_name" in df.columns:
        mask &= df["company_name"].fillna("").astype(str).str.lower() == company_name.lower()
    return int(mask.sum())


def _risk_score_sum(kri_df: pd.DataFrame, company_name: str) -> int:
    if kri_df.empty or "risk_score_hint" not in kri_df.columns or "company_name" not in kri_df.columns:
        return 0
    subset = kri_df[kri_df["company_name"].fillna("").astype(str).str.lower() == company_name.lower()]
    return int(pd.to_numeric(subset["risk_score_hint"], errors="coerce").fillna(0).sum())
