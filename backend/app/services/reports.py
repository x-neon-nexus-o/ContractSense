"""PDF analysis report generation."""
from __future__ import annotations

import io
from html import escape
from typing import Any


def generate_pdf_report(result: dict[str, Any]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    except ImportError as exc:
        raise RuntimeError("PDF reports require ReportLab; install backend/requirements.txt.") from exc
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=0.62*inch, leftMargin=0.62*inch,
                            topMargin=0.64*inch, bottomMargin=0.58*inch, title="ContractSense review report")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", parent=styles["Title"], textColor=colors.HexColor("#172d35"),
                              fontSize=23, leading=27, alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#66757a")))
    story = [Paragraph("ContractSense", styles["Brand"]),
             Paragraph("AI-assisted contract review • informational use only", styles["Normal"]), Spacer(1, 16)]
    meta = [["Document", escape(str(result.get("contract_name", "Uploaded contract")))],
            ["Contract type", escape(str(result.get("contract_type", "Not specified")).title())],
            ["State / jurisdiction", escape(str(result.get("jurisdiction_state") or "Not provided"))],
            ["Overall review priority", f"{int(result.get('overall_risk_score',0))}/100 • {escape(str(result.get('overall_risk_level','unknown')).upper())}"],
            ["Score meaning", escape(str(result.get("score_label", "Review-priority indicator; not a probability or legal conclusion")))],
            ["Clauses reviewed", str(result.get("clause_count", 0))]]
    table = Table([[Paragraph(f"<b>{escape(k)}</b>", styles["BodyText"]), Paragraph(v, styles["BodyText"])] for k,v in meta], colWidths=[1.7*inch, 5.4*inch])
    table.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#f2f6f4")), ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#dce5e1")),
                               ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#dce5e1")), ("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story += [table, Spacer(1, 16), Paragraph("Opening text excerpt (not an AI-generated summary)", styles["Heading2"]),
              Paragraph(escape(str(result.get("summary", "No extracted text available."))), styles["BodyText"]), Spacer(1, 12)]
    story.append(Paragraph("Legal review prompts", styles["Heading2"]))
    checks = result.get("legal_checks", [])
    if checks:
        for item in checks:
            title = f"{escape(str(item.get('law','')))} · {escape(str(item.get('provision','')))} · {escape(str(item.get('severity','')).upper())}"
            source_urls = item.get("source_urls") or ([item.get("source_url")] if item.get("source_url") else [])
            source = escape(" · ".join(str(url) for url in source_urls))
            source_title = escape(str(item.get("source_title", "")))
            checked_on = escape(str(item.get("source_checked_on", "")))
            source_metadata = " · ".join(part for part in [source_title, f"Sources: {source}" if source else "", f"Checked: {checked_on}" if checked_on else ""] if part)
            story += [Paragraph(f"<b>{title}</b>", styles["BodyText"]),
                      Paragraph(escape(str(item.get("message", ""))), styles["BodyText"]),
                      Paragraph(f"Rule ID: {escape(str(item.get('rule_id','')))} · {source_metadata}", styles["Small"]), Spacer(1, 8)]
    else:
        story.append(Paragraph("No configured deterministic review prompt was triggered. This is not a legal clearance.", styles["BodyText"]))
    story += [Spacer(1, 8), Paragraph("Clause findings", styles["Heading2"])]
    for clause in result.get("clauses", [])[:60]:
        title = f"{clause.get('id','')} · {clause.get('category','Other')} · {str(clause.get('risk_level','low')).upper()} · page {clause.get('page', 1)}"
        story += [Paragraph(f"<b>{escape(title)}</b>", styles["BodyText"]),
                  Paragraph(escape(str(clause.get("text", ""))[:1800]), styles["BodyText"]),
                  Paragraph(f"Classifier: {escape(str(clause.get('classifier_engine','')))} · confidence (not calibrated): {clause.get('confidence',0)} · review signals: {escape('; '.join(clause.get('risk_signals',[])))}", styles["Small"]),
                  Spacer(1, 8)]
    story += [Spacer(1, 12), Paragraph("Coverage and limitations", styles["Heading2"])]
    for note in result.get("coverage_notes", []):
        story.append(Paragraph("• " + escape(str(note)), styles["Small"]))
    story += [Spacer(1, 10), Paragraph(escape(str(result.get("disclaimer", ""))), styles["Small"])]
    doc.build(story)
    return stream.getvalue()
