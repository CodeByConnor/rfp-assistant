"""Generate the XLSX form of the Alderwood RFP fixture.

Shaped like a real enterprise RFP response workbook, including the structure
that breaks naive parsers:

  - 12 tabs, only 8 of which contain requirements. A parser must not treat
    Instructions, Pricing Workbook, Scoring Summary, or Exceptions Log as
    requirement tables.
  - a metadata block above the header row on every requirement tab
  - merged subsection banner rows interleaved with requirement rows
  - a worked EXAMPLE row on each requirement tab that must NOT be parsed
  - hierarchical requirement ids (4.2.3), not flat ones
  - buyer-owned columns (Priority, Weight, Score) interleaved with
    vendor-owned columns (Compliance Level, Comments, Cost Impact)
  - a locked-down dropdown on the compliance column
  - near-duplicate requirements across tabs (see requirements_data.dupe)

Formulas: the Score column and the Scoring Summary and Pricing Workbook tabs
are formula-driven, not precomputed, so the workbook recalculates as a vendor
fills it in.
"""

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).parent))
from requirements_data import (  # noqa: E402
    COMPLIANCE_DEFINITIONS,
    COMPLIANCE_LEVELS,
    PRIORITY_DEFINITIONS,
    RFP_META,
    SECTIONS,
)

OUT = Path(__file__).parent / "rfp-alderwood-retail.xlsx"

ARIAL = "Arial"
VENDOR_FILL = PatternFill("solid", fgColor="FFF2CC")   # vendor completes
BUYER_FILL = PatternFill("solid", fgColor="EDEDED")    # buyer-owned, do not edit
BANNER_FILL = PatternFill("solid", fgColor="D9E2F3")
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
TITLE_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# Compliance level -> score factor. Lives on Scoring Summary so the Score
# formulas reference a real cell range rather than hardcoding the factors.
SCORE_FACTORS = {
    "Standard": 1.0,
    "Configuration": 0.8,
    "Customization": 0.5,
    "Third-Party": 0.5,
    "Roadmap": 0.25,
    "Not Supported": 0.0,
}

REQ_COLUMNS = [
    ("Req ID", 10, "buyer"),
    ("Requirement", 74, "buyer"),
    ("Priority", 10, "buyer"),
    ("Weight", 9, "buyer"),
    ("Compliance Level", 18, "vendor"),
    ("Vendor Comments", 46, "vendor"),
    ("Supporting Doc Reference", 26, "vendor"),
    ("Cost Impact (USD)", 16, "vendor"),
    ("Score", 10, "buyer"),
]

EXAMPLE_ROW = [
    "EXAMPLE",
    "(Example row illustrating the expected response format. Do not submit a response against this row.)",
    "Must",
    5,
    "Configuration",
    "Supported in the current release. Requires an administrator to enable the feature and map source fields during onboarding.",
    "Admin Guide s.4.2, p.31",
    0,
]

METADATA_ROWS = [
    ("Issuing organization", RFP_META["buyer"]),
    ("RFP reference", RFP_META["reference"]),
    ("Issued", RFP_META["issued"]),
    ("Responses due", f"{RFP_META['due']}, {RFP_META['due_time']}"),
]

HEADER_ROW = 8          # requirement tabs: metadata rows 1-6, header at 8
EXAMPLE_AT = 9
FIRST_REQ_ROW = 10


def style(cell, *, bold=False, size=10, wrap=False, valign="top", italic=False, color=None):
    cell.font = Font(name=ARIAL, bold=bold, size=size, italic=italic, color=color)
    cell.alignment = Alignment(wrap_text=wrap, vertical=valign)
    return cell


def build_requirement_tab(ws, section):
    for idx, (title, width, _owner) in enumerate(REQ_COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(REQ_COLUMNS))
    title_cell = ws.cell(row=1, column=1, value=f"Section {section.number} - {section.title}")
    style(title_cell, bold=True, size=13)
    title_cell.fill = TITLE_FILL

    for offset, (label, value) in enumerate(METADATA_ROWS, start=2):
        style(ws.cell(row=offset, column=1, value=label), bold=True)
        style(ws.cell(row=offset, column=2, value=value))

    if section.intro:
        ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=len(REQ_COLUMNS))
        style(ws.cell(row=6, column=1, value=section.intro), wrap=True)
        ws.row_dimensions[6].height = 30

    for idx, (title, _w, _owner) in enumerate(REQ_COLUMNS, start=1):
        cell = ws.cell(row=HEADER_ROW, column=idx, value=title)
        cell.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.fill = HEADER_FILL
        cell.border = BORDER

    for idx, value in enumerate(EXAMPLE_ROW, start=1):
        cell = ws.cell(row=EXAMPLE_AT, column=idx, value=value)
        style(cell, wrap=True, italic=True, color="808080")
        cell.border = BORDER
    style(ws.cell(row=EXAMPLE_AT, column=9, value="(not scored)"), italic=True, color="808080")
    ws.cell(row=EXAMPLE_AT, column=9).border = BORDER
    ws.row_dimensions[EXAMPLE_AT].height = 28

    row = FIRST_REQ_ROW
    req_rows = []
    for sub in section.subsections:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(REQ_COLUMNS))
        banner = ws.cell(row=row, column=1, value=f"{sub.number}  {sub.title}")
        style(banner, bold=True)
        banner.fill = BANNER_FILL
        for col in range(1, len(REQ_COLUMNS) + 1):
            ws.cell(row=row, column=col).border = BORDER
        row += 1

        for req in sub.items:
            style(ws.cell(row=row, column=1, value=req.rid), bold=True)
            style(ws.cell(row=row, column=2, value=req.text), wrap=True)
            style(ws.cell(row=row, column=3, value=req.priority))
            style(ws.cell(row=row, column=4, value=req.weight))
            for col in (1, 2, 3, 4):
                ws.cell(row=row, column=col).fill = BUYER_FILL
            for col in (5, 6, 7, 8):
                cell = ws.cell(row=row, column=col)
                cell.fill = VENDOR_FILL
                style(cell, wrap=True)
            score = ws.cell(row=row, column=9)
            score.value = (
                f"=IFERROR(D{row}*INDEX('Scoring Summary'!$C$6:$C$11,"
                f"MATCH(E{row},'Scoring Summary'!$B$6:$B$11,0)),\"\")"
            )
            score.fill = BUYER_FILL
            style(score)
            score.number_format = "0.0"
            for col in range(1, len(REQ_COLUMNS) + 1):
                ws.cell(row=row, column=col).border = BORDER
            ws.row_dimensions[row].height = 30
            req_rows.append(row)
            row += 1

    dv = DataValidation(
        type="list",
        formula1='"' + ",".join(COMPLIANCE_LEVELS) + '"',
        allow_blank=True,
        showDropDown=False,
        errorTitle="Invalid compliance level",
        error="Select one of the six defined compliance levels. See the Instructions tab.",
    )
    ws.add_data_validation(dv)
    dv.add(f"E{req_rows[0]}:E{req_rows[-1]}")

    ws.freeze_panes = ws.cell(row=HEADER_ROW + 1, column=3)
    ws.auto_filter.ref = f"A{HEADER_ROW}:I{row - 1}"
    return req_rows[0], req_rows[-1], len(req_rows)


def build_vendor_profile_tab(ws, section):
    """Narrative tab - no compliance level, no scoring."""
    widths = [10, 82, 62]
    for idx, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w

    ws.merge_cells("A1:C1")
    c = ws.cell(row=1, column=1, value=f"Section {section.number} - {section.title}")
    style(c, bold=True, size=13)
    c.fill = TITLE_FILL
    for offset, (label, value) in enumerate(METADATA_ROWS, start=2):
        style(ws.cell(row=offset, column=1, value=label), bold=True)
        style(ws.cell(row=offset, column=2, value=value))
    ws.merge_cells("A6:C6")
    style(ws.cell(row=6, column=1, value=section.intro), wrap=True)
    ws.row_dimensions[6].height = 30

    for idx, title in enumerate(["Ref", "Question", "Vendor Response"], start=1):
        cell = ws.cell(row=HEADER_ROW, column=idx, value=title)
        cell.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.fill = HEADER_FILL
        cell.border = BORDER

    for idx, value in enumerate(
        ["EXAMPLE", "(Example row. Do not submit a response against this row.)",
         "Meridian Data, Inc., incorporated in Delaware, headquartered in Seattle, WA."],
        start=1,
    ):
        cell = ws.cell(row=EXAMPLE_AT, column=idx, value=value)
        style(cell, wrap=True, italic=True, color="808080")
        cell.border = BORDER

    row = FIRST_REQ_ROW
    count = 0
    for sub in section.subsections:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        banner = ws.cell(row=row, column=1, value=f"{sub.number}  {sub.title}")
        style(banner, bold=True)
        banner.fill = BANNER_FILL
        for col in range(1, 4):
            ws.cell(row=row, column=col).border = BORDER
        row += 1
        for req in sub.items:
            style(ws.cell(row=row, column=1, value=req.rid), bold=True)
            style(ws.cell(row=row, column=2, value=req.text), wrap=True)
            ws.cell(row=row, column=1).fill = BUYER_FILL
            ws.cell(row=row, column=2).fill = BUYER_FILL
            resp = ws.cell(row=row, column=3)
            resp.fill = VENDOR_FILL
            style(resp, wrap=True)
            for col in range(1, 4):
                ws.cell(row=row, column=col).border = BORDER
            ws.row_dimensions[row].height = 30
            count += 1
            row += 1

    ws.freeze_panes = ws.cell(row=HEADER_ROW + 1, column=1)
    return count


def build_instructions_tab(ws):
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 96

    style(ws["A1"], bold=True, size=16).value = (
        f"{RFP_META['buyer']} - Request for Proposal"
    )
    style(ws["A2"], bold=True, size=12).value = RFP_META["title"]

    meta = [
        ("RFP reference", RFP_META["reference"]),
        ("Issued", RFP_META["issued"]),
        ("Clarification questions due", RFP_META["questions_due"]),
        ("Responses due", f"{RFP_META['due']}, {RFP_META['due_time']}"),
        ("Submit to", RFP_META["contact"]),
    ]
    r = 4
    for label, value in meta:
        style(ws.cell(row=r, column=1, value=label), bold=True)
        style(ws.cell(row=r, column=2, value=value))
        r += 1

    r += 1
    style(ws.cell(row=r, column=1, value="How to complete this workbook"), bold=True, size=12)
    r += 1
    for line in [
        "Complete every shaded response cell on each of the eight requirement tabs.",
        "Columns shaded in cream are completed by the vendor. Columns shaded in grey are set by Alderwood and must not be edited.",
        "Each requirement tab carries an EXAMPLE row directly beneath the header. It is illustrative only and must not be answered.",
        "Where a requirement is answered elsewhere in this workbook, still provide a response. Cross-references alone will be scored as non-responsive.",
        "Exceptions to Alderwood's terms must be recorded on the Exceptions Log tab, not in the requirement comments.",
    ]:
        style(ws.cell(row=r, column=2, value=line), wrap=True)
        r += 1

    r += 1
    style(ws.cell(row=r, column=1, value="Compliance level definitions"), bold=True, size=12)
    r += 1
    for level, definition in COMPLIANCE_DEFINITIONS:
        style(ws.cell(row=r, column=1, value=level), bold=True)
        ws.cell(row=r, column=1).fill = VENDOR_FILL
        style(ws.cell(row=r, column=2, value=definition), wrap=True)
        r += 1

    r += 1
    style(ws.cell(row=r, column=1, value="Priority definitions"), bold=True, size=12)
    r += 1
    for level, definition in PRIORITY_DEFINITIONS:
        style(ws.cell(row=r, column=1, value=level), bold=True)
        style(ws.cell(row=r, column=2, value=definition), wrap=True)
        r += 1

    r += 1
    style(ws.cell(row=r, column=1, value="Tabs in this workbook"), bold=True, size=12)
    r += 1
    for tab, note in [
        ("Vendor Profile", "Narrative company information. Not compliance-scored."),
        ("Functional / Technical / Security / Privacy / Implementation / Support / Commercial",
         "Requirement tabs. Complete the compliance level and comments for every line item."),
        ("Pricing Workbook", "Five-year cost model. Complete the input cells only; totals are calculated."),
        ("Scoring Summary", "Calculated by Alderwood during evaluation. Do not edit."),
        ("Exceptions Log", "Record any exception to Alderwood's stated terms here."),
    ]:
        style(ws.cell(row=r, column=1, value=tab), bold=True, wrap=True)
        style(ws.cell(row=r, column=2, value=note), wrap=True)
        r += 1


def build_scoring_tab(ws, tab_ranges):
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 16

    style(ws["A1"], bold=True, size=14).value = "Scoring Summary"
    style(ws["A2"], wrap=True).value = (
        "Calculated by Alderwood during evaluation. Vendors must not edit this tab. "
        "Score per requirement = Weight x the compliance factor below."
    )

    style(ws["B5"], bold=True).value = "Compliance Level"
    style(ws["C5"], bold=True).value = "Score Factor"
    ws["B5"].fill = HEADER_FILL
    ws["C5"].fill = HEADER_FILL
    ws["B5"].font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
    ws["C5"].font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
    for offset, level in enumerate(COMPLIANCE_LEVELS, start=6):
        style(ws.cell(row=offset, column=2, value=level))
        c = ws.cell(row=offset, column=3, value=SCORE_FACTORS[level])
        style(c)
        c.number_format = "0.00"
        c.font = Font(name=ARIAL, size=10, color="0000FF")  # blue = hardcoded input
        ws.cell(row=offset, column=2).border = BORDER
        c.border = BORDER

    style(ws["A13"], wrap=True).value = (
        "Factors above are Alderwood evaluation inputs (shown in blue) and are the "
        "only hardcoded numbers on this tab. Every figure below is calculated."
    )

    head_row = 15
    for idx, title in enumerate(
        ["Section", "Max Possible", "Vendor Score", "Percent of Max"], start=1
    ):
        cell = ws.cell(row=head_row, column=idx, value=title)
        cell.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center")

    r = head_row + 1
    first = r
    for tab_name, (start, end) in tab_ranges.items():
        style(ws.cell(row=r, column=1, value=tab_name))
        style(ws.cell(row=r, column=2)).value = f"=SUM('{tab_name}'!D{start}:D{end})"
        style(ws.cell(row=r, column=3)).value = f"=SUM('{tab_name}'!I{start}:I{end})"
        style(ws.cell(row=r, column=4)).value = f"=IFERROR(C{r}/B{r},0)"
        ws.cell(row=r, column=4).number_format = "0.0%"
        for col in range(1, 5):
            ws.cell(row=r, column=col).border = BORDER
        r += 1

    style(ws.cell(row=r, column=1, value="Total"), bold=True)
    style(ws.cell(row=r, column=2), bold=True).value = f"=SUM(B{first}:B{r - 1})"
    style(ws.cell(row=r, column=3), bold=True).value = f"=SUM(C{first}:C{r - 1})"
    style(ws.cell(row=r, column=4), bold=True).value = f"=IFERROR(C{r}/B{r},0)"
    ws.cell(row=r, column=4).number_format = "0.0%"
    for col in range(1, 5):
        ws.cell(row=r, column=col).border = BORDER
        ws.cell(row=r, column=col).fill = BUYER_FILL


def build_pricing_tab(ws):
    for col, width in zip("ABCDEFG", [40, 16, 16, 16, 16, 16, 16]):
        ws.column_dimensions[col].width = width

    style(ws["A1"], bold=True, size=14).value = "Pricing Workbook - Five Year Total Cost of Ownership"
    style(ws["A2"], wrap=True).value = (
        "Complete the cream input cells only. All totals are calculated. "
        "State all amounts in US dollars, exclusive of sales tax."
    )

    style(ws["A4"], bold=True, size=12).value = "Inputs"
    inputs = [
        ("Tracked customer profiles (year 1)", 2100000, "0,000"),
        ("Assumed annual profile growth", 0.20, "0.0%"),
        ("Annual subscription fee (year 1)", None, "$#,##0"),
        ("Annual uplift at renewal", None, "0.0%"),
        ("One-time implementation fee", None, "$#,##0"),
        ("Annual support and success fee", None, "$#,##0"),
        ("Overage rate per profile above tier", None, "$#,##0.0000"),
        ("Profiles included in contracted tier", None, "0,000"),
    ]
    r = 5
    for label, value, fmt in inputs:
        style(ws.cell(row=r, column=1, value=label), bold=True)
        cell = ws.cell(row=r, column=2, value=value)
        style(cell)
        cell.number_format = fmt
        cell.fill = VENDOR_FILL if value is None else BUYER_FILL
        cell.font = Font(name=ARIAL, size=10, color="0000FF")
        cell.border = BORDER
        r += 1
    style(ws.cell(row=r, column=1, value="Cells shaded cream are vendor inputs. The two grey cells are Alderwood's stated volume assumptions and must not be changed."), wrap=True)

    profiles_r, growth_r = 5, 6
    sub_r, uplift_r, impl_r, support_r, over_rate_r, tier_r = 7, 8, 9, 10, 11, 12

    head = 16
    style(ws.cell(row=head, column=1, value="Cost Line"), bold=True)
    ws.cell(row=head, column=1).fill = HEADER_FILL
    ws.cell(row=head, column=1).font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
    for i in range(5):
        c = ws.cell(row=head, column=2 + i, value=f"Year {i + 1}")
        c.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal="center")
        c.border = BORDER
    c = ws.cell(row=head, column=7, value="5-Year Total")
    c.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
    c.fill = HEADER_FILL
    c.border = BORDER

    rows = {}
    r = head + 1

    style(ws.cell(row=r, column=1, value="Tracked profiles"), bold=True)
    for i in range(5):
        col = get_column_letter(2 + i)
        if i == 0:
            ws[f"{col}{r}"] = f"=$B${profiles_r}"
        else:
            prev = get_column_letter(1 + i)
            ws[f"{col}{r}"] = f"={prev}{r}*(1+$B${growth_r})"
        style(ws[f"{col}{r}"])
        ws[f"{col}{r}"].number_format = "0,000"
        ws[f"{col}{r}"].border = BORDER
    rows["profiles"] = r
    r += 1

    style(ws.cell(row=r, column=1, value="Subscription fee"), bold=True)
    for i in range(5):
        col = get_column_letter(2 + i)
        if i == 0:
            ws[f"{col}{r}"] = f"=$B${sub_r}"
        else:
            prev = get_column_letter(1 + i)
            ws[f"{col}{r}"] = f"={prev}{r}*(1+$B${uplift_r})"
        style(ws[f"{col}{r}"])
        ws[f"{col}{r}"].number_format = "$#,##0"
        ws[f"{col}{r}"].border = BORDER
    rows["sub"] = r
    r += 1

    style(ws.cell(row=r, column=1, value="Implementation (one time)"), bold=True)
    for i in range(5):
        col = get_column_letter(2 + i)
        ws[f"{col}{r}"] = f"=$B${impl_r}" if i == 0 else 0
        style(ws[f"{col}{r}"])
        ws[f"{col}{r}"].number_format = "$#,##0;($#,##0);-"
        ws[f"{col}{r}"].border = BORDER
    rows["impl"] = r
    r += 1

    style(ws.cell(row=r, column=1, value="Support and success fee"), bold=True)
    for i in range(5):
        col = get_column_letter(2 + i)
        ws[f"{col}{r}"] = f"=$B${support_r}"
        style(ws[f"{col}{r}"])
        ws[f"{col}{r}"].number_format = "$#,##0"
        ws[f"{col}{r}"].border = BORDER
    rows["support"] = r
    r += 1

    style(ws.cell(row=r, column=1, value="Overage charges"), bold=True)
    pr = rows["profiles"]
    for i in range(5):
        col = get_column_letter(2 + i)
        ws[f"{col}{r}"] = f"=MAX(0,{col}{pr}-$B${tier_r})*$B${over_rate_r}"
        style(ws[f"{col}{r}"])
        ws[f"{col}{r}"].number_format = "$#,##0;($#,##0);-"
        ws[f"{col}{r}"].border = BORDER
    rows["over"] = r
    r += 1

    style(ws.cell(row=r, column=1, value="Total annual cost"), bold=True)
    ws.cell(row=r, column=1).fill = BUYER_FILL
    for i in range(5):
        col = get_column_letter(2 + i)
        ws[f"{col}{r}"] = (
            f"={col}{rows['sub']}+{col}{rows['impl']}+{col}{rows['support']}+{col}{rows['over']}"
        )
        style(ws[f"{col}{r}"], bold=True)
        ws[f"{col}{r}"].number_format = "$#,##0"
        ws[f"{col}{r}"].fill = BUYER_FILL
        ws[f"{col}{r}"].border = BORDER
    ws[f"G{r}"] = f"=SUM(B{r}:F{r})"
    style(ws[f"G{r}"], bold=True)
    ws[f"G{r}"].number_format = "$#,##0"
    ws[f"G{r}"].fill = BUYER_FILL
    ws[f"G{r}"].border = BORDER

    style(ws.cell(row=r + 2, column=1, value="Five-year total cost of ownership"), bold=True, size=12)
    ws[f"B{r + 2}"] = f"=G{r}"
    style(ws[f"B{r + 2}"], bold=True, size=12)
    ws[f"B{r + 2}"].number_format = "$#,##0"

    style(ws.cell(row=r + 4, column=1, value=(
        "Profile growth of 20 percent per year is Alderwood's planning assumption, "
        "stated in section 3.2.2 of the requirements. Overage is charged only on "
        "profiles above the contracted tier."
    )), wrap=True)


def build_exceptions_tab(ws):
    for col, width in zip("ABCDE", [10, 22, 60, 60, 18]):
        ws.column_dimensions[col].width = width
    style(ws["A1"], bold=True, size=14).value = "Exceptions Log"
    style(ws["A2"], wrap=True).value = (
        "Record every exception to Alderwood's stated requirements or contractual terms here. "
        "An exception recorded only in a requirement comment will not be considered."
    )
    for idx, title in enumerate(
        ["Item", "Requirement Ref", "Exception Taken", "Proposed Alternative", "Commercial Impact"],
        start=1,
    ):
        cell = ws.cell(row=4, column=idx, value=title)
        cell.font = Font(name=ARIAL, bold=True, size=10, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, horizontal="center")
        cell.border = BORDER
    example = [
        "EXAMPLE", "4.6.2",
        "(Example row. Do not submit against this row.) Vendor cannot meet the 24-hour incident notification period.",
        "Vendor proposes notification within 72 hours of confirmation.",
        "None",
    ]
    for idx, value in enumerate(example, start=1):
        cell = ws.cell(row=5, column=idx, value=value)
        style(cell, wrap=True, italic=True, color="808080")
        cell.border = BORDER
    for row in range(6, 26):
        for col in range(1, 6):
            cell = ws.cell(row=row, column=col)
            cell.fill = VENDOR_FILL
            cell.border = BORDER
            style(cell, wrap=True)


def main():
    wb = Workbook()
    instructions = wb.active
    instructions.title = "Instructions"
    build_instructions_tab(instructions)

    tab_ranges = {}
    counts = {}
    for section in SECTIONS:
        ws = wb.create_sheet(section.tab)
        if section.tab == "Vendor Profile":
            counts[section.tab] = build_vendor_profile_tab(ws, section)
        else:
            start, end, n = build_requirement_tab(ws, section)
            tab_ranges[section.tab] = (start, end)
            counts[section.tab] = n

    build_pricing_tab(wb.create_sheet("Pricing Workbook"))
    build_scoring_tab(wb.create_sheet("Scoring Summary"), tab_ranges)
    build_exceptions_tab(wb.create_sheet("Exceptions Log"))

    wb.save(OUT)
    total = sum(counts.values())
    print(f"wrote {OUT}")
    print(f"  tabs: {len(wb.sheetnames)} -> {wb.sheetnames}")
    for tab, n in counts.items():
        print(f"  {tab:<16} {n:>3} items")
    print(f"  total line items: {total}")


if __name__ == "__main__":
    main()
