"""Generate the Markdown form of the Alderwood RFP fixture.

This is the control format: clean structure, no hazards. A parser that cannot
get 248/248 here has a bug unrelated to document format, which makes it the
right thing to debug against before touching the xlsx or pdf paths.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from requirements_data import RFP_META, SECTIONS, all_requirements  # noqa: E402

OUT = Path(__file__).parent / "rfp-alderwood-retail.md"


def main():
    lines = [
        f"# Request for Proposal: {RFP_META['title']}",
        "",
        f"**Issuing organization:** {RFP_META['buyer']}  ",
        f"**RFP reference:** {RFP_META['reference']}  ",
        f"**Issued:** {RFP_META['issued']}  ",
        f"**Clarification questions due:** {RFP_META['questions_due']}  ",
        f"**Responses due:** {RFP_META['due']}, {RFP_META['due_time']}  ",
        f"**Submit to:** {RFP_META['contact']}",
        "",
        "> Generated from `fixtures/requirements_data.py`. Do not edit by hand —",
        "> edit the data module and re-run `build_md_fixture.py`.",
        "",
        "Respond to every numbered requirement with one of: **Standard**,",
        "**Configuration**, **Customization**, **Third-Party**, **Roadmap**, or",
        "**Not Supported**, together with a supporting explanation.",
        "",
        "---",
        "",
    ]

    for section in SECTIONS:
        lines.append(f"## Section {section.number} — {section.title}")
        lines.append("")
        if section.intro:
            lines.append(section.intro)
            lines.append("")
        for sub in section.subsections:
            lines.append(f"### {sub.number} {sub.title}")
            lines.append("")
            for req in sub.items:
                lines.append(f"**{req.rid}** _[{req.priority}, weight {req.weight}]_  ")
                lines.append(f"{req.text}")
                lines.append("")
        lines.append("---")
        lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(all_requirements())} requirements)")


if __name__ == "__main__":
    main()
