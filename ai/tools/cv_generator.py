"""ATS-friendly CV PDF generator.

Design goals (why it looks plain):
  ATS parsers choke on colors, icons, text boxes, multi-column layouts, and
  non-standard fonts. So this renders a single-column, black-on-white PDF in a
  standard font (Helvetica), plain "•" bullets, and simple UPPERCASE section
  headers with a thin rule. No navy, no emoji, no tables-as-layout — just clean
  text a resume scanner reads correctly.
"""
import os
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)

BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
ITAL_FONT = "Helvetica-Oblique"

# ── Styles (all black) ──────────────────────────────────────
_NAME = ParagraphStyle(
    "Name", fontName=BOLD_FONT, fontSize=18, leading=21,
    alignment=TA_CENTER, spaceAfter=2,
)
_CONTACT = ParagraphStyle(
    "Contact", fontName=BODY_FONT, fontSize=9.5, leading=12,
    alignment=TA_CENTER, spaceAfter=10,
)
_SECTION = ParagraphStyle(
    "Section", fontName=BOLD_FONT, fontSize=11, leading=13,
    alignment=TA_LEFT, spaceBefore=10, spaceAfter=2,
)
_COMPANY = ParagraphStyle(
    "Company", fontName=BODY_FONT, fontSize=10.5, leading=13,
    alignment=TA_LEFT, spaceBefore=5, spaceAfter=1,
)
_BODY = ParagraphStyle(
    "Body", fontName=BODY_FONT, fontSize=10.5, leading=13.5,
    alignment=TA_LEFT, spaceBefore=1, spaceAfter=1,
)
_BULLET = ParagraphStyle(
    "Bullet", fontName=BODY_FONT, fontSize=10.5, leading=13.5,
    alignment=TA_LEFT, leftIndent=14, bulletIndent=2,
    spaceBefore=1, spaceAfter=1,
)


def _esc(text: str) -> str:
    """Escape XML-special chars — reportlab Paragraph parses markup."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Parsing (shared with the old docx renderer) ─────────────
KNOWN_HEADERS = {
    "summary", "objective", "profile", "about",
    "skills", "technical skills", "core competencies",
    "experience", "work experience", "professional experience",
    "education",
    "projects", "personal projects", "key projects",
    "certifications", "certificates", "awards"
}


def parse_cv(cv_text: str) -> dict:
    lines    = cv_text.strip().split("\n")
    sections = {}
    current  = "HEADER"
    buf      = []

    for line in lines:
        s     = line.strip()
        lower = s.lower().rstrip(":")
        if lower in KNOWN_HEADERS:
            sections[current] = buf
            current = lower.upper().rstrip(":")
            buf = []
        else:
            buf.append(s)

    sections[current] = buf
    return sections


def fmt_contact(lines: list) -> str:
    """Plain ' | '-joined contact line — no emoji/icons (ATS-safe)."""
    parts = [item.strip(" |,") for item in lines if item.strip(" |,")]
    return "  |  ".join(parts)


def parse_experience_blocks(lines: list) -> list:
    blocks  = []
    current = None

    for line in lines:
        if not line.strip():
            continue
        if re.search(r"\b(19|20)\d{2}\b", line) and not line.startswith("-"):
            if current:
                blocks.append(current)
            current = {"raw": line, "bullets": []}
        elif line.startswith("-") or line.startswith("•"):
            if current:
                current["bullets"].append(line)
            else:
                current = {"raw": "", "bullets": [line]}
        else:
            if current and not current["bullets"]:
                current["raw"] += " " + line
            elif current:
                current["bullets"].append(line)
            else:
                current = {"raw": line, "bullets": []}

    if current:
        blocks.append(current)
    return blocks


def split_company_line(raw: str):
    date_match = re.search(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|\d{4})[\w\s,\-–]+(?:Present|\d{4}))",
        raw, re.IGNORECASE
    )
    dates     = date_match.group(1).strip() if date_match else ""
    remainder = raw.replace(dates, "").strip(" |-,")
    parts     = re.split(r"\s*[-|,]\s*", remainder, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip(), dates
    return remainder.strip(), "", dates


SECTION_ORDER = [
    "SUMMARY", "OBJECTIVE", "PROFILE", "ABOUT",
    "EDUCATION",
    "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES",
    "EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE",
    "PROJECTS", "PERSONAL PROJECTS", "KEY PROJECTS",
    "CERTIFICATIONS", "CERTIFICATES", "AWARDS"
]


def _section_header(flow, title: str):
    flow.append(Paragraph(_esc(title.upper()), _SECTION))
    flow.append(HRFlowable(width="100%", thickness=0.75, color="black",
                           spaceBefore=1, spaceAfter=4))


def _company_line(flow, company: str, role: str, dates: str):
    bits = [f"<b>{_esc(company)}</b>"] if company else []
    if role:
        bits.append(_esc(role))
    if dates:
        bits.append(_esc(dates))
    flow.append(Paragraph("  |  ".join(bits), _COMPANY))


def _bullet(flow, text: str):
    clean = _esc(text.lstrip("-•* ").strip())
    flow.append(Paragraph(clean, _BULLET, bulletText="•"))


def generate_cv_pdf(cv_text: str, output_path: str, candidate_name: str = "") -> str:
    """Render cv_text to a single-column, ATS-friendly black-on-white PDF."""
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        title="Resume",
    )

    flow = []
    sections = parse_cv(cv_text)

    header_lines = [l for l in sections.get("HEADER", []) if l.strip()]
    name = candidate_name or (header_lines[0] if header_lines else "")

    if name:
        flow.append(Paragraph(_esc(name), _NAME))

    contact_str = fmt_contact(header_lines[1:] if header_lines else [])
    if contact_str:
        flow.append(Paragraph(_esc(contact_str), _CONTACT))
    else:
        flow.append(Spacer(1, 6))

    rendered = set()
    for key in SECTION_ORDER:
        if key in sections and key not in rendered:
            lines = [l for l in sections[key] if l.strip()]
            if not lines:
                continue
            rendered.add(key)

            title = key.title().replace("And", "and")
            _section_header(flow, title)

            if key in {"EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE"}:
                for block in parse_experience_blocks(lines):
                    if block["raw"].strip():
                        company, role, dates = split_company_line(block["raw"])
                        _company_line(flow, company, role, dates)
                    for b in block["bullets"]:
                        _bullet(flow, b)
            else:
                for line in lines:
                    if line.startswith(("-", "•", "*")):
                        _bullet(flow, line)
                    else:
                        flow.append(Paragraph(_esc(line), _BODY))

    doc.build(flow)
    return output_path


# Backwards-compatible alias (older imports called generate_cv_docx).
generate_cv_docx = generate_cv_pdf
