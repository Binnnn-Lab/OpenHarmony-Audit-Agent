"""Small ReportLab renderer for the Markdown technical report."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape


def build_pdf(markdown_path: str | Path, output_path: str | Path, font_path: str = r"C:\Windows\Fonts\msyh.ttc") -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not Path(font_path).exists():
        raise FileNotFoundError(font_path)
    try:
        pdfmetrics.registerFont(TTFont("OHChinese", font_path, subfontIndex=0))
    except TypeError:
        pdfmetrics.registerFont(TTFont("OHChinese", font_path))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="OHTitle", parent=styles["Title"], fontName="OHChinese", fontSize=20, leading=28, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=16))
    styles.add(ParagraphStyle(name="OHHeading", parent=styles["Heading2"], fontName="OHChinese", fontSize=14, leading=20, textColor=colors.HexColor("#17365D"), spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="OHBody", parent=styles["BodyText"], fontName="OHChinese", fontSize=9.5, leading=15, spaceAfter=6))
    styles.add(ParagraphStyle(name="OHCode", parent=styles["Code"], fontName="OHChinese", fontSize=8, leading=11, backColor=colors.HexColor("#F3F6FA"), borderPadding=5, spaceAfter=7))
    story = []
    for raw in Path(markdown_path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["OHTitle"]))
        elif line.startswith("## ") or line.startswith("### "):
            heading = line.lstrip("#").strip()
            story.append(Paragraph(escape(heading), styles["OHHeading"]))
        elif line.startswith("```"):
            continue
        elif line.startswith("|") or line.startswith(">") or line.startswith("-") or line.startswith("*"):
            text = re.sub(r"^[-*>| ]+", "", line).replace("|", " · ")
            if text and not set(text) <= {"-", "·", " "}:
                story.append(Paragraph(escape(text), styles["OHBody"]))
        elif line.startswith("!["):
            story.append(Paragraph("架构图见 docs/architecture.mmd。", styles["OHBody"]))
        else:
            story.append(Paragraph(escape(line).replace("`", ""), styles["OHBody"]))
    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title="OpenHarmony-Audit-Agent 技术方案")
    doc.build(story)
    return target

