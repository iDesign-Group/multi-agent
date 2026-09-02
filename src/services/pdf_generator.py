from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from ..config import REPORTS_DIR


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and 'Page X of Y' footers across all generated pages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header on subsequent pages
        if self._pageNumber > 1:
            self.drawString(36, letter[1] - 22, "Executive Competitive Intelligence Report — AI Multi-Agent Market Intelligence")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 26, letter[0] - 36, letter[1] - 26)

        # Footer with metadata and page count
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 26, letter[0] - 36, 26)
        self.drawString(36, 15, "CONFIDENTIAL — Multi-Agent Market & Competitor Intelligence System")
        self.drawRightString(letter[0] - 36, 15, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


class PDFReportGenerator:
    """Generates corporate executive PDF reports with evidence auditing."""

    def __init__(self, output_dir: str = str(REPORTS_DIR)):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, run_id: str, report_data: Dict[str, Any]) -> str:
        pdf_filename = f"competitive_report_{run_id}.pdf"
        file_path = self.output_dir / pdf_filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=8,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=14,
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=14,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        callout_style = ParagraphStyle(
            "CalloutCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.whitesmoke,
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )

        def _clean_text_for_pdf(text: Any) -> str:
            if text is None:
                return ""
            s = str(text)
            # Replace Rupee symbol with 'Rs. ' to avoid missing glyph square in Type 1 fonts
            return s.replace("₹", "Rs. ")

        story = []

        # 1. Header & Metadata
        company = _clean_text_for_pdf(report_data.get("company_name", "Organization"))
        industry = _clean_text_for_pdf(report_data.get("industry", "Technology"))
        period = _clean_text_for_pdf(report_data.get("analysis_period", "Current"))
        gen_time = _clean_text_for_pdf(report_data.get("generated_at", ""))

        story.append(Paragraph("Executive Competitive Intelligence Report", title_style))
        story.append(
            Paragraph(
                f"<b>Target Organization:</b> {company} &nbsp;|&nbsp; "
                f"<b>Industry:</b> {industry} &nbsp;|&nbsp; "
                f"<b>Period:</b> {period} &nbsp;|&nbsp; "
                f"<b>Generated:</b> {gen_time}",
                subtitle_style,
            )
        )
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # 2. Executive Summary Callout Box
        story.append(Paragraph("Executive Summary", h2_style))
        exec_summary = _clean_text_for_pdf(report_data.get("executive_summary", ""))
        summary_table = Table([[Paragraph(exec_summary, callout_style)]], colWidths=[7.2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # 3. Competitive Landscape Matrix
        story.append(Paragraph("Competitive Landscape", h2_style))
        landscape = report_data.get("landscape", [])
        matrix_data = [
            [
                Paragraph("Competitor", table_header_style),
                Paragraph("Positioning", table_header_style),
                Paragraph("Pricing", table_header_style),
                Paragraph("Key Services", table_header_style),
                Paragraph("Recent Change", table_header_style),
            ]
        ]
        for comp in landscape:
            matrix_data.append(
                [
                    Paragraph(f"<b>{_clean_text_for_pdf(comp.get('name'))}</b>", table_cell_style),
                    Paragraph(_clean_text_for_pdf(comp.get("positioning", "-")), table_cell_style),
                    Paragraph(_clean_text_for_pdf(comp.get("pricing_tier", "-")), table_cell_style),
                    Paragraph(_clean_text_for_pdf(", ".join(comp.get("key_services", []))), table_cell_style),
                    Paragraph(_clean_text_for_pdf(comp.get("recent_change", "-")), table_cell_style),
                ]
            )

        col_widths = [1.2 * inch, 1.2 * inch, 0.9 * inch, 1.8 * inch, 2.1 * inch]
        matrix_table = Table(matrix_data, colWidths=col_widths)
        matrix_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(matrix_table)
        story.append(Spacer(1, 12))

        # 4. Market Opportunities & Recommendations
        story.append(Paragraph("Market Opportunities", h2_style))
        opps = report_data.get("market_opportunities", [])
        for opp in opps:
            story.append(Paragraph(f"• &nbsp;{_clean_text_for_pdf(opp)}", body_style))

        story.append(Spacer(1, 6))
        story.append(Paragraph("Recommended Actions", h2_style))
        recs = report_data.get("recommended_actions", [])
        for rec in recs:
            story.append(Paragraph(f"✓ &nbsp;{_clean_text_for_pdf(rec)}", body_style))

        story.append(Spacer(1, 12))

        # 5. Evidence Quality & Hallucination Audit Section
        ev = report_data.get("evidence_quality", {})
        conf = ev.get("overall_confidence", 0.0)
        valid_cnt = ev.get("claims_validated", 0)
        rev_cnt = ev.get("claims_requiring_review", 0)
        total_cnt = ev.get("total_claims", 0)

        evidence_summary_text = (
            f"<b>Evidence Quality Score:</b> {conf}% &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Validated Claims:</b> {valid_cnt}/{total_cnt} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Requires Review:</b> {rev_cnt} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<i>Audited against source material by Validator Agent</i>"
        )

        badge_color = "#15803d" if conf >= 85 else "#b45309"
        ev_box = Table(
            [
                [
                    Paragraph(
                        f"<font color='{badge_color}'><b>AI Evaluation & Evidence Audit</b></font><br/>{evidence_summary_text}",
                        callout_style,
                    )
                ]
            ],
            colWidths=[7.2 * inch],
        )
        ev_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4" if conf >= 85 else "#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac" if conf >= 85 else "#fde68a")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(KeepTogether([Paragraph("Evidence Quality & Verification Audit", h2_style), ev_box]))

        # Claim-level verification sample
        verifications = ev.get("verifications", [])[:8]
        if verifications:
            story.append(Spacer(1, 6))
            ev_table_data = [
                [
                    Paragraph("Claim Statement", table_header_style),
                    Paragraph("Status", table_header_style),
                    Paragraph("Confidence", table_header_style),
                    Paragraph("Verified Citation Quote", table_header_style),
                ]
            ]
            for v in verifications:
                raw_status = v.get("status", "VALIDATED")
                if hasattr(raw_status, "value"):
                    raw_status = raw_status.value
                status_str = str(raw_status).replace("ClaimStatus.", "").replace("_", " ").strip()
                color_hex = "#16a34a" if status_str == "VALIDATED" else ("#d97706" if "LOW" in status_str else "#dc2626")
                status_p = Paragraph(f"<font color='{color_hex}'><b>{status_str}</b></font>", table_cell_style)
                citation = _clean_text_for_pdf(v.get("source_citation") or v.get("audit_notes", "N/A"))
                stmt = _clean_text_for_pdf(v.get("statement", ""))
                ev_table_data.append(
                    [
                        Paragraph(stmt, table_cell_style),
                        status_p,
                        Paragraph(f"{int(v.get('confidence_score', 1.0) * 100)}%", table_cell_style),
                        Paragraph(f"<i>\"{citation[:140]}...\"</i>" if len(citation) > 140 else f"<i>\"{citation}\"</i>", table_cell_style),
                    ]
                )
            ev_table = Table(ev_table_data, colWidths=[2.4 * inch, 1.2 * inch, 0.9 * inch, 2.7 * inch])
            ev_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                        ("PADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(ev_table)

        doc.build(story, canvasmaker=NumberedCanvas)
        return str(file_path)
