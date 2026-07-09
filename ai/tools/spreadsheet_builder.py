from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

DOWNLOAD_BASE_URL = "http://localhost:8001/api/download"


NAVY       = "1B2A4A"
LIGHT_GRAY = "F5F5F5"
WHITE      = "FFFFFF"
BORDER_CLR = "CCCCCC"

COLUMNS = [
    ("Job Title",      25),
    ("Company",        20),
    ("Location",       15),
    ("Type",           12),
    ("Posted",         18),
    ("Apply Link",     40),
    ("ATS Score",      10),
    ("CV File",        40),
]

thin_border = Border(
    left=Side(style="thin", color=BORDER_CLR),
    right=Side(style="thin", color=BORDER_CLR),
    top=Side(style="thin", color=BORDER_CLR),
    bottom=Side(style="thin", color=BORDER_CLR),
)

header_font  = Font(name="Arial", size=11, bold=True, color=WHITE)
header_fill  = PatternFill("solid", fgColor=NAVY)
header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

body_font  = Font(name="Arial", size=10, color="333333")
body_align = Alignment(vertical="center", wrap_text=True)

link_font = Font(name="Arial", size=10, color="1155CC", underline="single")

score_good_font = Font(name="Arial", size=10, bold=True, color="0F6E56")
score_ok_font   = Font(name="Arial", size=10, bold=True, color="854F0B")
score_bad_font  = Font(name="Arial", size=10, bold=True, color="993C1D")


def build_xlsx(job_results: list[dict], output_path: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Job Results"

    for col_idx, (col_name, col_width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    ws.row_dimensions[1].height = 30

    for row_idx, job in enumerate(job_results, start=2):
        row_fill = PatternFill("solid", fgColor=WHITE if row_idx % 2 == 0 else LIGHT_GRAY)

        values = [
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("employment_type", ""),
            job.get("posted_at", "")[:10] if job.get("posted_at") else "",
            job.get("apply_link", ""),
            job.get("ats_score", "N/A"),
            job.get("cv_path", ""),
        ]

        for col_idx, value in enumerate(values, start=1):
            cell           = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = body_font
            cell.alignment = body_align
            cell.fill      = row_fill
            cell.border    = thin_border

        apply_link = job.get("apply_link", "")
        if apply_link:
            link_cell           = ws.cell(row=row_idx, column=6)
            link_cell.hyperlink = apply_link
            link_cell.value     = "Apply here"
            link_cell.font      = link_font

        cv_path = job.get("cv_path", "")
        if cv_path:
            cv_filename       = os.path.basename(cv_path)
            cv_cell           = ws.cell(row=row_idx, column=8)
            cv_cell.hyperlink = f"{DOWNLOAD_BASE_URL}/{cv_filename}"
            cv_cell.value     = "Download CV"
            cv_cell.font      = link_font

        score      = job.get("ats_score", "N/A")
        score_cell = ws.cell(row=row_idx, column=7)
        if isinstance(score, (int, float)):
            score_cell.value     = f"{int(score)}%"
            score_cell.alignment = Alignment(horizontal="center", vertical="center")
            if score >= 70:
                score_cell.font = score_good_font
            elif score >= 55:
                score_cell.font = score_ok_font
            else:
                score_cell.font = score_bad_font

    ws.freeze_panes = "A2"

    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    wb.save(output_path)
    return output_path
