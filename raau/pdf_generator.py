import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFReportGenerator:
    @staticmethod
    def generate_pdf(data: dict, results: dict, filename: str = None) -> str:
        if not filename:
            clean_name = "".join(c for c in data['pc_name'] if c.isalnum() or c in ('_', '-'))
            filename = f"ASTER_Assessment_{clean_name}.pdf"

        # Standard Letter size width: 612pt. Margins 36pt left/right -> Printable Width = 540pt
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        # Brand Colors
        COLOR_PRIMARY = colors.HexColor("#0D47A1")    # Deep Blue
        COLOR_SUCCESS = colors.HexColor("#1B5E20")    # Dark Green
        COLOR_TEXT_DARK = colors.HexColor("#212121")  # Off-Black
        COLOR_BG_LIGHT = colors.HexColor("#F5F7FA")   # Soft Grey Fill
        COLOR_BORDER = colors.HexColor("#CFD8DC")     # Light Table Border

        # Base Styles
        styles = getSampleStyleSheet()

        # Custom Paragraph Styles WITH explicit leading (prevents text overlap)
        title_style = ParagraphStyle(
            'HeaderTitle',
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=18,
            textColor=colors.white
        )
        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#BBDEFB"),
            alignment=2
        )
        section_heading = ParagraphStyle(
            'SecHead',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=COLOR_PRIMARY,
            spaceBefore=6,
            spaceAfter=4
        )
        label_bold = ParagraphStyle(
            'LblBold',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_DARK
        )
        val_normal = ParagraphStyle(
            'ValNorm',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_DARK
        )
        score_val_style = ParagraphStyle(
            'ScoreVal',
            fontName='Helvetica-Bold',
            fontSize=28,
            leading=32,
            textColor=COLOR_SUCCESS,
            alignment=1
        )
        score_title_style = ParagraphStyle(
            'ScoreTitle',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=COLOR_PRIMARY,
            alignment=1
        )
        score_body_style = ParagraphStyle(
            'ScoreBody',
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=COLOR_TEXT_DARK
        )

        story = []

        # ---------------------------------------------------------
        # 1. HEADER BANNER
        # ---------------------------------------------------------
        header_table = Table(
            [[
                Paragraph("RESOFTO ASTER ASSESSMENT REPORT", title_style),
                Paragraph("Automated PC Readiness Utility<br/><b>www.resofto.com</b>", subtitle_style)
            ]],
            colWidths=[330, 210]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLOR_PRIMARY),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # ---------------------------------------------------------
        # 2. EXECUTIVE SCORECARD
        # ---------------------------------------------------------
        # Replaced raw Unicode stars/rupee symbols with clean ASCII text to avoid PDF glyph boxes
        star_str = f"Rating: {results.get('star_rating', '5/5')}"
        score_cell = [
            Paragraph("ASTER READINESS", score_title_style),
            Spacer(1, 4),
            Paragraph(f"{results['score_pct']}%", score_val_style),
            Spacer(1, 2),
            Paragraph(star_str, score_title_style)
        ]

        details_cell = [
            Paragraph(f"<b>STATUS:</b> {results['status']}", score_body_style),
            Spacer(1, 3),
            Paragraph(f"<b>RECOMMENDED DEPLOYMENT:</b><br/>1 CPU = {results['capacity']} Concurrent Users", score_body_style),
            Spacer(1, 3),
            Paragraph(f"<b>ESTIMATED 5-YEAR SAVINGS:</b><br/><font color='#1B5E20'><b>INR {results['five_year_savings_inr']:,}</b></font>", score_body_style)
        ]

        score_table = Table([[score_cell, details_cell]], colWidths=[200, 340])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), COLOR_BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 1, COLOR_PRIMARY),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 10),
            ('LINEAFTER', (0,0), (0,0), 0.5, COLOR_BORDER),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # 3. HARDWARE & DIAGNOSTICS AUDIT TABLE
        # ---------------------------------------------------------
        story.append(Paragraph("SYSTEM DIAGNOSTICS SUMMARY", section_heading))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceAfter=6))

        diag_data = [
            [Paragraph("Computer Name", label_bold), Paragraph(data['pc_name'], val_normal), Paragraph("OS Version", label_bold), Paragraph(data['os'], val_normal)],
            [Paragraph("Manufacturer / Model", label_bold), Paragraph(f"{data['manufacturer']} {data['model']}", val_normal), Paragraph("Serial Number", label_bold), Paragraph(data['serial_number'], val_normal)],
            [Paragraph("BIOS Version", label_bold), Paragraph(data['bios_version'], val_normal), Paragraph("TPM Module", label_bold), Paragraph("Present" if data['tpm_present'] else "Not Found", val_normal)],
            [Paragraph("Processor (CPU)", label_bold), Paragraph(f"{data['cpu']} ({data['cores']} Cores)", val_normal), Paragraph("CPU Evaluation", label_bold), Paragraph(f"<b>{results['cpu_eval']}</b>", val_normal)],
            [Paragraph("Installed RAM", label_bold), Paragraph(f"{data['ram_gb']} GB ({data['avail_ram_gb']} GB Free)", val_normal), Paragraph("RAM Evaluation", label_bold), Paragraph(f"<b>{results['ram_eval']}</b>", val_normal)],
            [Paragraph("RAM Speed / Slots", label_bold), Paragraph(f"{data['ram_speed_mhz']} MHz ({data['ram_slots_used']} Slots)", val_normal), Paragraph("Storage Type", label_bold), Paragraph(data['storage_type'], val_normal)],
            [Paragraph("Graphics Adapter", label_bold), Paragraph(data['gpu'], val_normal), Paragraph("Monitors Detected", label_bold), Paragraph(str(data['monitors_detected']), val_normal)]
        ]

        diag_table = Table(diag_data, colWidths=[110, 160, 110, 160])
        diag_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
            ('PADDING', (0,0), (-1,-1), 4.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(diag_table)
        story.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # 4. ACTION ITEMS & UPGRADE RECOMMENDATIONS
        # ---------------------------------------------------------
        story.append(Paragraph("REQUIRED PURCHASES & ACTION ITEMS", section_heading))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceAfter=6))

        rec_rows = []
        if results['recommendations']:
            for rec in results['recommendations']:
                # Replace symbol with text
                clean_rec = rec.replace("~₹", "approx. INR ").replace("₹", "INR ")
                rec_rows.append([Paragraph("[✓]", label_bold), Paragraph(clean_rec, val_normal)])
        else:
            rec_rows.append([Paragraph("[✓]", label_bold), Paragraph("Hardware configuration is optimal. No hardware upgrades or adapters required.", val_normal)])

        if results['alerts']:
            for alert in results['alerts']:
                rec_rows.append([Paragraph("[!]", label_bold), Paragraph(f"<font color='#C62828'>{alert}</font>", val_normal)])

        rec_table = Table(rec_rows, colWidths=[20, 520])
        rec_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # 5. FINANCIAL ROI & ENERGY SAVINGS BREAKDOWN
        # ---------------------------------------------------------
        story.append(Paragraph("FINANCIAL ROI & ENERGY SAVINGS (PER COMPUTER)", section_heading))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceAfter=6))

        fin_data = [
            [Paragraph("Cost Metric / Savings Category", label_bold), Paragraph("Estimated Financial Value", label_bold)],
            [Paragraph("Hardware Procurement Savings (N-1 PCs Avoided)", val_normal), Paragraph(f"INR {results['hardware_saved_inr']:,}", val_normal)],
            [Paragraph("Estimated Hardware Adapter / Expansion Cost", val_normal), Paragraph(f"INR {results['adapter_cost_inr']:,}", val_normal)],
            [Paragraph("Annual Electricity Savings Percentage", val_normal), Paragraph(f"<b>{results['elec_savings_pct']}% / year</b>", val_normal)],
            [Paragraph("Net Cumulative 5-Year Financial Benefit", label_bold), Paragraph(f"<font color='#1B5E20'><b>INR {results['five_year_savings_inr']:,}</b></font>", label_bold)]
        ]

        fin_table = Table(fin_data, colWidths=[320, 220])
        fin_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLOR_BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(fin_table)

        # Build Document
        doc.build(story)
        return os.path.abspath(filename)