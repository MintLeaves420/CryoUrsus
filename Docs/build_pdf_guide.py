#!/usr/bin/env python
"""
Builds the comprehensive CryoUrsus Architecture & Complete Guide PDF.
Saves output to Docs/CryoUrsus_Complete_Guide.pdf.
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

DOCS_DIR = Path(__file__).resolve().parent
PDF_PATH = DOCS_DIR / "CryoUrsus_Complete_Guide.pdf"


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count."""
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 760, "CryoUrsus — Complete Project Guide & Technical Architecture")
            self.drawRightString(572, 760, "Cold-Chain ML Simulation")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 752, 572, 752)

        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(40, 32, "Confidential & Educational • CryoUrsus Cold-Chain Simulation Project")
        self.drawRightString(572, 32, page_str)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)

        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Custom palette
    NAVY = colors.HexColor("#0F172A")
    TEAL = colors.HexColor("#0D9488")
    DARK_TEAL = colors.HexColor("#0F766E")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    BORDER_COL = colors.HexColor("#E2E8F0")
    TEXT_MAIN = colors.HexColor("#1E293B")
    TEXT_MUTED = colors.HexColor("#475569")
    AMBER = colors.HexColor("#D97706")
    RED_ACCENT = colors.HexColor("#DC2626")

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=NAVY,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=TEAL,
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=DARK_TEAL,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_MAIN,
        spaceAfter=6,
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=NAVY,
    )
    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=NAVY,
    )

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER
    # ---------------------------------------------------------
    story.append(Paragraph("CryoUrsus: The Complete Guide", title_style))
    story.append(Paragraph("Architecture, Machine Learning, Telemetry Simulation, and How It All Works", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceBefore=0, spaceAfter=12))

    # Executive Box
    summary_html = """
    <b>What is this document?</b> This guide explains everything about <b>CryoUrsus</b> from top to bottom. 
    It is written in clear, friendly language with relatable analogies so that anyone—whether you are a 
    software engineer, a product manager, or someone with zero AI background—can understand what the system 
    does, why it is built this way, and how the machine learning operates under the hood.
    """
    callout_data = [[Paragraph(summary_html, body_style)]]
    callout_table = Table(callout_data, colWidths=[532])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDFA")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#99F6E4")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 1: THE 10-YEAR-OLD EXPLANATION
    # ---------------------------------------------------------
    story.append(Paragraph("1. What Is CryoUrsus? (The 10-Year-Old Explanation)", h1_style))
    story.append(Paragraph(
        "Imagine you are sending your friend an <b>ice cream cake</b> by mail across a hot desert. "
        "If the cake gets even slightly warm for an hour, it turns into sticky soup. Even if you freeze it back "
        "later, the cake is ruined—nobody can eat it!",
        body_style
    ))
    story.append(Paragraph(
        "In modern medicine, doctors use super-sensitive life-saving treatments called <b>biologics</b> "
        "(like mRNA vaccines or cell therapies). Just like that ice cream cake, these medicines must stay in "
        "a strict <b>'Cold Chain'</b>—an unbroken chain of super-chilled boxes, delivery trucks, and refrigerators. "
        "For example, an mRNA vaccine has to stay colder than <b>-60°C</b> (colder than the North Pole!), "
        "while antibody medicines must stay in a refrigerator between <b>+2°C and +8°C</b>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>CryoUrsus is a smart digital guardian simulation.</b> It acts like an intelligent co-pilot "
        "that rides along with the medicine package. It reads temperature sensors every second, watches out for "
        "faulty or broken sensors, rings the alarm if the cooler starts warming up, and uses <b>Machine Learning</b> "
        "to calculate exactly how much medicine potency is left—and explains exactly why!",
        body_style
    ))
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 2: HOW THE SYSTEM WORKS STEP-BY-STEP
    # ---------------------------------------------------------
    story.append(Paragraph("2. How It Works: The 6-Step Journey of a Vial", h1_style))

    journey_steps = [
        ("Step 1: The Product Profile", 
         "Before the truck leaves, the system chooses what medicine is inside: Monoclonal Antibodies (+2°C to +8°C), "
         "mRNA Vaccine (-80°C to -60°C), or Cryopreserved Cells (-150°C to -120°C). This sets the 'safe safety envelope'."),
        ("Step 2: 3D Package Telemetry", 
         "Inside the package, 3 to 10 digital sensors report temperature readings every 1.5 seconds. "
         "The user sees a real-time interactive 3D box with color-coded vials showing thermal gradients across the box."),
        ("Step 3: The Sensor Detective", 
         "Before trusting any temperature, CryoUrsus checks sensor health. If a sensor gets unplugged ('disconnected'), "
         "freezes on one exact number ('stuck'), or sends crazy data like 150°C ('implausible'), it flags the sensor as faulty."),
        ("Step 4: Temperature Grade Referee", 
         "When a valid reading breaches the safety limit, the referee assigns a severity grade: "
         "Grade 0 (Normal), Grade 1 (Mild: 0-2°C breach), Grade 2 (Moderate: 2-5°C breach), or Grade 3 (Severe: >5°C breach)."),
        ("Step 5: The Machine Learning Brain", 
         "The app feeds these excursion-grade durations into an offline-trained Random Forest model. "
         "The AI predicts the remaining viability percentage (e.g., 94.2% viable)."),
        ("Step 6: SHAP Explainability", 
         "The AI doesn't just give a number; it itemizes the reason: 'Heat Grade 3 for 45 seconds reduced viability by -4.2%'. "
         "Operators can review and download a cryptographically auditable PDF report."),
    ]

    for title, desc in journey_steps:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", body_style))

    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 3: THE TEMPERATURE GRADING SYSTEM
    # ---------------------------------------------------------
    story.append(Paragraph("3. Clinical Excursion Grading: Why Not Raw Temperatures?", h1_style))
    story.append(Paragraph(
        "Why can't the Machine Learning model just look at raw temperature numbers like <b>+5.0°C</b>? "
        "Because context is everything! For an antibody medicine (+2°C to +8°C), +5.0°C is <i>perfect</i>. "
        "But for an mRNA vaccine (-80°C to -60°C), +5.0°C is a complete disaster! "
        "Therefore, CryoUrsus transforms raw numbers into <b>Universal Excursion Grades</b>:",
        body_style
    ))

    grade_table_data = [
        ["Grade", "Condition", "Temperature Delta Beyond Envelope", "Severity Impact"],
        ["Grade 0", "Normal", "0.0°C (Within configured safe limits)", "Optimal (Zero degradation)"],
        ["Grade 1", "Mild Excursion", "More than 0.0°C up to 2.0°C beyond limit", "Minor stress on biologic"],
        ["Grade 2", "Moderate Excursion", "More than 2.0°C up to 5.0°C beyond limit", "Accelerated thermal decay"],
        ["Grade 3", "Severe Excursion", "More than 5.0°C beyond limit", "Rapid loss of potency / structure"],
    ]
    t_grade = Table(grade_table_data, colWidths=[60, 110, 202, 160])
    t_grade.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_grade)
    story.append(Spacer(1, 14))

    # Page Break for clean multi-page reading
    story.append(PageBreak())

    # ---------------------------------------------------------
    # SECTION 4: THE MACHINE LEARNING MODEL & JOBLIB
    # ---------------------------------------------------------
    story.append(Paragraph("4. How the Machine Learning Works (Under the Hood)", h1_style))
    story.append(Paragraph(
        "CryoUrsus uses an offline-trained <b>Random Forest Regressor</b>. Here is how it functions in plain English:",
        body_style
    ))

    story.append(Paragraph("A. What is a Random Forest?", h2_style))
    story.append(Paragraph(
        "Think of a Random Forest as a <b>committee of 100 expert scientists (decision trees)</b>. "
        "Each tree asks a series of 'Yes/No' questions about the shipment: <i>'Did Grade 3 last longer than 30 seconds? "
        "Is this an mRNA vaccine? How many breaches happened?'</i> Each tree comes up with a prediction, and the forest "
        "averages all 100 votes together. This committee approach prevents single mistakes and makes the model super-accurate.",
        body_style
    ))

    story.append(Paragraph("B. What is `.joblib`?", h2_style))
    story.append(Paragraph(
        "When you train a machine learning model, Python builds large mathematical tables in your computer's RAM. "
        "<b>`.joblib` is like a deep-freeze camera snapshot of the trained model's brain.</b> "
        "Instead of retraining the model every time someone opens the web page (which would make the computer slow and hot), "
        "we save the trained model once to disk as <code>viability_model.joblib</code>. When the FastAPI server starts, "
        "it loads this file into memory in less than 20 milliseconds and reuses it for every prediction instantly!",
        body_style
    ))

    story.append(Paragraph("C. The 16 Features Fed Into the Model", h2_style))
    story.append(Paragraph(
        "The model looks at exactly 16 measurements (measured consistently in seconds):",
        body_style
    ))

    features_data = [
        ["Feature Category", "Feature Name", "What It Measures"],
        ["Formulation (1)", "biological_type", "Formula sensitivity (mRNA vaccine, antibody, or cell therapy)"],
        ["Heat Grades (3)", "heat_grade_1/2/3_time_sec", "Seconds package was too warm in Grade 1, 2, or 3"],
        ["Cold Grades (3)", "cold_grade_1/2/3_time_sec", "Seconds package was too frozen in Grade 1, 2, or 3"],
        ["Combined Grades (3)", "grade_1/2/3_time_sec", "Total seconds across both heat and cold breaches"],
        ["Aggregate Time (2)", "total_excursion_time_sec\nlongest_excursion_sec", "Total seconds outside envelope & longest single continuous event"],
        ["Counts & Peak (4)", "excursion_count\nheat/cold_excursion_count\nmax_grade_reached", "Number of breach events and the worst grade severity reached (0 to 3)"],
    ]
    t_feat = Table(features_data, colWidths=[110, 180, 242])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 5: SHAP EXPLAINABLE AI
    # ---------------------------------------------------------
    story.append(Paragraph("5. Explainable AI: What is SHAP?", h1_style))
    story.append(Paragraph(
        "In hospital medicine, an AI cannot just say: <i>'Viability is 85%, trust me.'</i> "
        "Doctors and quality regulators must know <b>why</b>. This is why CryoUrsus uses <b>SHAP</b> "
        "(SHapley Additive exPlanations).",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Analogy:</b> Imagine getting an itemized supermarket grocery bill. It doesn't just say "
        "'Total: $85'. It shows: <i>Base total $100, -5 dollars for spilled milk, -10 dollars for crushed eggs</i>. "
        "SHAP does the exact same thing for the AI prediction:",
        body_style
    ))

    shap_box = """
    <b>Average Expected Viability Baseline:</b> 91.8%<br/>
    <b>• SHAP Impact:</b> Peak Excursion Grade (Grade 3 reached) contributed <b>-3.2%</b><br/>
    <b>• SHAP Impact:</b> Heat Grade 3 Duration (60s) contributed <b>-4.5%</b><br/>
    <b>• SHAP Impact:</b> mRNA Vaccine Formulation Sensitivity contributed <b>-1.1%</b><br/>
    <b>Final Predicted Viability:</b> <b>83.0%</b> (Transparent & Auditable!)
    """
    s_table = Table([[Paragraph(shap_box, body_style)]], colWidths=[532])
    s_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#FDE68A")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(s_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 6: SOFTWARE ARCHITECTURE & TECH STACK
    # ---------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("6. Software Architecture & Technology Stack", h1_style))
    story.append(Paragraph(
        "CryoUrsus is built as a production-grade local-first web application divided into clean modules:",
        body_style
    ))

    tech_data = [
        ["Layer", "Technology", "Role & Purpose in CryoUrsus"],
        ["Frontend UI", "React 18 + TypeScript + Vite", "Fast, type-safe dashboard with tabs for Operator, QA Reviewer, and Log."],
        ["3D Visualization", "Three.js + Lucide Icons", "Renders the interactive 3D thermal package and vial status."],
        ["Backend API", "FastAPI (Python 3.10+)", "Asynchronous high-performance REST endpoints + WebSocket streaming server."],
        ["Real-Time Streaming", "WebSockets", "Broadcasts tick readings every 1.5s to all connected client screens."],
        ["Database", "SQLite (ACID Compliant)", "Authoritative persistence for shipments, sensors, readings, and audits."],
        ["Machine Learning", "Scikit-Learn + Joblib", "RandomForest regression pipeline serialized to disk for instant inference."],
        ["Explainable AI", "SHAP (TreeExplainer)", "Calculates mathematical feature-attribution scores per shipment."],
        ["Reporting", "ReportLab", "Generates compliant, cryptographically audited PDF custody certificates."],
    ]
    t_tech = Table(tech_data, colWidths=[90, 150, 292])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 14))

    # Architecture Diagram
    story.append(Paragraph("High-Level Data Flow Diagram:", h2_style))
    arch_box = """
    <b>[3D Package & Virtual Sensors]</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;│ (Simulated telemetry ticks every 1.5s)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
    <b>[Sensor Validation Engine]</b> ───(Fault detected?)───► <b>[Alert Service]</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;│ (Trustworthy readings only)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
    <b>[Excursion Grade Engine]</b> (Maps breaches into Grade 0, 1, 2, 3 seconds)<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;│<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
    <b>[ML Viability Model (Loaded once via .joblib)]</b> ──► <b>[SHAP Explainer]</b><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;│<br/>
    &nbsp;&nbsp;&nbsp;&nbsp;▼<br/>
    <b>[WebSocket Broadcaster]</b> ───► <b>[React Operator Dashboard (Real-Time)]</b>
    """
    diag_table = Table([[Paragraph(arch_box, code_style)]], colWidths=[532])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('BORDER', (0, 0), (-1, -1), 1, BORDER_COL),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 7: CORE PRINCIPLES & CHEAT SHEET
    # ---------------------------------------------------------
    story.append(Paragraph("7. Core Engineering Principles", h1_style))
    principles = [
        ("1. Single Source of Truth", "All calculations and state transitions happen strictly on the FastAPI backend. The frontend is a clean display layer."),
        ("2. Offline Training Only", "The ML model trains offline on-demand. It never retrains during server startup, simulation ticks, or web page refreshes."),
        ("3. Quality Gate Before AI", "If sensors are faulty or dropped (<50% valid telemetry), the AI refuses to guess and reports 'Insufficient Trustworthy Data'."),
        ("4. Transparent Simulation Disclaimer", "Every dashboard view and PDF report clearly marks numbers as a synthetic demo simulation, never real medical advice."),
    ]
    for p_title, p_desc in principles:
        story.append(Paragraph(f"• <b>{p_title}:</b> {p_desc}", body_style))

    story.append(Spacer(1, 10))

    story.append(Paragraph("8. Commands & Quick Reference Guide", h1_style))
    cmd_data = [
        ["Action", "Terminal Command"],
        ["1. Train ML Model Offline", "python backend/ml/train_model.py"],
        ["2. Start Backend Server", "python -m uvicorn backend.app.main:app --port 8000 --reload"],
        ["3. Start Frontend Client", "cd frontend && npm run dev"],
        ["4. Run Automated Test Suite", "python -m pytest backend/tests"],
        ["5. Build Production Frontend", "cd frontend && npm run build"],
    ]
    t_cmd = Table(cmd_data, colWidths=[180, 352])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_cmd)
    story.append(Spacer(1, 14))

    # Disclaimer note
    disc_html = "<b>Regulatory Notice:</b> CryoUrsus is an educational demonstration software developed for cold-chain simulation testing. It is not an FDA-cleared or CE-marked medical device."
    d_table = Table([[Paragraph(disc_html, callout_style)]], colWidths=[532])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#FECACA")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(d_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Guide PDF generated successfully at: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
