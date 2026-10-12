import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from backend.app.services.shipment_service import get_shipment_by_id
from backend.app.services.alert_service import list_alerts
from backend.app.services.excursion_engine import get_excursion_events_for_shipment
from backend.app.services.viability_estimator import calculate_demo_viability
from backend.app.models.database import get_connection
from backend.app.config import DEMO_DISCLAIMER

def generate_shipment_pdf(shipment_id: str) -> io.BytesIO:
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise ValueError(f"Shipment '{shipment_id}' not found.")

    with get_connection() as conn:
        readings_rows = conn.execute(
            """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN quality_status = 'valid' THEN 1 END) as valid_cnt,
                   MAX(temperature_c) as max_temp,
                   MIN(temperature_c) as min_temp
            FROM readings WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

        assessment_row = conn.execute(
            "SELECT * FROM assessments WHERE shipment_id = ? ORDER BY created_at DESC LIMIT 1",
            (shipment_id,),
        ).fetchone()

    total_readings = readings_rows["total"] or 0
    valid_readings = readings_rows["valid_cnt"] or 0
    max_t = readings_rows["max_temp"]
    min_t = readings_rows["min_temp"]

    excursions = get_excursion_events_for_shipment(shipment_id)
    alerts = list_alerts(shipment_id=shipment_id)

    viability = calculate_demo_viability(
        valid_readings_count=valid_readings,
        total_readings=total_readings,
        excursion_events=excursions,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#b45309"),
        backColor=colors.HexColor("#fef3c7"),
        borderPadding=6,
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "Heading2Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # Title & Header
    story.append(Paragraph("CryoUrsus — Cold-Chain Telemetry & Decision Report", title_style))
    story.append(Paragraph(f"Simulated Shipment ID: <b>{shp.id}</b> | Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
    story.append(Spacer(1, 8))

    # Mandatory Simulation Disclaimer Banner
    story.append(Paragraph(f"<b>[SIMULATION NOTICE]</b> {DEMO_DISCLAIMER} All readings, sensor metrics, and thermal viability indicators herein are computer-simulated demonstrative models.", disclaimer_style))

    # Shipment Metadata Table
    profile_name = shp.profile.name if shp.profile else "N/A"
    limits = f"{shp.profile.lower_limit_c:.1f}°C to {shp.profile.upper_limit_c:.1f}°C" if shp.profile else "N/A"
    metadata_data = [
        ["Product Profile:", Paragraph(profile_name, body_style), "Storage Envelope:", limits],
        ["Shipment Status:", shp.status.upper(), "Destination:", shp.destination_label or "Demo Destination"],
        ["Vial Count (3x3):", f"{shp.vial_count} / 9", "Active Sensors:", f"{shp.sensor_count} Sensors"],
        ["Started At:", shp.started_at or "Not started", "Ended At:", shp.ended_at or "Active/Ongoing"],
    ]
    t_meta = Table(metadata_data, colWidths=[110, 160, 110, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # Telemetry & Excursion Summary
    story.append(Paragraph("Telemetry & Thermal Excursion Summary", h2_style))
    max_str = f"{max_t:.1f}°C" if max_t is not None else "N/A"
    min_str = f"{min_t:.1f}°C" if min_t is not None else "N/A"
    summary_data = [
        ["Total Telemetry Readings", str(total_readings), "Valid Sample Count", str(valid_readings)],
        ["Peak Observed Temp", max_str, "Minimum Observed Temp", min_str],
        ["Total Excursion Breaches", str(len(excursions)), "Total Active/Raised Alerts", str(len(alerts))],
    ]
    t_sum = Table(summary_data, colWidths=[140, 130, 140, 130])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 12))

    # Demo Viability Estimation Panel
    story.append(Paragraph("Illustrative Remaining-Viability Model (Demonstration Only)", h2_style))
    score_display = f"{viability['score']:.1f} / 100" if viability["score"] is not None else "N/A (Insufficient Data)"
    model_data = [
        ["Method Version:", viability["method_version"], "Demo Viability Score:", score_display],
        ["Status Category:", viability["label"], "Valid Coverage:", f"{viability['features']['valid_data_coverage']*100:.1f}%"],
    ]
    t_model = Table(model_data, colWidths=[120, 150, 120, 150])
    t_model.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_model)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Model Decision Factors & Reasoning:</b>", body_style))
    for reason in viability["explanation"]:
        story.append(Paragraph(f"• {reason}", body_style))
    story.append(Spacer(1, 10))

    # Operator Human Review Section
    story.append(Paragraph("Human Assessment & Chain-of-Custody Disposition", h2_style))
    rev_status = shp.operator_review_status or "PENDING REVIEW"
    rev_note = shp.operator_review_note or "No review notes submitted by operator."
    if assessment_row:
        rev_status = assessment_row["review_status"]
        rev_note = assessment_row["review_note"] or rev_note

    review_data = [
        ["Review Status:", rev_status.upper()],
        ["Review Notes:", Paragraph(rev_note, body_style)],
    ]
    t_rev = Table(review_data, colWidths=[120, 420])
    t_rev.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fafaf9")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_rev)
    story.append(Spacer(1, 10))

    # Excursions / Alerts table if any
    if alerts:
        story.append(Paragraph(f"Logged Alerts ({len(alerts)} records)", h2_style))
        alert_rows = [["Type", "Severity", "Title", "Status", "Timestamp"]]
        for alt in alerts[:10]:
            alert_rows.append([
                alt.type,
                alt.severity.upper(),
                Paragraph(alt.title, body_style),
                alt.status.upper(),
                alt.created_at[:19].replace("T", " "),
            ])
        t_alts = Table(alert_rows, colWidths=[80, 60, 180, 80, 140])
        t_alts.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_alts)

    doc.build(story)
    buffer.seek(0)
    return buffer
