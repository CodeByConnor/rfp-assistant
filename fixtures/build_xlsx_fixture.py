"""Generate the XLSX form of the Alderwood RFP fixture.

The output is deliberately shaped like a real vendor-supplied RFP workbook,
including the things that break naive parsers: a metadata block above the
header row, an Instructions sheet in front of the data sheet, merged section
banner rows interleaved with requirement rows, and a worked example row that
must NOT be parsed as a requirement.
"""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ARIAL = "Arial"
RESPONSE_FILL = PatternFill("solid", fgColor="FFF2CC")
BANNER_FILL = PatternFill("solid", fgColor="D9D9D9")
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# (kind, payload): "section" banners are not requirements; "req" rows are.
ROWS = [
    ("section", "SECTION A - COMPANY & PRODUCT OVERVIEW"),
    ("req", ("A1", "Describe your platform's core identity resolution capability across web, mobile, and offline (in-store POS) data sources.")),
    ("req", ("A2", "Describe your data model and any limits on custom customer attributes.")),
    ("req", ("A3", "Confirm whether your platform is offered as single-tenant / dedicated infrastructure, or multi-tenant SaaS only. Alderwood's security team has a stated preference for single-tenant deployments for PII-heavy workloads.")),
    ("req", ("A4", "What regions can customer data be hosted in? Alderwood requires U.S. data residency at minimum and may expand into Canada within 18 months.")),
    ("section", "SECTION B - SECURITY & COMPLIANCE"),
    ("req", ("B1", "List all current security certifications (SOC 2, ISO 27001, PCI DSS, etc.) and provide certificate/report availability.")),
    ("req", ("B2", "Describe encryption of data at rest and in transit.")),
    ("req", ("B3", "Describe supported single sign-on (SSO) protocols for admin console access.")),
    ("req", ("B4", "Do you support SCIM-based automated user provisioning/deprovisioning?")),
    ("req", ("B5", "Describe role-based access control (RBAC) capabilities.")),
    ("req", ("B6", "Describe your penetration testing program and cadence.")),
    ("req", ("B7", "Given that Alderwood's loyalty program captures purchase data from in-store pharmacy counters, is your platform HIPAA compliant, and will you sign a Business Associate Agreement (BAA)?")),
    ("req", ("B8", "Describe your disaster recovery capabilities, including RPO and RTO.")),
    ("req", ("B9", "Do you support multi-factor authentication (MFA) for platform admin accounts?")),
    ("req", ("B10", "Describe your approach to sub-processors and third-party data sharing disclosure.")),
    ("section", "SECTION C - DATA PRIVACY & RESIDENCY"),
    ("req", ("C1", "Confirm GDPR compliance and availability of a Data Processing Agreement (DPA), in case Alderwood expands to EU markets in the future.")),
    ("req", ("C2", "Confirm CCPA compliance, including support for consumer data deletion and access requests.")),
    ("req", ("C3", "If Alderwood expands operations into Canada within the next 18 months, can customer data be hosted to meet Canadian data residency expectations?")),
    ("req", ("C4", "What is your default and maximum configurable data retention period?")),
    ("section", "SECTION D - INTEGRATIONS & TECHNICAL ARCHITECTURE"),
    ("req", ("D1", "Confirm native integration support for Salesforce Marketing Cloud.")),
    ("req", ("D2", "Confirm native integration support for Shopify Plus.")),
    ("req", ("D3", "Describe support for real-time (sub-minute latency) audience segmentation and activation.")),
    ("req", ("D4", "Do you offer a managed connector for streaming raw event data into a Kafka topic for downstream consumption by Alderwood's data engineering team?")),
    ("req", ("D5", "Describe available REST APIs and SDKs for custom event ingestion.")),
    ("req", ("D6", "Describe reverse ETL capabilities to sync computed segments into a data warehouse (Alderwood uses Snowflake).")),
    ("section", "SECTION E - RELIABILITY, SLA & SUPPORT"),
    ("req", ("E1", "What uptime SLA do you offer, and what remedy is provided for SLA breaches?")),
    ("req", ("E2", "Describe support response time commitments by severity level for your highest support tier.")),
    ("req", ("E3", "Is 24/7 support available, and through which channels?")),
    ("req", ("E4", "Will Alderwood be assigned a dedicated Customer Success Manager (CSM) and/or Technical Account Manager (TAM)?")),
    ("section", "SECTION F - IMPLEMENTATION & CHANGE MANAGEMENT"),
    ("req", ("F1", "Describe your typical implementation timeline for a customer of Alderwood's size and complexity.")),
    ("req", ("F2", "What professional services or implementation support is included versus billed separately?")),
    ("section", "SECTION G - CORPORATE RESPONSIBILITY"),
    ("req", ("G1", "Describe your company's environmental sustainability program, including any data center carbon footprint commitments or offsets.")),
    ("section", "SECTION H - COMMERCIAL TERMS"),
    ("req", ("H1", "Provide pricing for a deployment covering approximately 2.1 million tracked customer profiles, including any volume discount structure.")),
    ("req", ("H2", "Describe your overage billing policy if tracked profile volume exceeds the contracted tier mid-term.")),
]


def style_cell(cell, *, bold=False, size=10, wrap=False, valign="top"):
    cell.font = Font(name=ARIAL, bold=bold, size=size)
    cell.alignment = Alignment(wrap_text=wrap, vertical=valign)
    return cell


def build_requirements_sheet(ws):
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 82
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 46

    ws.merge_cells("A1:D1")
    style_cell(ws["A1"], bold=True, size=14).value = (
        "Alderwood Retail Group - Customer Data Platform RFP"
    )
    style_cell(ws["A2"]).value = "RFP Reference: ARG-CDP-2026-014"
    style_cell(ws["A3"]).value = "Issued: 2026-07-01"
    style_cell(ws["A4"]).value = "Response Due: 2026-08-15"
    ws.merge_cells("A5:D5")
    style_cell(ws["A5"], wrap=True).value = (
        "Vendors: complete the shaded columns for every numbered requirement. "
        "Valid responses are Yes, Partial, No, or Planned/Roadmap."
    )

    header_row = 7
    for col, title in enumerate(
        ["Req ID", "Requirement", "Vendor Response", "Vendor Comments"], start=1
    ):
        cell = ws.cell(row=header_row, column=col, value=title)
        style_cell(cell, bold=True, wrap=True, valign="center")
        cell.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.border = BORDER

    example_row = header_row + 1
    ws.cell(row=example_row, column=1, value="EXAMPLE")
    ws.cell(
        row=example_row,
        column=2,
        value="(Example row - illustrates the expected response format. Do not submit a response to this row.)",
    )
    ws.cell(row=example_row, column=3, value="Yes")
    ws.cell(
        row=example_row,
        column=4,
        value="Full CSV/Parquet export is available via the admin console and API at no additional cost.",
    )
    for col in range(1, 5):
        cell = ws.cell(row=example_row, column=col)
        style_cell(cell, wrap=True)
        cell.font = Font(name=ARIAL, size=10, italic=True, color="808080")
        cell.border = BORDER

    row = example_row + 1
    first_data_row = row
    for kind, payload in ROWS:
        if kind == "section":
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            cell = ws.cell(row=row, column=1, value=payload)
            style_cell(cell, bold=True)
            cell.fill = BANNER_FILL
            for col in range(1, 5):
                ws.cell(row=row, column=col).border = BORDER
        else:
            req_id, text = payload
            style_cell(ws.cell(row=row, column=1, value=req_id), bold=True)
            style_cell(ws.cell(row=row, column=2, value=text), wrap=True)
            for col in (3, 4):
                cell = ws.cell(row=row, column=col)
                cell.fill = RESPONSE_FILL
                style_cell(cell, wrap=True)
            for col in range(1, 5):
                ws.cell(row=row, column=col).border = BORDER
            ws.row_dimensions[row].height = 30
        row += 1

    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    return first_data_row, row - 1


def build_instructions_sheet(ws, data_range):
    first_data_row, last_data_row = data_range
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 62

    style_cell(ws["A1"], bold=True, size=14).value = "Response Instructions"
    style_cell(ws["A3"], bold=True).value = "Issuing organization"
    style_cell(ws["B3"]).value = "Alderwood Retail Group"
    style_cell(ws["A4"], bold=True).value = "RFP reference"
    style_cell(ws["B4"]).value = "ARG-CDP-2026-014"
    style_cell(ws["A5"], bold=True).value = "Response due"
    style_cell(ws["B5"]).value = "2026-08-15"

    style_cell(ws["A7"], bold=True, size=12).value = "Legend - cells to complete"
    legend = [
        ("Shaded cells (Requirements!C:D)", "Vendor completes these. All other cells are read-only."),
        ("Vendor Response", "One of: Yes / Partial / No / Planned/Roadmap"),
        ("Vendor Comments", "Free text. Cite supporting documentation where available."),
        ("EXAMPLE row", "Illustrative only - do not submit a response for it."),
    ]
    for offset, (label, meaning) in enumerate(legend, start=8):
        style_cell(ws[f"A{offset}"], bold=True).value = label
        style_cell(ws[f"B{offset}"], wrap=True).value = meaning
    ws[f"A8"].fill = RESPONSE_FILL

    style_cell(ws["A14"], bold=True, size=12).value = "Completion tracker"
    style_cell(ws["A15"], bold=True).value = "Total requirements"
    style_cell(ws["B15"]).value = (
        f"=COUNTA(Requirements!B{first_data_row}:B{last_data_row})"
    )
    style_cell(ws["A16"], bold=True).value = "Responses provided"
    style_cell(ws["B16"]).value = (
        f"=COUNTA(Requirements!C{first_data_row}:C{last_data_row})"
    )
    style_cell(ws["A17"], bold=True).value = "Percent complete"
    style_cell(ws["B17"]).value = "=IFERROR(B16/B15,0)"
    ws["B17"].number_format = "0.0%"

    style_cell(ws["A19"], wrap=True).value = (
        "Counts are taken over column B, which is empty on merged section banner rows "
        "(their merge anchor is column A), so banners are excluded. The EXAMPLE row "
        "sits above the counted range and is excluded as well."
    )


def main():
    wb = Workbook()
    instructions = wb.active
    instructions.title = "Instructions"
    requirements = wb.create_sheet("Requirements")

    data_range = build_requirements_sheet(requirements)
    build_instructions_sheet(instructions, data_range)

    out = "/Users/Connor/rfp-assistant/fixtures/rfp-alderwood-retail.xlsx"
    wb.save(out)
    print(f"wrote {out} (requirement rows {data_range[0]}-{data_range[1]})")


if __name__ == "__main__":
    main()
