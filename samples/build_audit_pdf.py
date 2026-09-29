"""Renders backend/AUDIT_REPORT.md as backend/AUDIT_REPORT.pdf.

Run from the project root with the backend venv:
    backend/.venv/Scripts/python.exe samples/build_audit_pdf.py
"""

import html
import re
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Preformatted, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "backend" / "AUDIT_REPORT.md"
TARGET = ROOT / "backend" / "AUDIT_REPORT.pdf"

MAX_CODE_WIDTH = 112

BODY = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=9, leading=12, spaceAfter=4, textColor=colors.HexColor("#111111")
)
H1 = ParagraphStyle("H1", parent=BODY, fontName="Helvetica-Bold", fontSize=15, leading=18, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=BODY, fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=10, spaceAfter=5)
H3 = ParagraphStyle("H3", parent=BODY, fontName="Helvetica-Bold", fontSize=10, leading=13, spaceBefore=8, spaceAfter=3)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=12, bulletIndent=4, spaceAfter=2)
CODE = ParagraphStyle("Code", fontName="Courier", fontSize=7, leading=8.6, textColor=colors.HexColor("#222222"), spaceBefore=2, spaceAfter=6)


def _inline(text: str) -> str:
    """Escape HTML, then apply the inline markdown (bold and code spans) we use."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8">\1</font>', text)
    return text


def _wrapped_code(line: str) -> list[str]:
    """Split code lines that would overflow the printable width."""
    if len(line) <= MAX_CODE_WIDTH:
        return [line]
    return textwrap.wrap(line, width=MAX_CODE_WIDTH, subsequent_indent="    ", break_long_words=True, break_on_hyphens=False)


def render(source: Path, target: Path) -> None:
    """Convert the audit markdown to a platypus PDF."""
    flowables: list = []
    code_buffer: list[str] = []
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        if raw_line.strip().startswith("```"):
            if code_buffer:
                lines = [wrapped for buffered in code_buffer for wrapped in _wrapped_code(buffered)]
                flowables.append(Preformatted("\n".join(lines), CODE, maxLineLength=None))
                code_buffer = []
            continue
        if raw_line.startswith("```"):
            continue
        if raw_line.startswith("    ") and raw_line.strip():
            code_buffer.append(raw_line[4:])
            continue
        if code_buffer:
            lines = [wrapped for buffered in code_buffer for wrapped in _wrapped_code(buffered)]
            flowables.append(Preformatted("\n".join(lines), CODE, maxLineLength=None))
            code_buffer = []
        line = raw_line.rstrip()
        if not line:
            continue
        if line == "---":
            flowables.append(HRFlowable(width="100%", thickness=0.6, color=colors.grey, spaceBefore=6, spaceAfter=6))
        elif line.startswith("### "):
            flowables.append(Paragraph(_inline(line[4:]), H3))
        elif line.startswith("## "):
            flowables.append(Paragraph(_inline(line[3:]), H2))
        elif line.startswith("# "):
            flowables.append(Paragraph(_inline(line[2:]), H1))
        elif line.startswith("- "):
            flowables.append(Paragraph(_inline(line[2:]), BULLET, bulletText="•"))
        else:
            flowables.append(Paragraph(_inline(line), BODY))
    if code_buffer:
        lines = [wrapped for buffered in code_buffer for wrapped in _wrapped_code(buffered)]
        flowables.append(Preformatted("\n".join(lines), CODE, maxLineLength=None))

    document = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Verification and Hardening Pass — Evidence Report",
    )
    document.build(flowables)


def main() -> None:
    """Render the report PDF and report its page count."""
    render(SOURCE, TARGET)
    import pdfplumber

    with pdfplumber.open(TARGET) as pdf:
        print(f"wrote {TARGET} ({TARGET.stat().st_size} bytes, {len(pdf.pages)} pages)")


if __name__ == "__main__":
    main()
