"""Generate the PDF form of the Alderwood RFP fixture.

This is the hard parsing case. Requirements are embedded in flowing numbered
prose rather than table rows, so a structural parser cannot recover them and
the LLM fallback path has to. It carries the hazards real RFP PDFs carry:

  - a cover page and a table of contents whose entries look like requirements
  - front matter (timeline, submission instructions, evaluation criteria,
    glossary) written in dense "must"/"shall" language while containing NO
    requirements at all - the single largest source of false positives
  - a terms and conditions appendix, likewise all obligation language
  - repeating page headers and footers that interleave into extracted text
  - a signature and attestation page

Correct extraction yields exactly the requirements in requirements_data, and
nothing from the front matter or appendices.

Not exercised here: a requirement whose text breaks across a page boundary.
ReportLab reflows a paragraph onto the next page rather than splitting it, and
forcing a split needs a requirement longer than a full page, which no real RFP
contains. If that case matters later, hand-author a PDF for it rather than
distorting this one.
"""

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

sys.path.insert(0, str(Path(__file__).parent))
from requirements_data import (  # noqa: E402
    COMPLIANCE_DEFINITIONS,
    RFP_META,
    SECTIONS,
)

OUT = Path(__file__).parent / "rfp-alderwood-retail.pdf"

BACKGROUND = [
    f"{RFP_META['buyer']} operates 118 grocery and general-merchandise stores across "
    "the Pacific Northwest and Mountain West, together with an e-commerce storefront "
    "hosted on Shopify Plus. Its loyalty programme has 2.1 million enrolled members and "
    "captures transaction data from all store formats, including 22 in-store pharmacy "
    "counters.",

    "Alderwood is seeking a customer data platform to unify online, in-store, and "
    "loyalty data into a single customer profile, and to drive marketing "
    "personalisation from that profile. Campaign execution today runs through "
    "Salesforce Marketing Cloud, and the analytics team operates a Snowflake "
    "warehouse. Alderwood anticipates expanding operations into Canada within 18 "
    "months of contract signature.",

    "This solicitation covers the licence, implementation, and ongoing support of that "
    "platform for an initial term of three years. Alderwood intends to award to a "
    "single vendor. Alderwood is not obliged to award at all, and reserves the right "
    "to cancel this solicitation at any point prior to execution of a definitive "
    "agreement.",
]

# Front matter. Dense obligation language, zero requirements. Every "must" and
# "shall" below is a false positive waiting to happen.
SUBMISSION = [
    "Responses must be submitted as a single PDF document together with the completed "
    f"response workbook to {RFP_META['contact']} no later than "
    f"{RFP_META['due']} at {RFP_META['due_time']}. Late submissions shall not be "
    f"considered. Each submission must cite reference {RFP_META['reference']} in the "
    "subject line.",

    "Vendors must submit clarification questions in writing no later than "
    f"{RFP_META['questions_due']}. Alderwood will publish consolidated answers to all "
    "vendors that have registered an intent to respond. Vendors must not contact "
    "Alderwood store, marketing, or technology personnel directly in connection with "
    "this solicitation. Any such contact may result in disqualification.",

    "Each response must include: the completed response workbook with every line item "
    "answered; a completed pricing workbook; three customer references; a copy of the "
    "vendor's most recent SOC 2 Type II report or equivalent attestation; and the "
    "signed attestation at Appendix C. A response omitting any of these elements may "
    "be scored as incomplete.",

    "Alderwood shall not be liable for any cost incurred by a vendor in preparing a "
    "response. All material submitted becomes the property of Alderwood. Vendors must "
    "mark any commercially confidential material clearly; Alderwood will use "
    "reasonable efforts to protect material so marked but gives no warranty.",
]

TIMELINE = [
    ["Milestone", "Date"],
    ["RFP issued", RFP_META["issued"]],
    ["Registration of intent to respond due", "11 July 2026"],
    ["Clarification questions due", RFP_META["questions_due"]],
    ["Consolidated answers published", "1 August 2026"],
    ["Responses due", f"{RFP_META['due']}, {RFP_META['due_time']}"],
    ["Shortlist notified", "28 August 2026"],
    ["Vendor demonstrations", "Week of 7 September 2026"],
    ["Reference checks complete", "25 September 2026"],
    ["Intent to award", "9 October 2026"],
    ["Target contract execution", "6 November 2026"],
]

EVALUATION = [
    ["Criterion", "Weighting"],
    ["Functional fit", "30%"],
    ["Information security and privacy", "25%"],
    ["Technical architecture and scalability", "15%"],
    ["Total cost of ownership over five years", "15%"],
    ["Implementation approach and timeline", "8%"],
    ["Support model and service levels", "5%"],
    ["Vendor viability and references", "2%"],
]

GLOSSARY = [
    ("Activation", "The delivery of a segment or profile attribute from the platform to a downstream execution system."),
    ("CDP", "Customer data platform. The class of system sought under this solicitation."),
    ("Identity resolution", "The process of associating records originating from different sources with a single individual."),
    ("Known customer", "A customer profile associated with at least one directly identifying attribute, such as an email address or loyalty number."),
    ("Loyalty member", "An individual enrolled in the Alderwood Advantage loyalty programme."),
    ("Must", "Denotes a mandatory requirement. A response of Not Supported against a Must requirement may disqualify the response."),
    ("Profile", "The unified record held by the platform for a single individual."),
    ("Segment", "A defined population of customer profiles meeting a stated set of conditions."),
    ("Should", "Denotes an important but non-disqualifying requirement."),
    ("Tracked profile", "A customer profile counted for the purposes of subscription pricing."),
]

TERMS = [
    "The successful vendor shall enter into Alderwood's master services agreement. "
    "Vendors must record any exception to those terms in the exceptions log within the "
    "response workbook. Exceptions raised after the response deadline shall not be "
    "considered.",

    "The vendor shall maintain commercial general liability insurance of not less than "
    "five million dollars per occurrence, professional liability insurance of not less "
    "than five million dollars, and cyber liability insurance of not less than ten "
    "million dollars. Certificates of insurance must be provided prior to contract "
    "execution and Alderwood must be named as an additional insured.",

    "The vendor shall indemnify Alderwood against any claim arising from the vendor's "
    "breach of its data protection obligations. Liability for a data protection breach "
    "shall not be subject to the general limitation of liability. Any proposed cap on "
    "data protection liability must be stated as an exception.",

    "Either party may terminate for material breach on thirty days' written notice "
    "where the breach remains uncured. Alderwood may additionally terminate for "
    "convenience on ninety days' written notice at any point after the first "
    "anniversary of the effective date. On termination the vendor must return or "
    "destroy all Alderwood data in accordance with the requirements of section 3.4.",
]

ATTESTATION = [
    "The undersigned, being duly authorised to bind the responding vendor, attests "
    "that the information provided in this response and its accompanying workbook is "
    "accurate and complete to the best of their knowledge; that the vendor has "
    "disclosed all material litigation, regulatory action, and security incidents as "
    "required by section 1; and that the pricing submitted shall remain valid for one "
    "hundred and twenty days from the response deadline.",

    "The undersigned further attests that no capability has been represented as "
    "Standard or Configuration where it is in fact unreleased, and acknowledges that "
    "a material misrepresentation may result in disqualification or, if discovered "
    "after award, termination for cause.",
]


def page_furniture(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillGray(0.45)
    canvas.drawString(
        0.9 * inch, letter[1] - 0.55 * inch,
        f"{RFP_META['buyer'].upper()} - CONFIDENTIAL - RFP {RFP_META['reference']}",
    )
    canvas.drawString(
        0.9 * inch, 0.55 * inch,
        f"{RFP_META['title']} - Issued {RFP_META['issued']}",
    )
    canvas.drawRightString(letter[0] - 0.9 * inch, 0.55 * inch, f"Page {doc.page}")
    canvas.setStrokeGray(0.8)
    canvas.line(0.9 * inch, letter[1] - 0.62 * inch, letter[0] - 0.9 * inch, letter[1] - 0.62 * inch)
    canvas.line(0.9 * inch, 0.7 * inch, letter[0] - 0.9 * inch, 0.7 * inch)
    canvas.restoreState()


def make_table(rows, widths, align_right_last=False):
    t = Table(rows, colWidths=widths, repeatRows=1)
    stylecmds = [
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
    ]
    if align_right_last:
        stylecmds.append(("ALIGN", (-1, 1), (-1, -1), "CENTER"))
    t.setStyle(TableStyle(stylecmds))
    return t


def main():
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=8)
    req_style = ParagraphStyle("Req", parent=body, leftIndent=0.42 * inch,
                               firstLineIndent=-0.42 * inch, spaceAfter=7)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=13, spaceBefore=15, spaceAfter=8,
                        textColor=colors.HexColor("#1F3864"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                        fontSize=10.5, spaceBefore=11, spaceAfter=5)
    cover_title = ParagraphStyle("CT", parent=styles["Title"], fontName="Helvetica-Bold",
                                 fontSize=22, leading=27)
    cover_meta = ParagraphStyle("CM", parent=body, alignment=TA_CENTER, fontSize=10.5,
                                spaceAfter=3)
    toc_style = ParagraphStyle("TOC", parent=body, spaceAfter=3, alignment=0)

    story = [
        Spacer(1, 1.7 * inch),
        Paragraph("Request for Proposal", cover_title),
        Paragraph(RFP_META["title"], cover_title),
        Spacer(1, 0.45 * inch),
        Paragraph(RFP_META["buyer"], cover_meta),
        Paragraph(f"Reference: {RFP_META['reference']}", cover_meta),
        Paragraph(f"Issued: {RFP_META['issued']}", cover_meta),
        Paragraph(f"Responses due: {RFP_META['due']}, {RFP_META['due_time']}", cover_meta),
        Spacer(1, 0.9 * inch),
        Paragraph(
            "This document and the accompanying response workbook are confidential and "
            "are provided solely for the purpose of preparing a response.", cover_meta),
        PageBreak(),
    ]

    # ---- table of contents (entries resemble requirement lines) ----
    story.append(Paragraph("Table of Contents", h1))
    toc = [
        "1.  Background and Scope",
        "2.  Procurement Timeline",
        "3.  Submission Instructions",
        "4.  Evaluation Criteria",
        "5.  Definitions",
        "6.  Response Format and Compliance Levels",
    ]
    for section in SECTIONS:
        toc.append(f"{int(section.number) + 6}.  {section.title}")
    toc += [
        "Appendix A.  Terms and Conditions",
        "Appendix B.  Insurance Requirements",
        "Appendix C.  Vendor Attestation",
    ]
    for line in toc:
        story.append(Paragraph(line, toc_style))

    story.append(PageBreak())
    story.append(Paragraph("1. Background and Scope", h1))
    story += [Paragraph(p, body) for p in BACKGROUND]

    story.append(Paragraph("2. Procurement Timeline", h1))
    story.append(make_table(TIMELINE, [4.0 * inch, 2.6 * inch]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Alderwood reserves the right to amend this timeline. Vendors that have "
        "registered an intent to respond shall be notified in writing of any change.",
        body))

    story.append(Paragraph("3. Submission Instructions", h1))
    story += [Paragraph(p, body) for p in SUBMISSION]

    story.append(Paragraph("4. Evaluation Criteria", h1))
    story.append(Paragraph(
        "Responses will be scored against the weighted criteria below. Alderwood may "
        "decline to progress any vendor scoring below sixty percent on information "
        "security and privacy irrespective of total score.", body))
    story.append(make_table(EVALUATION, [4.6 * inch, 2.0 * inch], align_right_last=True))

    story.append(PageBreak())
    story.append(Paragraph("5. Definitions", h1))
    story.append(Paragraph(
        "The following terms carry the meanings given below wherever they appear in "
        "this document or the accompanying workbook.", body))
    for term, meaning in GLOSSARY:
        story.append(Paragraph(f"<b>{term}.</b> {meaning}", body))

    story.append(Paragraph("6. Response Format and Compliance Levels", h1))
    story.append(Paragraph(
        "Every numbered requirement in sections 7 through 14 must receive one of the "
        "six compliance levels defined below, recorded in the response workbook, "
        "together with a supporting explanation. A compliance level given without an "
        "explanation shall be scored as Not Supported.", body))
    for level, definition in COMPLIANCE_DEFINITIONS:
        story.append(Paragraph(f"<b>{level}.</b> {definition}", body))

    # ---- requirements ----
    story.append(PageBreak())
    for section in SECTIONS:
        story.append(Paragraph(f"{int(section.number) + 6}. {section.title}", h1))
        if section.intro:
            story.append(Paragraph(section.intro, body))
        for sub in section.subsections:
            story.append(Paragraph(f"{sub.number}  {sub.title}", h2))
            for req in sub.items:
                marker = f"<b>{req.rid}</b>"
                tag = "" if req.priority == "Should" else f" <i>[{req.priority}]</i>"
                story.append(Paragraph(f"{marker}&nbsp;&nbsp;{req.text}{tag}", req_style))

    # ---- appendices ----
    story.append(PageBreak())
    story.append(Paragraph("Appendix A. Terms and Conditions", h1))
    story += [Paragraph(p, body) for p in TERMS]

    story.append(Paragraph("Appendix B. Insurance Requirements", h1))
    story.append(Paragraph(
        "Coverage limits stated in Appendix A are minimums. Alderwood may require "
        "higher limits where the vendor will process pharmacy-derived data. "
        "Certificates must be renewed annually for the duration of the agreement and "
        "provided to Alderwood without request.", body))

    story.append(Paragraph("Appendix C. Vendor Attestation", h1))
    story += [Paragraph(p, body) for p in ATTESTATION]
    story.append(Spacer(1, 30))
    sig = [
        ["Signature", ""],
        ["Name", ""],
        ["Title", ""],
        ["Vendor legal entity", ""],
        ["Date", ""],
    ]
    story.append(make_table(sig, [1.9 * inch, 4.7 * inch]))

    doc = SimpleDocTemplate(
        str(OUT), pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title=f"RFP {RFP_META['reference']} - {RFP_META['title']}",
        author=RFP_META["buyer"],
        subject=f"Request for Proposal - {RFP_META['title']}",
    )
    doc.build(story, onFirstPage=page_furniture, onLaterPages=page_furniture)

    total = sum(len(sub.items) for s in SECTIONS for sub in s.subsections)
    print(f"wrote {OUT} ({total} requirements)")


if __name__ == "__main__":
    main()
