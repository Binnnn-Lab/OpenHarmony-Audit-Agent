"""Render the project's Markdown manuals, including tables and code, to PDF."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape


def build_pdf(markdown_path: str | Path, output_path: str | Path, font_path: str = r"C:\Windows\Fonts\msyh.ttc") -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not Path(font_path).is_file():
        raise FileNotFoundError(f"Specify an installed Chinese TrueType font: {font_path}")
    pdfmetrics.registerFont(TTFont("OHChinese", font_path, subfontIndex=0))
    pdfmetrics.registerFontFamily("OHChinese", normal="OHChinese", bold="OHChinese", italic="OHChinese", boldItalic="OHChinese")
    ink, accent, muted = (colors.HexColor(c) for c in ("#20353C", "#23624E", "#596D67"))
    base = dict(fontName="OHChinese", textColor=ink, wordWrap="CJK", splitLongWords=True)
    body = ParagraphStyle("body", fontSize=9.5, leading=16, spaceAfter=7, **base)
    title_style = ParagraphStyle("title", fontSize=21, leading=31, spaceBefore=12, spaceAfter=18, **base)
    heading = ParagraphStyle("heading", fontSize=13, leading=20, spaceBefore=15, spaceAfter=8, keepWithNext=True, **base)
    code_style = ParagraphStyle("code", fontSize=8, leading=12, spaceAfter=3, backColor=colors.HexColor("#EDF2EF"), borderPadding=4, **base)
    cell_style = ParagraphStyle("cell", fontSize=8, leading=13, **base)
    label_style = ParagraphStyle("label", fontSize=8, leading=12, textColor=accent, fontName="OHChinese")

    def inline(text):
        text = escape(text.strip())
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
        text = re.sub(r"`([^`]+)`", r'<font color="#23624E">\1</font>', text)
        return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    lines = Path(markdown_path).read_text(encoding="utf-8").splitlines()
    title = next((line[2:] for line in lines if line.startswith("# ")), Path(markdown_path).stem)
    story = [Paragraph("OPENHARMONY AUDIT AGENT / 题目一交付资料", label_style)]
    width = A4[0] - 36 * mm
    i, in_code = 0, False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if line.startswith("```"):
            in_code = not in_code
            story.append(Spacer(1, 5))
        elif in_code:
            story.append(Paragraph(escape(lines[i - 1]).replace(" ", "&#160;"), code_style))
        elif not line:
            continue
        elif line.startswith("# "):
            title_text = inline(line[2:]).replace("OpenHarmony-Audit-Agent ", "OpenHarmony-Audit-Agent<br/>", 1)
            story.append(Paragraph(title_text, title_style))
        elif line.startswith("##"):
            story.append(Paragraph(inline(line.lstrip("# ")), heading))
        elif line.startswith("|"):
            rows = [line]
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            rows = [r for r in rows if not re.fullmatch(r"[|\s:-]+", r)]
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            columns = len(cells[0])
            ratios = {2: [0.30, 0.70], 3: [0.20, 0.34, 0.46]}.get(columns, [1 / columns] * columns)
            table = Table([[Paragraph(inline(c), cell_style) for c in row] for row in cells],
                          colWidths=[width * r for r in ratios], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DEEAE2")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F4")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#AAC4B7")),
            ]))
            story.extend([table, Spacer(1, 9)])
        elif line.startswith("!["):
            story.append(Paragraph("架构图源文件：docs/architecture.mmd。", body))
        else:
            text = ("• " + line[2:]) if line.startswith("- ") else line.removeprefix("> ")
            story.append(Paragraph(inline(text), body))

    def page_decoration(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C6D6CD"))
        canvas.line(18 * mm, 17 * mm, A4[0] - 18 * mm, 17 * mm)
        canvas.setFont("OHChinese", 7)
        canvas.setFillColor(muted)
        canvas.drawString(18 * mm, 12 * mm, "OpenHarmony-Audit-Agent · 源码审计 / 按需辅助验证")
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=23 * mm, title=title,
                            author="", subject="题目一工程交付材料")
    doc.build(story, onFirstPage=page_decoration, onLaterPages=page_decoration)
    return target
