from __future__ import annotations

"""
UW Companion Documentation Generator
=====================================
Generates a comprehensive PDF documentation for the UW Companion project
using reportlab.

Usage:
    python3 docs/generate_docs.py

Output:
    docs/UW_Companion_Documentation.pdf
"""

import os
from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    ListFlowable,
    ListItem,
    HRFlowable,
    Image,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.pdfgen.canvas import Canvas

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
AIG_BLUE = HexColor("#00205B")
AIG_BLUE_LIGHT = HexColor("#1A3A6B")
AIG_BLUE_LIGHTER = HexColor("#E8EDF5")
ACCENT_TEAL = HexColor("#0088A9")
ACCENT_GREEN = HexColor("#2E7D32")
ACCENT_AMBER = HexColor("#F57F17")
ACCENT_RED = HexColor("#C62828")
TEXT_PRIMARY = HexColor("#1A1A2E")
TEXT_SECONDARY = HexColor("#4A4A6A")
LIGHT_GREY = HexColor("#F4F6F9")
BORDER_GREY = HexColor("#D0D5DD")
CODE_BG = HexColor("#F8F9FB")
WHITE = white
BLACK = black

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PDF = SCRIPT_DIR / "UW_Companion_Documentation.pdf"


# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------
class SectionDivider(Flowable):
    """A thin horizontal divider with AIG blue accent."""

    def __init__(self, width: float = 500, color: Color = AIG_BLUE, thickness: float = 1.5):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self._fixedWidth = width
        self._fixedHeight = 8

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 4, self.width, 4)

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (self.width, self._fixedHeight)


class BoxCallout(Flowable):
    """A coloured callout box with left border accent."""

    def __init__(
        self,
        text: str,
        width: float = 460,
        bg: Color = AIG_BLUE_LIGHTER,
        accent: Color = AIG_BLUE,
        font_name: str = "Helvetica",
        font_size: float = 9,
    ):
        super().__init__()
        self._text = text
        self._width = width
        self._bg = bg
        self._accent = accent
        self._font_name = font_name
        self._font_size = font_size
        self._padding = 12
        self._accent_width = 4
        self._calculated_height: float = 0

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        inner_width = self._width - self._padding * 2 - self._accent_width
        # Estimate line count
        avg_char_width = self._font_size * 0.52
        chars_per_line = max(1, int(inner_width / avg_char_width))
        num_lines = max(1, len(self._text) // chars_per_line + 1)
        self._calculated_height = max(40, num_lines * (self._font_size + 4) + self._padding * 2)
        return (self._width, self._calculated_height)

    def draw(self) -> None:
        c = self.canv
        h = self._calculated_height
        w = self._width

        # Background
        c.setFillColor(self._bg)
        c.setStrokeColor(self._bg)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=0)

        # Accent bar
        c.setFillColor(self._accent)
        c.rect(0, 0, self._accent_width, h, fill=1, stroke=0)

        # Text
        c.setFillColor(TEXT_PRIMARY)
        c.setFont(self._font_name, self._font_size)
        text_obj = c.beginText(
            self._accent_width + self._padding,
            h - self._padding - self._font_size,
        )
        text_obj.setFont(self._font_name, self._font_size)
        text_obj.setLeading(self._font_size + 4)

        inner_width = w - self._padding * 2 - self._accent_width
        avg_char_width = self._font_size * 0.52
        chars_per_line = max(1, int(inner_width / avg_char_width))

        words = self._text.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if len(test) > chars_per_line:
                text_obj.textLine(line)
                line = word
            else:
                line = test
        if line:
            text_obj.textLine(line)

        c.drawText(text_obj)


class ArchitectureDiagram(Flowable):
    """A diagram showing the RAG pipeline flow."""

    def __init__(self, width: float = 480, height: float = 320):
        super().__init__()
        self._width = width
        self._height = height

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (self._width, self._height)

    def draw(self) -> None:
        c = self.canv
        w = self._width
        h = self._height

        # Background
        c.setFillColor(HexColor("#FAFBFD"))
        c.setStrokeColor(BORDER_GREY)
        c.setLineWidth(1)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(AIG_BLUE)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, h - 22, "RAG Pipeline Architecture")

        # ----- Define boxes -----
        box_h = 36
        box_w = 110
        small_w = 100

        # Row positions (from top)
        row1_y = h - 75
        row2_y = h - 140
        row3_y = h - 205
        row4_y = h - 270

        def draw_box(
            x: float,
            y: float,
            bw: float,
            bh: float,
            label: str,
            sublabel: str = "",
            bg: Color = AIG_BLUE,
            fg: Color = WHITE,
        ) -> None:
            c.setFillColor(bg)
            c.setStrokeColor(HexColor("#B0B8C8"))
            c.setLineWidth(0.8)
            c.roundRect(x, y, bw, bh, 5, fill=1, stroke=1)
            c.setFillColor(fg)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x + bw / 2, y + bh / 2 + (4 if sublabel else 0), label)
            if sublabel:
                c.setFont("Helvetica", 6.5)
                c.drawCentredString(x + bw / 2, y + bh / 2 - 8, sublabel)

        def draw_arrow_down(x: float, y_from: float, y_to: float) -> None:
            c.setStrokeColor(TEXT_SECONDARY)
            c.setLineWidth(1.2)
            c.line(x, y_from, x, y_to + 6)
            # Arrowhead
            c.setFillColor(TEXT_SECONDARY)
            arrow_size = 4
            p = c.beginPath()
            p.moveTo(x, y_to)
            p.lineTo(x - arrow_size, y_to + arrow_size * 1.5)
            p.lineTo(x + arrow_size, y_to + arrow_size * 1.5)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        def draw_arrow_right(x_from: float, x_to: float, y: float) -> None:
            c.setStrokeColor(TEXT_SECONDARY)
            c.setLineWidth(1.2)
            c.line(x_from, y, x_to - 6, y)
            c.setFillColor(TEXT_SECONDARY)
            arrow_size = 4
            p = c.beginPath()
            p.moveTo(x_to, y)
            p.lineTo(x_to - arrow_size * 1.5, y - arrow_size)
            p.lineTo(x_to - arrow_size * 1.5, y + arrow_size)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        # --- Row 1: Frontend + Upload ---
        fe_x = 30
        draw_box(fe_x, row1_y, box_w + 20, box_h, "Angular 18 Frontend", "Tailwind CSS + Lucide", bg=ACCENT_TEAL)

        upload_x = fe_x + box_w + 50
        draw_box(upload_x, row1_y, box_w, box_h, "FastAPI Backend", "REST API", bg=AIG_BLUE)

        draw_arrow_right(fe_x + box_w + 20, upload_x, row1_y + box_h / 2)

        # --- Row 2: Parsing -> Chunking -> Embedding ---
        gap = 20
        total_3 = small_w * 3 + gap * 2
        start_x = (w - total_3) / 2

        parse_x = start_x
        chunk_x = start_x + small_w + gap
        embed_x = start_x + (small_w + gap) * 2

        draw_box(parse_x, row2_y, small_w, box_h, "Parsing Layer", "PDF / DOCX", bg=AIG_BLUE_LIGHT)
        draw_box(chunk_x, row2_y, small_w, box_h, "Chunking Layer", "Section-aware", bg=AIG_BLUE_LIGHT)
        draw_box(embed_x, row2_y, small_w, box_h, "Embedding Layer", "Gemini 001", bg=AIG_BLUE_LIGHT)

        draw_arrow_right(parse_x + small_w, chunk_x, row2_y + box_h / 2)
        draw_arrow_right(chunk_x + small_w, embed_x, row2_y + box_h / 2)

        # Arrow from backend to parsing
        draw_arrow_down(upload_x + box_w / 2, row1_y, row2_y + box_h)

        # --- Row 3: VectorDB (center) ---
        vdb_w = 130
        vdb_x = (w - vdb_w) / 2
        draw_box(vdb_x, row3_y, vdb_w, box_h, "LanceDB Vector Store", "Cosine Similarity", bg=HexColor("#2E5090"))

        draw_arrow_down(embed_x + small_w / 2, row2_y, row3_y + box_h)

        # --- Row 4: Generation + Hallucination + Actions ---
        total_3b = small_w * 3 + gap * 2
        start_x2 = (w - total_3b) / 2

        gen_x = start_x2
        hall_x = start_x2 + small_w + gap
        act_x = start_x2 + (small_w + gap) * 2

        draw_box(gen_x, row4_y, small_w, box_h, "Generation Layer", "Gemini 2.0 Flash", bg=AIG_BLUE_LIGHT)
        draw_box(hall_x, row4_y, small_w, box_h, "Hallucination", "4-Factor Scoring", bg=ACCENT_AMBER, fg=BLACK)
        draw_box(act_x, row4_y, small_w, box_h, "Actions Layer", "UW Workflow", bg=ACCENT_GREEN, fg=WHITE)

        draw_arrow_down(vdb_x + vdb_w / 2, row3_y, row4_y + box_h)

        draw_arrow_right(gen_x + small_w, hall_x, row4_y + box_h / 2)
        draw_arrow_right(hall_x + small_w, act_x, row4_y + box_h / 2)

        # Arrow from VectorDB up to query path (label)
        c.setFillColor(TEXT_SECONDARY)
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(w / 2, row3_y - 4, "Retrieval + Context Injection")


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["Title"] = ParagraphStyle(
        "DocTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=30,
        textColor=AIG_BLUE,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=36,
    )

    styles["Subtitle"] = ParagraphStyle(
        "DocSubtitle",
        fontName="Helvetica",
        fontSize=14,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=18,
    )

    styles["VersionDate"] = ParagraphStyle(
        "VersionDate",
        fontName="Helvetica",
        fontSize=11,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=2,
        leading=15,
    )

    styles["Heading1"] = ParagraphStyle(
        "DocH1",
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=AIG_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        leading=26,
    )

    styles["Heading2"] = ParagraphStyle(
        "DocH2",
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=AIG_BLUE_LIGHT,
        spaceBefore=14,
        spaceAfter=8,
        leading=20,
    )

    styles["Heading3"] = ParagraphStyle(
        "DocH3",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=TEXT_PRIMARY,
        spaceBefore=10,
        spaceAfter=6,
        leading=16,
    )

    styles["Body"] = ParagraphStyle(
        "DocBody",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_PRIMARY,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=6,
        leading=14.5,
    )

    styles["BodyBold"] = ParagraphStyle(
        "DocBodyBold",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=TEXT_PRIMARY,
        spaceBefore=2,
        spaceAfter=4,
        leading=14,
    )

    styles["Bullet"] = ParagraphStyle(
        "DocBullet",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_PRIMARY,
        leftIndent=20,
        bulletIndent=8,
        spaceBefore=2,
        spaceAfter=2,
        leading=14,
    )

    styles["SubBullet"] = ParagraphStyle(
        "DocSubBullet",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=TEXT_SECONDARY,
        leftIndent=36,
        bulletIndent=24,
        spaceBefore=1,
        spaceAfter=1,
        leading=13,
    )

    styles["Code"] = ParagraphStyle(
        "DocCode",
        fontName="Courier",
        fontSize=9,
        textColor=TEXT_PRIMARY,
        backColor=CODE_BG,
        leftIndent=12,
        rightIndent=12,
        spaceBefore=4,
        spaceAfter=4,
        leading=13,
        borderColor=BORDER_GREY,
        borderWidth=0.5,
        borderPadding=6,
    )

    styles["TOCEntry"] = ParagraphStyle(
        "TOCEntry",
        fontName="Helvetica",
        fontSize=11,
        textColor=AIG_BLUE,
        spaceBefore=4,
        spaceAfter=4,
        leading=16,
        leftIndent=16,
    )

    styles["TOCSubEntry"] = ParagraphStyle(
        "TOCSubEntry",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_SECONDARY,
        spaceBefore=2,
        spaceAfter=2,
        leading=14,
        leftIndent=32,
    )

    styles["TableHeader"] = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_LEFT,
        leading=12,
    )

    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=9,
        textColor=TEXT_PRIMARY,
        alignment=TA_LEFT,
        leading=12,
        wordWrap="LTR",
    )

    styles["TableCellCode"] = ParagraphStyle(
        "TableCellCode",
        fontName="Courier",
        fontSize=8,
        textColor=TEXT_PRIMARY,
        alignment=TA_LEFT,
        leading=11,
    )

    styles["Footer"] = ParagraphStyle(
        "Footer",
        fontName="Helvetica",
        fontSize=8,
        textColor=TEXT_SECONDARY,
        alignment=TA_CENTER,
    )

    return styles


# ---------------------------------------------------------------------------
# Page template callbacks
# ---------------------------------------------------------------------------
def _header_footer(canvas: Canvas, doc: SimpleDocTemplate) -> None:
    canvas.saveState()
    w, h = letter

    # Header line
    canvas.setStrokeColor(AIG_BLUE)
    canvas.setLineWidth(1.5)
    canvas.line(40, h - 40, w - 40, h - 40)

    # Header text
    canvas.setFillColor(AIG_BLUE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(40, h - 35, "UW Companion")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_SECONDARY)
    canvas.drawRightString(w - 40, h - 35, "Technical Documentation v1.0")

    # Footer
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(40, 38, w - 40, 38)
    canvas.setFillColor(TEXT_SECONDARY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 24, f"Page {doc.page}")
    canvas.drawString(40, 24, "Confidential")
    canvas.drawRightString(w - 40, 24, "AIG - Commercial Insurance")

    canvas.restoreState()


def _title_page_template(canvas: Canvas, doc: SimpleDocTemplate) -> None:
    """Minimal header/footer for the title page."""
    canvas.saveState()
    w, h = letter

    # Decorative top bar
    canvas.setFillColor(AIG_BLUE)
    canvas.rect(0, h - 8, w, 8, fill=1, stroke=0)

    # Bottom accent bar
    canvas.setFillColor(AIG_BLUE)
    canvas.rect(0, 0, w, 4, fill=1, stroke=0)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Helper functions for content building
# ---------------------------------------------------------------------------
def bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"\u2022  {text}", styles["Bullet"])


def sub_bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"\u2013  {text}", styles["SubBullet"])


def make_table(
    headers: list[str],
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    col_widths: list[float] | None = None,
) -> Table:
    header_cells = [Paragraph(h, styles["TableHeader"]) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(cell, styles["TableCell"]) for cell in row])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AIG_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
                ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_PRIMARY),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


# ---------------------------------------------------------------------------
# Build document content
# ---------------------------------------------------------------------------
def build_content(styles: dict[str, ParagraphStyle]) -> list:
    story: list = []

    # ==================================================================
    # TITLE PAGE
    # ==================================================================
    story.append(Spacer(1, 120))
    story.append(Paragraph("UW Companion", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "AI-Powered Underwriting Assistant",
            styles["Subtitle"],
        )
    )
    story.append(Spacer(1, 24))
    story.append(SectionDivider(width=200, color=ACCENT_TEAL, thickness=2))
    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            "Intelligent Document Analysis for Commercial Insurance Underwriters",
            ParagraphStyle(
                "tagline",
                fontName="Helvetica",
                fontSize=12,
                textColor=TEXT_SECONDARY,
                alignment=TA_CENTER,
                leading=16,
            ),
        )
    )
    story.append(Spacer(1, 40))
    story.append(Paragraph("Version 1.0", styles["VersionDate"]))
    story.append(Paragraph(date.today().strftime("%B %d, %Y"), styles["VersionDate"]))
    story.append(Spacer(1, 30))
    story.append(
        Paragraph(
            "RAG-Powered \u2022 Hallucination Detection \u2022 Action Extraction",
            ParagraphStyle(
                "badges",
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=ACCENT_TEAL,
                alignment=TA_CENTER,
                leading=14,
            ),
        )
    )
    story.append(Spacer(1, 60))
    story.append(
        Paragraph(
            "AIG \u2014 Commercial Insurance Technology",
            ParagraphStyle(
                "orgline",
                fontName="Helvetica",
                fontSize=10,
                textColor=TEXT_SECONDARY,
                alignment=TA_CENTER,
            ),
        )
    )

    story.append(PageBreak())

    # ==================================================================
    # TABLE OF CONTENTS
    # ==================================================================
    story.append(Paragraph("Table of Contents", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 10))

    toc_entries = [
        ("1", "Overview"),
        ("2", "Architecture Overview"),
        ("3", "Layer Architecture"),
        ("", "3.1  Parsing Layer"),
        ("", "3.2  Chunking Layer"),
        ("", "3.3  Embedding Layer"),
        ("", "3.4  Vectorization Layer"),
        ("", "3.5  Generation Layer"),
        ("", "3.6  Hallucination Detection Layer"),
        ("", "3.7  Actions Layer"),
        ("4", "Hallucination Detection Algorithm"),
        ("5", "API Reference"),
        ("6", "Frontend Features"),
        ("7", "Configuration Reference"),
        ("8", "Setup &amp; Running"),
        ("9", "Feature List"),
        ("10", "Testing"),
    ]
    for num, title in toc_entries:
        if num:
            story.append(Paragraph(f"<b>{num}.</b>  {title}", styles["TOCEntry"]))
        else:
            story.append(Paragraph(title, styles["TOCSubEntry"]))

    story.append(PageBreak())

    # ==================================================================
    # 1. OVERVIEW
    # ==================================================================
    story.append(Paragraph("1. Overview", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "UW Companion is an AI-powered document analysis platform designed specifically for "
            "commercial insurance underwriters. It enables underwriters to upload policy documents "
            "(PDF and DOCX), ask natural-language questions about document contents, and receive "
            "accurate, source-cited answers with built-in hallucination detection and automated "
            "underwriting action extraction.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The system employs a Retrieval-Augmented Generation (RAG) architecture, combining "
            "vector similarity search over LanceDB with Google Gemini large language models to "
            "deliver grounded, trustworthy responses. Every AI-generated answer is accompanied "
            "by a multi-factor hallucination score that quantifies how well the response is "
            "supported by the source documents.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("Key Capabilities", styles["Heading3"]))
    capabilities = [
        "<b>Document Ingestion</b> \u2014 Parse PDF and DOCX files, extract text with page provenance",
        "<b>Smart Chunking</b> \u2014 Section-aware document splitting with configurable overlap",
        "<b>Vector Search</b> \u2014 Semantic similarity search using Gemini embeddings and LanceDB",
        "<b>RAG Chat</b> \u2014 Contextual question-answering grounded in uploaded documents",
        "<b>Hallucination Detection</b> \u2014 4-factor scoring system for response trustworthiness",
        "<b>Action Extraction</b> \u2014 Automated identification of underwriting actions with priorities",
        "<b>Source Citations</b> \u2014 Every claim linked back to specific documents and page numbers",
    ]
    for cap in capabilities:
        story.append(bullet(cap, styles))

    story.append(PageBreak())

    # ==================================================================
    # 2. ARCHITECTURE OVERVIEW
    # ==================================================================
    story.append(Paragraph("2. Architecture Overview", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "UW Companion follows a clean separation between the frontend presentation layer "
            "and a Python backend that implements the RAG pipeline as a series of composable layers.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 6))

    # Technology stack table
    story.append(Paragraph("Technology Stack", styles["Heading3"]))
    stack_table = make_table(
        headers=["Component", "Technology", "Details"],
        rows=[
            ["Frontend", "Angular 18", "Standalone components, Tailwind CSS v4, Lucide icons"],
            ["Backend", "Python FastAPI", "Async REST API with layered architecture"],
            ["Vector Database", "LanceDB", "In-memory / file-based vector store, cosine similarity"],
            ["Chat LLM", "Google Gemini 2.0 Flash", "Fast, high-quality generative model"],
            ["Embeddings", "Gemini Embedding 001", "3072-dimensional vectors, separate task types"],
            ["PDF Parsing", "PyPDF2", "Page-by-page text extraction"],
            ["DOCX Parsing", "python-docx", "Paragraph and table extraction with synthetic pages"],
            ["Validation", "Pydantic v2", "Request/response schema validation"],
        ],
        styles=styles,
        col_widths=[100, 130, 250],
    )
    story.append(stack_table)
    story.append(Spacer(1, 16))

    # Architecture Diagram
    story.append(Paragraph("RAG Pipeline Flow", styles["Heading3"]))
    story.append(Spacer(1, 4))
    story.append(ArchitectureDiagram(width=480, height=310))

    story.append(Spacer(1, 12))
    story.append(
        BoxCallout(
            "The RAG pipeline processes documents through six sequential layers: "
            "Parsing -> Chunking -> Embedding -> Vectorization (storage). At query time, "
            "the pipeline performs embedding -> vector search -> generation -> hallucination "
            "analysis -> action extraction. Each layer is independently testable and replaceable.",
            width=480,
            bg=AIG_BLUE_LIGHTER,
            accent=AIG_BLUE,
        )
    )

    story.append(PageBreak())

    # ==================================================================
    # 3. LAYER ARCHITECTURE
    # ==================================================================
    story.append(Paragraph("3. Layer Architecture", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "The backend is organized into seven discrete layers, each with a single responsibility. "
            "Layers communicate through well-defined interfaces (Python dicts and Pydantic models), "
            "enabling independent development, testing, and replacement.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    # --- 3.1 Parsing Layer ---
    story.append(Paragraph("3.1  Parsing Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/parsing/parser.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> Document Ingestion Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Parsing Layer is the entry point for document ingestion. It accepts file paths "
            "for PDF and DOCX documents and extracts structured text with page-level provenance. "
            "Each page is returned as a (page_number, text) tuple, preserving the association "
            "between content and its location in the original document.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Capabilities:", styles["BodyBold"]))
    parsing_bullets = [
        "<b>PDF Parsing</b> (PyPDF2) \u2014 Iterates through pages, extracts text per page, "
        "filters empty pages, returns list of (page_num, text) tuples",
        "<b>DOCX Parsing</b> (python-docx) \u2014 Extracts paragraphs and table cell content, "
        "synthesizes page boundaries (40 paragraphs per page) since DOCX lacks native pages",
        "<b>Auto-detection</b> \u2014 The <font face='Courier' size='9'>parse_document()</font> "
        "function detects format by file extension and dispatches to the correct parser",
    ]
    for b in parsing_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Interface:</b> <font face='Courier' size='9'>parse_document(filepath: str) "
            "\u2192 list[tuple[int, str]]</font>",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    # --- 3.2 Chunking Layer ---
    story.append(Paragraph("3.2  Chunking Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/chunking/chunker.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> NLP / Document Processing Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Chunking Layer splits parsed document text into semantically meaningful pieces "
            "sized for embedding and retrieval. It employs a section-aware strategy that preserves "
            "the logical structure of underwriting documents.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Chunking Strategy (in order of precedence):", styles["BodyBold"]))
    chunking_bullets = [
        "<b>Section header detection</b> \u2014 Recognizes patterns like SECTION, PART, ARTICLE, "
        "SCHEDULE, ENDORSEMENT, Roman numerals, and numbered headings",
        "<b>Paragraph-level splitting</b> \u2014 Falls back to paragraph boundaries for non-sectioned text",
        "<b>Recursive sentence splitting</b> \u2014 For oversized chunks, recursively splits at sentence "
        "boundaries to maintain coherence",
        "<b>Overlap injection</b> \u2014 Appends trailing tokens from the previous chunk to maintain "
        "context continuity across chunk boundaries",
    ]
    for b in chunking_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 4))

    chunk_config_table = make_table(
        headers=["Parameter", "Default", "Description"],
        rows=[
            ["CHUNK_SIZE", "512 tokens", "Maximum number of tokens per chunk"],
            ["CHUNK_OVERLAP", "64 tokens", "Number of trailing tokens carried into the next chunk"],
        ],
        styles=styles,
        col_widths=[130, 100, 250],
    )
    story.append(chunk_config_table)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Output:</b> <font face='Courier' size='9'>list[Chunk]</font> "
            "where each Chunk contains chunk_id, text, source filename, page number, "
            "section header, and token estimate.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    # --- 3.3 Embedding Layer ---
    story.append(Paragraph("3.3  Embedding Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/embedding/gemini_embedder.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> ML / Embeddings Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Embedding Layer converts text into high-dimensional vector representations using "
            "Google's Gemini Embedding 001 model. It supports batch processing for efficient "
            "document indexing and uses differentiated task types for optimal retrieval quality.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))

    embed_table = make_table(
        headers=["Property", "Value"],
        rows=[
            ["Model", "models/gemini-embedding-001"],
            ["Vector Dimensions", "3072"],
            ["Batch Size", "100 texts per API call"],
            ["Document Task Type", "retrieval_document (for indexing)"],
            ["Query Task Type", "retrieval_query (for search queries)"],
        ],
        styles=styles,
        col_widths=[160, 320],
    )
    story.append(embed_table)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Using separate task types (<font face='Courier' size='9'>retrieval_document</font> "
            "vs <font face='Courier' size='9'>retrieval_query</font>) is critical for optimal "
            "retrieval performance. The embedding model optimizes vectors differently based on "
            "whether the text will be stored (document) or used for searching (query).",
            styles["Body"],
        )
    )

    story.append(PageBreak())

    # --- 3.4 Vectorization Layer ---
    story.append(Paragraph("3.4  Vectorization Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/vectorization/lance_store.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> Data Infrastructure Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Vectorization Layer manages the LanceDB vector store. It handles chunk storage "
            "with embeddings, similarity search at query time, and document lifecycle management "
            "(add, list, delete). LanceDB operates as a file-based store in <font face='Courier' "
            "size='9'>/tmp/uw_companion_lancedb</font>.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Core Operations:", styles["BodyBold"]))
    vec_bullets = [
        "<b>store_chunks()</b> \u2014 Embeds text chunks, creates vector records with metadata "
        "(chunk_id, text, source, page, section, document_id), upserts into LanceDB",
        "<b>search()</b> \u2014 Embeds the query using retrieval_query task type, performs "
        "cosine similarity search, returns top-K results with similarity scores",
        "<b>get_all_documents()</b> \u2014 Returns metadata for all indexed documents",
        "<b>delete_document()</b> \u2014 Removes all chunks belonging to a document by document_id",
    ]
    for b in vec_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 4))

    vec_cfg = make_table(
        headers=["Parameter", "Default", "Description"],
        rows=[
            ["LANCE_DB_PATH", "/tmp/uw_companion_lancedb", "Path to LanceDB storage directory"],
            ["LANCE_TABLE_NAME", "document_chunks", "Name of the LanceDB table"],
            ["TOP_K_RESULTS", "8", "Number of chunks returned per search query"],
        ],
        styles=styles,
        col_widths=[130, 160, 190],
    )
    story.append(vec_cfg)
    story.append(Spacer(1, 10))

    # --- 3.5 Generation Layer ---
    story.append(Paragraph("3.5  Generation Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/generation/rag_generator.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> AI / LLM Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Generation Layer constructs prompts from retrieved document chunks and chat history, "
            "then generates responses using Google Gemini 2.0 Flash. It also provides action "
            "extraction prompts for the Actions Layer.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Functions:", styles["BodyBold"]))
    gen_bullets = [
        "<b>generate_rag_response()</b> \u2014 Builds a system prompt with underwriting expert "
        "persona, injects document context with source citations, includes chat history for "
        "multi-turn conversations, enforces rules (cite sources, no approximation, flag risks)",
        "<b>extract_actions_prompt()</b> \u2014 Generates a structured JSON extraction prompt "
        "requesting UW actions with categories (coverage_gap, risk_flag, endorsement, compliance, "
        "pricing) and priority levels",
    ]
    for b in gen_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The system prompt enforces strict grounding: the model must answer ONLY from provided "
            "context, cite specific sources and pages, use exact numbers, and explicitly flag when "
            "information is not available in the documents.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    # --- 3.6 Hallucination Layer ---
    story.append(Paragraph("3.6  Hallucination Detection Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/hallucination/detector.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> AI Safety / Trust Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Hallucination Detection Layer is the trust and safety backbone of UW Companion. "
            "It evaluates every AI response using a 4-factor scoring system to quantify how well "
            "the response is grounded in the source documents. The output is a detailed report "
            "including per-sentence grounding analysis and flagged claims.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "See Section 4 for the full algorithm specification.",
            ParagraphStyle(
                "italicnote",
                fontName="Helvetica-Oblique",
                fontSize=10,
                textColor=TEXT_SECONDARY,
                leading=14,
            ),
        )
    )

    story.append(PageBreak())

    # --- 3.7 Actions Layer ---
    story.append(Paragraph("3.7  Actions Layer", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Location:</b> <font face='Courier' size='9'>layers/actions/extractor.py</font>"
            "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
            "<b>Team:</b> Underwriting Workflow Team",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The Actions Layer extracts structured underwriting actions from AI analysis results. "
            "It uses Gemini to identify actionable items from the conversation context and parses "
            "them into validated UWAction objects.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Action Schema:", styles["BodyBold"]))

    action_schema_table = make_table(
        headers=["Field", "Type", "Values / Description"],
        rows=[
            ["action", "string", "Short description of what the underwriter should do"],
            ["category", "enum", "coverage_gap, risk_flag, endorsement, compliance, pricing"],
            ["priority", "enum", "critical, high, medium, low"],
            ["details", "string", "1-2 sentence explanation of the action"],
            ["source_reference", "string", "Document and page the action relates to"],
        ],
        styles=styles,
        col_widths=[110, 70, 300],
    )
    story.append(action_schema_table)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "The extraction uses Gemini to generate a JSON array of actions, which is then parsed "
            "and validated. Invalid categories or priorities are automatically corrected to safe "
            "defaults (risk_flag / medium). Markdown code fences in the LLM output are stripped "
            "before JSON parsing.",
            styles["Body"],
        )
    )

    story.append(PageBreak())

    # ==================================================================
    # 4. HALLUCINATION DETECTION ALGORITHM
    # ==================================================================
    story.append(Paragraph("4. Hallucination Detection Algorithm", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Every AI-generated response is scored on four complementary factors. The final "
            "hallucination score (0\u2013100) is a weighted combination of these factors, where "
            "higher scores indicate greater trustworthiness.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    # Factor 1
    story.append(Paragraph("Factor 1: Retrieval Confidence", styles["Heading3"]))
    story.append(
        Paragraph("<b>Weight: 0.25 (25%)</b>", styles["Body"])
    )
    story.append(
        Paragraph(
            "Measures the quality of the retrieved document chunks used to generate the response. "
            "Computed as a position-weighted average of chunk similarity scores \u2014 earlier "
            "(more relevant) chunks receive higher weight. The weighting formula uses "
            "<font face='Courier' size='9'>weight[i] = 1 / (i + 1)</font> for the i-th chunk. "
            "The result is clamped to [0, 100].",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 6))

    # Factor 2
    story.append(Paragraph("Factor 2: Response Grounding", styles["Heading3"]))
    story.append(
        Paragraph("<b>Weight: 0.35 (35%)</b> \u2014 Heaviest factor", styles["Body"])
    )
    story.append(
        Paragraph(
            "The most important factor. Evaluates each sentence in the AI response individually "
            "by computing its embedding similarity against all source chunks. For each sentence, "
            "the best matching source is identified. A sentence is considered <b>grounded</b> if "
            "its similarity exceeds the threshold of <b>0.65</b>. The per-sentence score is "
            "normalized as <font face='Courier' size='9'>min(1.0, similarity / 0.8) * 100</font>. "
            "The factor score is the average across all sentences.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Ungrounded sentences (below threshold) are collected into the "
            "<font face='Courier' size='9'>flagged_claims</font> list for underwriter review.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 6))

    # Factor 3
    story.append(Paragraph("Factor 3: Numerical Fidelity", styles["Heading3"]))
    story.append(
        Paragraph("<b>Weight: 0.20 (20%)</b>", styles["Body"])
    )
    story.append(
        Paragraph(
            "Checks whether numerical values in the AI response (dollar amounts, percentages, "
            "plain numbers, formatted numbers) can be found in the source documents. Uses regex "
            "patterns to extract numbers in formats such as <font face='Courier' size='9'>"
            "$1,000,000</font>, <font face='Courier' size='9'>5.5%</font>, "
            "<font face='Courier' size='9'>$2.5 million</font>. If no numbers appear in the "
            "response, the score defaults to 100 (no numerical claims to verify).",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 6))

    # Factor 4
    story.append(Paragraph("Factor 4: Entity Consistency", styles["Heading3"]))
    story.append(
        Paragraph("<b>Weight: 0.20 (20%)</b>", styles["Body"])
    )
    story.append(
        Paragraph(
            "Verifies that named entities in the response (policy numbers, dates, proper names, "
            "multi-word capitalized terms) also appear in the source documents. Entity extraction "
            "uses regex patterns for: policy/form numbers (e.g., CGL-2024001), dates in multiple "
            "formats (MM/DD/YYYY, Month DD, YYYY), and capitalized proper nouns. If no entities "
            "are found in the response, the score defaults to 100.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    # Rating thresholds
    story.append(Paragraph("Rating Thresholds", styles["Heading3"]))

    rating_table = make_table(
        headers=["Score Range", "Rating", "Indicator", "Meaning"],
        rows=[
            ["80 \u2013 100", "LOW risk", "Green", "Response is well-grounded in source documents"],
            ["50 \u2013 79", "MEDIUM risk", "Amber", "Some claims may not be fully supported"],
            ["0 \u2013 49", "HIGH risk", "Red", "Significant hallucination detected \u2014 review carefully"],
        ],
        styles=styles,
        col_widths=[80, 90, 80, 230],
    )
    story.append(rating_table)
    story.append(Spacer(1, 10))

    # Formula callout
    story.append(
        BoxCallout(
            "Overall Score = (Retrieval Confidence x 0.25) + (Response Grounding x 0.35) "
            "+ (Numerical Fidelity x 0.20) + (Entity Consistency x 0.20). "
            "Result is clamped to [0, 100] and rounded to 1 decimal place.",
            width=480,
            bg=AIG_BLUE_LIGHTER,
            accent=AIG_BLUE,
            font_name="Courier",
            font_size=9,
        )
    )

    story.append(PageBreak())

    # ==================================================================
    # 5. API REFERENCE
    # ==================================================================
    story.append(Paragraph("5. API Reference", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "The UW Companion backend exposes a RESTful API via FastAPI. "
            "Base URL: <font face='Courier' size='9'>http://localhost:8000</font>",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    # --- POST /api/documents/upload ---
    story.append(Paragraph("POST /api/documents/upload", styles["Heading3"]))
    story.append(
        Paragraph(
            "Upload a PDF or DOCX document for processing. The document is parsed, chunked, "
            "embedded, and stored in the vector database.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))

    upload_table = make_table(
        headers=["Property", "Details"],
        rows=[
            ["Content-Type", "multipart/form-data"],
            ["Form Field", 'file (UploadFile) \u2014 the PDF or DOCX file'],
            ["Accepted Types", ".pdf, .docx, .doc"],
            ["Success Response", "200 OK \u2014 DocumentUploadResponse"],
            ["Error Responses", "400 (unsupported type, no filename, no text) | 500 (processing error)"],
        ],
        styles=styles,
        col_widths=[120, 360],
    )
    story.append(upload_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Response Schema (DocumentUploadResponse):", styles["BodyBold"]))
    upload_resp = make_table(
        headers=["Field", "Type", "Description"],
        rows=[
            ["document_id", "string (UUID)", "Unique identifier for the uploaded document"],
            ["filename", "string", "Original filename"],
            ["num_chunks", "integer", "Number of chunks stored in vector DB"],
            ["num_pages", "integer", "Number of pages extracted"],
            ["status", "string", '"indexed" on success'],
        ],
        styles=styles,
        col_widths=[110, 110, 260],
    )
    story.append(upload_resp)
    story.append(Spacer(1, 10))

    # --- GET /api/documents ---
    story.append(Paragraph("GET /api/documents", styles["Heading3"]))
    story.append(
        Paragraph("List all uploaded and indexed documents.", styles["Body"])
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Response: Array of DocumentInfo:", styles["BodyBold"]))
    doc_info_table = make_table(
        headers=["Field", "Type", "Description"],
        rows=[
            ["document_id", "string", "Document UUID"],
            ["filename", "string", "Original filename"],
            ["num_chunks", "integer", "Number of indexed chunks"],
            ["num_pages", "integer", "Number of pages"],
            ["upload_time", "string (ISO 8601)", "Timestamp of upload"],
        ],
        styles=styles,
        col_widths=[110, 120, 250],
    )
    story.append(doc_info_table)
    story.append(Spacer(1, 10))

    # --- DELETE /api/documents/{id} ---
    story.append(Paragraph("DELETE /api/documents/{document_id}", styles["Heading3"]))
    story.append(
        Paragraph(
            "Remove a document and all its chunks from the vector store. "
            "Also deletes the uploaded file from the server.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    del_table = make_table(
        headers=["Property", "Details"],
        rows=[
            ["Path Parameter", "document_id (string) \u2014 UUID of the document to delete"],
            ["Success Response", '200 OK \u2014 {"status": "deleted", "document_id": "..."}'],
            ["Error Response", "404 Not Found \u2014 document does not exist"],
        ],
        styles=styles,
        col_widths=[120, 360],
    )
    story.append(del_table)

    story.append(PageBreak())

    # --- POST /api/chat ---
    story.append(Paragraph("POST /api/chat", styles["Heading3"]))
    story.append(
        Paragraph(
            "Send a natural-language query and receive a RAG-generated answer with hallucination "
            "analysis and underwriting action extraction.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("Request Body (ChatRequest):", styles["BodyBold"]))
    chat_req_table = make_table(
        headers=["Field", "Type", "Default", "Description"],
        rows=[
            ["query", "string", "(required)", "The underwriting question to ask"],
            ["session_id", "string", '"default"', "Session ID for multi-turn conversation history"],
        ],
        styles=styles,
        col_widths=[80, 70, 80, 250],
    )
    story.append(chat_req_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Response Body (ChatResponse):", styles["BodyBold"]))
    chat_resp_table = make_table(
        headers=["Field", "Type", "Description"],
        rows=[
            ["answer", "string", "AI-generated response grounded in document context"],
            ["sources", "SourceReference[]", "Top 5 source chunks with text, file, page, similarity"],
            ["hallucination", "HallucinationReport", "4-factor hallucination analysis (see Section 4)"],
            ["actions", "UWAction[]", "Extracted underwriting actions with priorities"],
            ["session_id", "string", "Session identifier for this conversation"],
        ],
        styles=styles,
        col_widths=[100, 120, 260],
    )
    story.append(chat_resp_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("HallucinationReport Schema:", styles["BodyBold"]))
    hall_schema = make_table(
        headers=["Field", "Type", "Description"],
        rows=[
            ["overall_score", "float (0-100)", "Weighted composite hallucination score"],
            ["retrieval_confidence", "float", "Factor 1 score"],
            ["response_grounding", "float", "Factor 2 score"],
            ["numerical_fidelity", "float", "Factor 3 score"],
            ["entity_consistency", "float", "Factor 4 score"],
            ["sentence_details", "SentenceGrounding[]", "Per-sentence grounding analysis"],
            ["flagged_claims", "string[]", "Sentences with grounding below threshold"],
            ["rating", "string", '"low", "medium", or "high" risk'],
        ],
        styles=styles,
        col_widths=[130, 110, 240],
    )
    story.append(hall_schema)
    story.append(Spacer(1, 10))

    # --- DELETE /api/chat/session/{id} ---
    story.append(Paragraph("DELETE /api/chat/session/{session_id}", styles["Heading3"]))
    story.append(
        Paragraph(
            "Clear the chat history for a specific session. Useful for starting a fresh conversation.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    session_table = make_table(
        headers=["Property", "Details"],
        rows=[
            ["Path Parameter", "session_id (string) \u2014 session to clear"],
            ["Success Response", '200 OK \u2014 {"status": "cleared", "session_id": "..."}'],
        ],
        styles=styles,
        col_widths=[120, 360],
    )
    story.append(session_table)
    story.append(Spacer(1, 10))

    # --- GET /health ---
    story.append(Paragraph("GET /health", styles["Heading3"]))
    story.append(
        Paragraph(
            "Health check endpoint for monitoring and deployment readiness probes.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))
    health_table = make_table(
        headers=["Property", "Details"],
        rows=[
            ["Success Response", '200 OK \u2014 {"status": "ok", "gemini_configured": true/false}'],
            ["Authentication", "None required"],
        ],
        styles=styles,
        col_widths=[120, 360],
    )
    story.append(health_table)

    story.append(PageBreak())

    # ==================================================================
    # 6. FRONTEND FEATURES
    # ==================================================================
    story.append(Paragraph("6. Frontend Features", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "The UW Companion frontend is built with Angular 18 using standalone components, "
            "Tailwind CSS v4 for styling, and Lucide icons for the icon system. It provides "
            "a modern, responsive interface for underwriters.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    # Dashboard
    story.append(Paragraph("Dashboard", styles["Heading3"]))
    dash_bullets = [
        "Real-time metrics display showing document count, chunk count, and system status",
        "Hallucination monitor with aggregate statistics across sessions",
        "Recent activity feed for uploaded documents and chat interactions",
        "Analytics view with visual representations of underwriting insights",
    ]
    for b in dash_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 6))

    # Document Management
    story.append(Paragraph("Document Management", styles["Heading3"]))
    doc_bullets = [
        "Drag-and-drop document upload supporting PDF and DOCX formats",
        "Processing indicator showing parsing, chunking, and embedding progress",
        "Document list with metadata (filename, pages, chunks, upload time)",
        "One-click document deletion with confirmation",
        "Document panel component for detailed document inspection",
    ]
    for b in doc_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 6))

    # AI Chat
    story.append(Paragraph("AI Chat Interface", styles["Heading3"]))
    chat_bullets = [
        "Natural-language query input with command bar interface",
        "Streaming-style response display with markdown rendering",
        "Per-message hallucination gauge showing trust level (green/amber/red)",
        "Source references panel showing matched document chunks with similarity scores",
        "Flagged claims highlighting for sentences with low grounding scores",
        "Multi-turn conversation support with session management",
        "Session clearing for fresh conversations",
    ]
    for b in chat_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 6))

    # UW Actions
    story.append(Paragraph("Underwriting Actions Panel", styles["Heading3"]))
    action_bullets = [
        "Automatic extraction of actionable items from AI analysis",
        "Priority badges with color coding (critical=red, high=orange, medium=yellow, low=green)",
        "Category chips for quick filtering (coverage gap, risk flag, endorsement, compliance, pricing)",
        "Action cards with detail expansion and source reference links",
        "Insight cards component for summarized analytical views",
    ]
    for b in action_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 6))

    # Navigation
    story.append(Paragraph("Navigation &amp; Layout", styles["Heading3"]))
    nav_bullets = [
        "Sidebar navigation with icon-based nav items",
        "Theme service supporting light/dark mode toggle",
        "Responsive layout adapting to different screen sizes",
        "Consistent design language with AIG branding",
    ]
    for b in nav_bullets:
        story.append(bullet(b, styles))

    story.append(PageBreak())

    # ==================================================================
    # 7. CONFIGURATION REFERENCE
    # ==================================================================
    story.append(Paragraph("7. Configuration Reference", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "All configuration is centralized in <font face='Courier' size='9'>config.py</font> "
            "at the backend root. Environment variables can override defaults.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 8))

    config_table = make_table(
        headers=["Variable", "Default", "Description"],
        rows=[
            ["GEMINI_API_KEY", "(env var)", "Google AI Studio API key for Gemini access"],
            ["GEMINI_CHAT_MODEL", "gemini-2.0-flash", "Model used for RAG response generation and action extraction"],
            ["GEMINI_EMBED_MODEL", "models/gemini-embedding-001", "Model used for text embedding"],
            ["EMBEDDING_DIM", "3072", "Dimensionality of embedding vectors"],
            ["LANCE_DB_PATH", "/tmp/uw_companion_lancedb", "File path for LanceDB storage"],
            ["LANCE_TABLE_NAME", "document_chunks", "LanceDB table name for chunk vectors"],
            ["CHUNK_SIZE", "512", "Maximum tokens per document chunk"],
            ["CHUNK_OVERLAP", "64", "Overlap tokens between adjacent chunks"],
            ["TOP_K_RESULTS", "8", "Number of chunks retrieved per search query"],
        ],
        styles=styles,
        col_widths=[140, 140, 200],
    )
    story.append(config_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Hallucination Weights", styles["Heading3"]))
    story.append(
        Paragraph(
            "The <font face='Courier' size='9'>HALLUCINATION_WEIGHTS</font> dictionary controls "
            "the relative importance of each hallucination detection factor:",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 4))

    weight_table = make_table(
        headers=["Key", "Weight", "Factor"],
        rows=[
            ["retrieval_confidence", "0.25", "Quality of retrieved chunks"],
            ["response_grounding", "0.35", "Per-sentence similarity to sources (heaviest)"],
            ["numerical_fidelity", "0.20", "Number matching between response and sources"],
            ["entity_consistency", "0.20", "Named entity matching"],
        ],
        styles=styles,
        col_widths=[160, 80, 240],
    )
    story.append(weight_table)

    story.append(PageBreak())

    # ==================================================================
    # 8. SETUP & RUNNING
    # ==================================================================
    story.append(Paragraph("8. Setup &amp; Running", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Prerequisites", styles["Heading3"]))
    prereq_bullets = [
        "Python 3.9 or higher",
        "Node.js 18+ and npm (for frontend)",
        "A Google AI Studio API key with Gemini access",
    ]
    for b in prereq_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Backend Setup", styles["Heading3"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Install Python dependencies:", styles["Body"]))
    story.append(Paragraph("pip install -r requirements.txt", styles["Code"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Set your Gemini API key:", styles["Body"]))
    story.append(Paragraph("export GEMINI_API_KEY=your_api_key_here", styles["Code"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Start the FastAPI server:", styles["Body"]))
    story.append(
        Paragraph("python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload", styles["Code"])
    )
    story.append(Spacer(1, 4))

    story.append(
        Paragraph(
            "The API will be available at <font face='Courier' size='9'>http://localhost:8000</font>. "
            "Interactive API docs (Swagger UI) are at <font face='Courier' size='9'>"
            "http://localhost:8000/docs</font>.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Frontend Setup", styles["Heading3"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. Install Node.js dependencies:", styles["Body"]))
    story.append(Paragraph("npm install", styles["Code"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Start the Angular development server:", styles["Body"]))
    story.append(Paragraph("ng serve", styles["Code"]))
    story.append(Spacer(1, 4))

    story.append(
        Paragraph(
            "The frontend will be served at <font face='Courier' size='9'>"
            "http://localhost:4200</font> and will proxy API requests to the backend.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Key Dependencies (requirements.txt)", styles["Heading3"]))
    deps_table = make_table(
        headers=["Package", "Version", "Purpose"],
        rows=[
            ["fastapi", "0.115.6", "Async web framework"],
            ["uvicorn[standard]", "0.34.0", "ASGI server"],
            ["lancedb", "0.20.0", "Vector database"],
            ["google-generativeai", "0.8.4", "Gemini API client"],
            ["PyPDF2", "3.0.1", "PDF text extraction"],
            ["python-docx", "1.1.2", "DOCX text extraction"],
            ["numpy", ">=1.24.0,<2.1", "Numerical computing for embeddings"],
            ["pydantic", "2.10.4", "Data validation and schemas"],
            ["pytest", "8.3.4", "Testing framework"],
            ["httpx", "0.28.1", "Async HTTP client for testing"],
        ],
        styles=styles,
        col_widths=[140, 100, 240],
    )
    story.append(deps_table)

    story.append(PageBreak())

    # ==================================================================
    # 9. FEATURE LIST
    # ==================================================================
    story.append(Paragraph("9. Feature List", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Document Ingestion &amp; Processing", styles["Heading3"]))
    doc_features = [
        "PDF document upload and text extraction (PyPDF2)",
        "DOCX document upload with paragraph and table extraction (python-docx)",
        "Page-level text provenance tracking for accurate source citations",
        "Automatic file format detection and parser dispatch",
        "Uploaded file persistence in temporary storage for lifecycle management",
    ]
    for f in doc_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Smart Document Chunking", styles["Heading3"]))
    chunk_features = [
        "Section-aware chunking that respects document structure",
        "Detection of common insurance document headers (SECTION, ENDORSEMENT, SCHEDULE, etc.)",
        "Recursive splitting: sections \u2192 paragraphs \u2192 sentences \u2192 token windows",
        "Configurable chunk size (default 512 tokens) and overlap (default 64 tokens)",
        "Section header prepended to each chunk for context",
        "Unique UUID assigned to every chunk for tracking",
    ]
    for f in chunk_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Vector Search &amp; Retrieval", styles["Heading3"]))
    vec_features = [
        "3072-dimensional Gemini embeddings for high-quality semantic search",
        "Differentiated embedding task types (retrieval_document vs. retrieval_query)",
        "Batch embedding with 100-text batches for efficient indexing",
        "LanceDB vector store with cosine similarity search",
        "Configurable top-K retrieval (default 8 chunks)",
        "Document-level management (add, list, delete) in the vector store",
    ]
    for f in vec_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("RAG-Powered AI Chat", styles["Heading3"]))
    rag_features = [
        "Natural-language question-answering over uploaded documents",
        "Expert underwriting system prompt with strict grounding rules",
        "Context injection with source document and page citations",
        "Multi-turn conversation support with session-based chat history",
        "Chat history capped at 20 messages per session for performance",
        "Graceful handling of empty document stores",
    ]
    for f in rag_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Hallucination Detection", styles["Heading3"]))
    hall_features = [
        "4-factor composite scoring system (retrieval confidence, response grounding, "
        "numerical fidelity, entity consistency)",
        "Per-sentence grounding analysis with embedding similarity comparison",
        "Automatic flagging of ungrounded claims (similarity below 0.65 threshold)",
        "Numerical extraction and cross-referencing (dollar amounts, percentages, numbers)",
        "Named entity extraction and source verification (policy numbers, dates, proper nouns)",
        "Three-tier risk rating: LOW (green), MEDIUM (amber), HIGH (red)",
        "Detailed HallucinationReport with sentence-level breakdown",
    ]
    for f in hall_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Underwriting Action Extraction", styles["Heading3"]))
    act_features = [
        "LLM-based extraction of structured underwriting actions",
        "Five action categories: coverage_gap, risk_flag, endorsement, compliance, pricing",
        "Four priority levels: critical, high, medium, low",
        "Automatic validation and safe-default correction for invalid categories/priorities",
        "Source reference linking to specific documents and pages",
        "JSON output parsing with markdown fence stripping",
    ]
    for f in act_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("API &amp; Integration", styles["Heading3"]))
    api_features = [
        "RESTful API built with FastAPI for high performance",
        "Automatic OpenAPI/Swagger documentation at /docs",
        "CORS configured for local Angular development (ports 4200)",
        "Pydantic v2 request/response validation",
        "Health check endpoint for monitoring and deployment probes",
        "Session management for multi-user chat isolation",
    ]
    for f in api_features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Frontend Experience", styles["Heading3"]))
    fe_features = [
        "Angular 18 with standalone components architecture",
        "Tailwind CSS v4 for responsive, utility-first styling",
        "Lucide icon system for consistent visual language",
        "Dashboard with real-time metrics and hallucination monitoring",
        "Document management panel with upload and deletion",
        "AI Chat with per-message hallucination gauge",
        "Underwriting Actions panel with priority badges and category chips",
        "Source reference cards with similarity scores",
        "Insight cards for analytical summaries",
        "Light/dark theme support via theme service",
        "Command bar interface for quick navigation",
    ]
    for f in fe_features:
        story.append(bullet(f, styles))

    story.append(PageBreak())

    # ==================================================================
    # 10. TESTING
    # ==================================================================
    story.append(Paragraph("10. Testing", styles["Heading1"]))
    story.append(SectionDivider(width=480))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "UW Companion uses pytest as its testing framework with httpx for async API testing.",
            styles["Body"],
        )
    )
    story.append(Spacer(1, 6))

    story.append(Paragraph("Test Infrastructure", styles["Heading3"]))
    test_bullets = [
        "<b>Framework:</b> pytest 8.3.4",
        "<b>HTTP Client:</b> httpx 0.28.1 (for async FastAPI test client)",
        "<b>Test Location:</b> <font face='Courier' size='9'>backend/tests/</font>",
    ]
    for b in test_bullets:
        story.append(bullet(b, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Running Tests", styles["Heading3"]))
    story.append(Paragraph("pytest", styles["Code"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("With verbose output:", styles["Body"]))
    story.append(Paragraph("pytest -v", styles["Code"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("With coverage:", styles["Body"]))
    story.append(Paragraph("pytest --cov=layers --cov=services --cov-report=term-missing", styles["Code"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Recommended Test Coverage", styles["Heading3"]))
    test_coverage = [
        "<b>Unit Tests:</b> Each layer should have isolated unit tests with mocked dependencies",
        "<b>Parsing Layer:</b> Test PDF/DOCX extraction with sample documents, empty files, corrupt files",
        "<b>Chunking Layer:</b> Test section detection, recursive splitting, overlap injection, "
        "configurable parameters",
        "<b>Embedding Layer:</b> Test batch processing, query embedding, API error handling",
        "<b>Vectorization Layer:</b> Test CRUD operations, search result ordering, "
        "similarity score computation",
        "<b>Generation Layer:</b> Test prompt construction, history injection, system prompt enforcement",
        "<b>Hallucination Layer:</b> Test each factor independently, composite scoring, "
        "edge cases (no numbers, no entities, empty response)",
        "<b>Actions Layer:</b> Test JSON parsing, category/priority validation, "
        "malformed LLM output handling",
        "<b>API Integration Tests:</b> End-to-end tests for each endpoint using FastAPI TestClient",
    ]
    for b in test_coverage:
        story.append(bullet(b, styles))

    story.append(Spacer(1, 20))
    story.append(SectionDivider(width=480, color=AIG_BLUE, thickness=2))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "End of Documentation",
            ParagraphStyle(
                "endmark",
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=AIG_BLUE,
                alignment=TA_CENTER,
            ),
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"Generated on {date.today().strftime('%B %d, %Y')} \u2014 UW Companion v1.0",
            ParagraphStyle(
                "enddate",
                fontName="Helvetica",
                fontSize=9,
                textColor=TEXT_SECONDARY,
                alignment=TA_CENTER,
            ),
        )
    )

    return story


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Generating UW Companion documentation...")
    print(f"Output: {OUTPUT_PDF}")

    styles = build_styles()

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        topMargin=52,
        bottomMargin=48,
        leftMargin=56,
        rightMargin=56,
        title="UW Companion - Technical Documentation",
        author="AIG Commercial Insurance Technology",
        subject="AI-Powered Underwriting Assistant Documentation",
    )

    story = build_content(styles)

    # Build with different page templates
    doc.build(
        story,
        onFirstPage=_title_page_template,
        onLaterPages=_header_footer,
    )

    print(f"PDF generated successfully: {OUTPUT_PDF}")
    print(f"File size: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
