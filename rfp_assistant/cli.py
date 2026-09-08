"""Command line entry point.

    python -m rfp_assistant parse fixtures/rfp-alderwood-retail.xlsx
    python -m rfp_assistant parse <file> --json > requirements.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .parsers import UnsupportedFormat, parse, parse_pdf_detailed, requirement_tabs


def _cmd_parse(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2

    try:
        requirements = parse(path)
    except UnsupportedFormat as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        json.dump([asdict(r) for r in requirements], sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"{path.name}: {len(requirements)} requirements")

    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        print(f"  requirement tabs: {', '.join(requirement_tabs(path))}")
    if path.suffix.lower() == ".pdf":
        detail = parse_pdf_detailed(path)
        print(f"  pages: {detail.pages}   body-line coverage: {detail.coverage:.1%}")
        if detail.coverage < 0.3:
            print(
                "  warning: low coverage. The document's requirement numbering may\n"
                "           not have been recognised; consider an LLM extraction pass.",
                file=sys.stderr,
            )

    by_section = Counter(r.section for r in requirements)
    print("\n  section  count  title")
    seen: dict[str, str] = {}
    for r in requirements:
        seen.setdefault(r.section, r.section_title)
    for section in sorted(by_section, key=lambda s: int(s) if s.isdigit() else 0):
        print(f"  {section:>7}  {by_section[section]:>5}  {seen[section]}")

    missing_priority = sum(1 for r in requirements if r.priority is None)
    if missing_priority:
        print(f"\n  {missing_priority} requirements carry no priority in this document")

    if args.show:
        print()
        for r in requirements[: args.show]:
            print(f"  [{r.locator}] {r.rid}  {r.text[:96]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rfp_assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="extract requirements from an RFP document")
    p.add_argument("path")
    p.add_argument("--json", action="store_true", help="emit requirements as JSON")
    p.add_argument("--show", type=int, default=0, metavar="N", help="print first N")
    p.set_defaults(func=_cmd_parse)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
