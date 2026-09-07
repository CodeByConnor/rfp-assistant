"""Generate the PDF form of the Alderwood RFP fixture.

This is the hard parsing case on purpose. Requirements are embedded in flowing
numbered prose rather than table rows, so a structural parser cannot recover
them and the LLM fallback path has to. It also carries the hazards real RFP
PDFs carry:

  - a cover page whose metadata is not a requirement
  - background prose containing "must"/"shall" sentences that are NOT
    requirements (a keyword-matching parser will over-extract these)
  - repeating page headers/footers that interleave into extracted text
  - an appendix of submission instructions, also full of "must" distractors

Not exercised here: a requirement whose text breaks across a page boundary.
ReportLab reflows a paragraph onto the next page rather than splitting it, and
forcing a split needs a requirement longer than a full page, which no real RFP
contains. If that case matters later, hand-author a PDF for it rather than
distorting this one.

Requirement IDs match the .md and .xlsx fixtures, so fixtures/gold-answers.json
applies unchanged to all three formats.
"""

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

OUT = "/Users/Connor/rfp-assistant/fixtures/rfp-alderwood-retail.pdf"

SECTIONS = [
    ("Section A - Company and Product Overview", [
        ("A1", "Describe your platform's core identity resolution capability across web, mobile, and offline (in-store point-of-sale) data sources. Vendors should explain whether matching is deterministic, probabilistic, or both."),
        ("A2", "Describe your data model and any limits on custom customer attributes."),
        ("A3", "Confirm whether your platform is offered as single-tenant or dedicated infrastructure, or as multi-tenant SaaS only. Alderwood's security team has a stated preference for single-tenant deployments for PII-heavy workloads."),
        ("A4", "What regions can customer data be hosted in? Alderwood requires U.S. data residency at minimum and may expand into Canada within 18 months."),
    ]),
    ("Section B - Security and Compliance", [
        ("B1", "List all current security certifications, including SOC 2, ISO 27001, and PCI DSS where applicable, and state the availability of the corresponding certificate or audit report."),
        ("B2", "Describe encryption of data at rest and in transit, including key management practices."),
        ("B3", "Describe supported single sign-on protocols for administrative console access."),
        ("B4", "Do you support SCIM-based automated user provisioning and deprovisioning?"),
        ("B5", "Describe role-based access control capabilities, including whether custom roles are supported. Alderwood expects to provision approximately 240 named users across its marketing, analytics, store operations, and loyalty teams, and requires that access to personally identifiable loyalty data be restricted to a named subset of those users. Your response should state which roles are available out of the box, whether custom roles may be defined by an administrator without vendor involvement, and whether role assignment can be delegated to a departmental administrator rather than a global administrator."),
        ("B6", "Describe your penetration testing program and its cadence, and state whether results are shareable."),
        ("B7", "Alderwood's loyalty program captures purchase data originating from 22 in-store pharmacy counters. Is your platform HIPAA compliant, and will you execute a Business Associate Agreement?"),
        ("B8", "Describe your disaster recovery capabilities, including stated Recovery Point Objective and Recovery Time Objective."),
        ("B9", "Do you support multi-factor authentication for platform administrator accounts?"),
        ("B10", "Describe your approach to sub-processors and to disclosure of third-party data sharing."),
    ]),
    ("Section C - Data Privacy and Residency", [
        ("C1", "Confirm GDPR compliance and the availability of a Data Processing Agreement, in the event Alderwood expands into EU markets."),
        ("C2", "Confirm CCPA compliance, including support for consumer data deletion and access requests."),
        ("C3", "If Alderwood expands operations into Canada within the next 18 months, can customer data be hosted so as to meet Canadian data residency expectations?"),
        ("C4", "What is your default data retention period, and what is the maximum configurable retention period?"),
    ]),
    ("Section D - Integrations and Technical Architecture", [
        ("D1", "Confirm native integration support for Salesforce Marketing Cloud, which Alderwood uses for email and SMS campaign execution."),
        ("D2", "Confirm native integration support for Shopify Plus."),
        ("D3", "Describe support for real-time audience segmentation and activation at sub-minute latency."),
        ("D4", "Do you offer a managed connector for streaming raw event data into a Kafka topic for downstream consumption by Alderwood's data engineering team?"),
        ("D5", "Describe the REST APIs and client SDKs available for custom event ingestion."),
        ("D6", "Describe reverse ETL capabilities for syncing computed segments into a data warehouse. Alderwood uses Snowflake."),
    ]),
    ("Section E - Reliability, Service Levels, and Support", [
        ("E1", "What uptime service level agreement do you offer, and what remedy is provided in the event of a breach?"),
        ("E2", "Describe support response time commitments by severity level for your highest support tier."),
        ("E3", "Is 24/7 support available, and through which channels?"),
        ("E4", "Will Alderwood be assigned a dedicated Customer Success Manager or Technical Account Manager?"),
    ]),
    ("Section F - Implementation and Change Management", [
        ("F1", "Describe your typical implementation timeline for a customer of Alderwood's size and data source complexity."),
        ("F2", "What professional services or implementation support is included in the subscription versus billed separately?"),
    ]),
    ("Section G - Corporate Responsibility", [
        ("G1", "Describe your company's environmental sustainability program, including any data center carbon footprint commitments or offset purchases."),
    ]),
    ("Section H - Commercial Terms", [
        ("H1", "Provide pricing for a deployment covering approximately 2.1 million tracked customer profiles, including any volume discount structure."),
        ("H2", "Describe your overage billing policy in the event tracked profile volume exceeds the contracted tier mid-term."),
    ]),
]

BACKGROUND = [
    "Alderwood Retail Group operates 118 grocery and general-merchandise stores across "
    "the Pacific Northwest and Mountain West, together with an e-commerce storefront "
    "hosted on Shopify Plus. Its loyalty program has 2.1 million enrolled members, and "
    "captures transaction data from all store formats, including 22 in-store pharmacy "
    "counters.",

    "Alderwood is evaluating customer data platform vendors in order to unify online, "
    "in-store, and loyalty data into a single customer profile, and to drive marketing "
    "personalization from that profile. Campaign execution today runs through Salesforce "
    "Marketing Cloud, and the analytics team operates a Snowflake warehouse.",

    # Deliberate distractors: obligation language in non-requirement prose.
    "All vendors must be incorporated within the United States or Canada and must have "
    "been operating continuously for no fewer than three years as of the response "
    "deadline. Proposals shall be submitted in electronic form only. Alderwood shall "
    "not be liable for any costs incurred by a vendor in preparing its response, and "
    "reserves the right to reject any or all proposals without stated cause.",

    "Vendors should respond to each numbered requirement below with one of the following "
    "dispositions: Yes, Partial, No, or Planned/Roadmap, followed by a brief supporting "
    "explanation. A disposition given without explanation may be scored as non-responsive.",
]

APPENDIX = [
    "Appendix A - Submission Instructions",

    "Responses must be submitted as a single PDF document to procurement@alderwoodretail.example "
    "no later than 5:00 p.m. Pacific Time on 15 August 2026. Late submissions shall not be "
    "considered. Each response must include the RFP reference number ARG-CDP-2026-014 in the "
    "subject line.",

    "Questions regarding this RFP must be submitted in writing no later than 25 July 2026. "
    "Alderwood will publish consolidated answers to all vendors who have registered intent "
    "to respond. Vendors must not contact Alderwood store or marketing personnel directly "
    "regarding this solicitation.",

    "Shortlisted vendors shall be invited to a technical demonstration during the week of "
    "1 September 2026. The demonstration must cover identity resolution and segment "
    "activation using a representative sample of Alderwood's own data under a mutual "
    "non-disclosure agreement.",
]


def page_furniture(canvas, doc):
    """Repeating header/footer - shows up as noise in extracted text."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillGray(0.45)
    canvas.drawString(
        0.9 * inch, letter[1] - 0.55 * inch,
        "ALDERWOOD RETAIL GROUP - CONFIDENTIAL - RFP ARG-CDP-2026-014",
    )
    canvas.drawString(
        0.9 * inch, 0.55 * inch,
        "Customer Data Platform RFP - Issued 1 July 2026",
    )
    canvas.drawRightString(
        letter[0] - 0.9 * inch, 0.55 * inch, f"Page {doc.page}",
    )
    canvas.setStrokeGray(0.8)
    canvas.line(0.9 * inch, letter[1] - 0.62 * inch, letter[0] - 0.9 * inch, letter[1] - 0.62 * inch)
    canvas.line(0.9 * inch, 0.7 * inch, letter[0] - 0.9 * inch, 0.7 * inch)
    canvas.restoreState()


def main():
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10,
        leading=14.5, alignment=TA_JUSTIFY, spaceAfter=9,
    )
    req = ParagraphStyle("Req", parent=body, leftIndent=0.32 * inch, firstLineIndent=-0.32 * inch)
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13,
        spaceBefore=16, spaceAfter=8,
    )
    cover_title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=25,
    )
    cover_meta = ParagraphStyle(
        "CoverMeta", parent=body, alignment=1, fontSize=10.5, spaceAfter=3,
    )

    story = [
        Spacer(1, 1.9 * inch),
        Paragraph("Request for Proposal", cover_title),
        Paragraph("Customer Data Platform", cover_title),
        Spacer(1, 0.5 * inch),
        Paragraph("Alderwood Retail Group", cover_meta),
        Paragraph("RFP Reference: ARG-CDP-2026-014", cover_meta),
        Paragraph("Issued: 1 July 2026", cover_meta),
        Paragraph("Responses Due: 15 August 2026, 5:00 p.m. Pacific", cover_meta),
        PageBreak(),
        Paragraph("1. Background and Scope", h1),
    ]
    story += [Paragraph(p, body) for p in BACKGROUND]
    story.append(Paragraph("2. Requirements", h1))

    for heading, items in SECTIONS:
        story.append(Paragraph(heading, h1))
        for req_id, text in items:
            story.append(Paragraph(f"<b>{req_id}.</b>&nbsp;&nbsp;{text}", req))

    story.append(PageBreak())
    story.append(Paragraph(APPENDIX[0], h1))
    story += [Paragraph(p, body) for p in APPENDIX[1:]]

    doc = SimpleDocTemplate(
        OUT, pagesize=letter,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title="RFP ARG-CDP-2026-014 - Customer Data Platform",
        author="Alderwood Retail Group",
        subject="Request for Proposal - Customer Data Platform",
    )
    doc.build(story, onFirstPage=page_furniture, onLaterPages=page_furniture)

    total = sum(len(items) for _, items in SECTIONS)
    print(f"wrote {OUT} ({total} requirements)")


if __name__ == "__main__":
    main()
