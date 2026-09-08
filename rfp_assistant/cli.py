"""Command line entry point.

    python -m rfp_assistant parse <file>
    python -m rfp_assistant eval-retrieval
    python -m rfp_assistant respond <file>              # offline, free
    python -m rfp_assistant respond <file> --live       # costs money, asks first

Spending safety: `respond` runs against the offline stub unless `--live` is
passed, and `--live` prints an estimate and requires confirmation before the
first call. `--yes` skips the prompt for non-interactive use, and `--limit`
caps how many requirements are sent.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .classify import classify_all
from .evaluate import evaluate_retrieval
from .knowledge import INTERNAL, PUBLIC, load_knowledge_base
from .llm import DEFAULT_MODEL, PRICING, AnthropicClient, StubClient, estimate_tokens
from .parsers import UnsupportedFormat, parse, parse_pdf_detailed, requirement_tabs
from .report import build_gaps, render_markdown, summarise

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KB = ROOT / "docs" / "knowledge-base"
DEFAULT_RFP = ROOT / "fixtures" / "rfp-alderwood-retail.xlsx"
DEFAULT_GOLD = ROOT / "fixtures" / "gold-answers.json"


def _cmd_parse(args) -> int:
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
                "  warning: low coverage - the numbering scheme may not have been "
                "recognised; consider an LLM extraction pass.",
                file=sys.stderr,
            )

    counts = Counter(r.section for r in requirements)
    titles: dict[str, str] = {}
    for r in requirements:
        titles.setdefault(r.section, r.section_title)
    print("\n  section  count  title")
    for section in sorted(counts, key=lambda s: int(s) if s.isdigit() else 0):
        print(f"  {section:>7}  {counts[section]:>5}  {titles[section]}")

    if args.show:
        print()
        for r in requirements[: args.show]:
            print(f"  [{r.locator}] {r.rid}  {r.text[:96]}")
    return 0


def _cmd_eval_retrieval(args) -> int:
    score = evaluate_retrieval(args.rfp, args.kb, args.gold, top_k=args.top_k)
    print(f"retrieval eval over {score.total} labelled requirements (top_k={args.top_k})")
    print(f"  recall  (an expected document retrieved) : {score.recall:.1%}")
    print(f"  exact   (all expected documents retrieved): {score.exact_rate:.1%}")
    if score.misses and args.show_misses:
        print(f"\n  {len(score.misses)} incomplete:")
        for rid, expected, got in score.misses:
            print(f"    {rid}: expected {expected}")
            print(f"          got      {got}")
    return 0


def _cmd_respond(args) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2

    requirements = parse(path)
    if args.limit:
        requirements = requirements[: args.limit]
    by_id = {r.rid: r for r in requirements}

    from .retrieval import BM25Retriever

    retriever = BM25Retriever(load_knowledge_base(args.kb))
    role = INTERNAL if args.role == "internal" else PUBLIC

    if args.live:
        estimated_in = sum(
            estimate_tokens(r.text) + args.top_k * 220 + 260 for r in requirements
        )
        estimated_out = len(requirements) * 160
        rate_in, rate_out = PRICING.get(args.model, PRICING[DEFAULT_MODEL])
        estimate = (estimated_in / 1e6) * rate_in + (estimated_out / 1e6) * rate_out

        print("LIVE RUN - this will call the Anthropic API and incur charges.")
        print(f"  model            : {args.model}")
        print(f"  requirements     : {len(requirements)}")
        print(f"  estimated tokens : ~{estimated_in:,} in / ~{estimated_out:,} out")
        print(f"  estimated cost   : ~${estimate:.2f}")
        print("  (estimate only; actual usage is reported when the run finishes)")

        if not args.yes:
            try:
                reply = input("\nProceed? [y/N] ").strip().lower()
            except EOFError:
                reply = ""
            if reply not in {"y", "yes"}:
                print("aborted - nothing was sent, nothing was charged.")
                return 1

        try:
            client = AnthropicClient(model=args.model)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        client = StubClient(verdict=args.stub_verdict)

    results, usage = classify_all(
        requirements, retriever, client, role=role, top_k=args.top_k
    )

    counts = summarise(results)
    gaps = build_gaps(by_id, results)
    blocking = [g for g in gaps if g.is_blocking]
    overridden = [r for r in results if r.was_overridden]

    mode = f"live ({args.model})" if args.live else f"offline stub, verdict={args.stub_verdict}"
    print(f"\n{path.name}: {len(results)} requirements  [{mode}]")
    print("  verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"  gaps: {len(gaps)}   blocking (Must + No): {len(blocking)}")
    print(f"  guardrail escalations: {len(overridden)}")
    if overridden:
        for reason, count in Counter(r.override_reason for r in overridden).most_common():
            print(f"    - {reason}: {count}")

    if usage.calls:
        print(
            f"  usage: {usage.calls} calls, {usage.input_tokens:,} in / "
            f"{usage.output_tokens:,} out"
        )
        if args.live:
            print(f"  actual cost: ${usage.cost(args.model):.2f}")

    if args.out:
        out = Path(args.out)
        out.write_text(render_markdown(by_id, results))
        print(f"\nwrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rfp_assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="extract requirements from an RFP document")
    p.add_argument("path")
    p.add_argument("--json", action="store_true")
    p.add_argument("--show", type=int, default=0, metavar="N")
    p.set_defaults(func=_cmd_parse)

    e = sub.add_parser("eval-retrieval", help="score retrieval against the gold key (free)")
    e.add_argument("--rfp", default=str(DEFAULT_RFP))
    e.add_argument("--kb", default=str(DEFAULT_KB))
    e.add_argument("--gold", default=str(DEFAULT_GOLD))
    e.add_argument("--top-k", type=int, default=6)
    e.add_argument("--show-misses", action="store_true")
    e.set_defaults(func=_cmd_eval_retrieval)

    r = sub.add_parser("respond", help="classify requirements and write a gap report")
    r.add_argument("path", nargs="?", default=str(DEFAULT_RFP))
    r.add_argument("--kb", default=str(DEFAULT_KB))
    r.add_argument("--role", choices=["public", "internal"], default="public")
    r.add_argument("--top-k", type=int, default=6)
    r.add_argument("--out", metavar="FILE", help="write a markdown gap report")
    r.add_argument(
        "--live",
        action="store_true",
        help="use the real API (costs money). Without this, runs offline for free.",
    )
    r.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(PRICING))
    r.add_argument("--limit", type=int, metavar="N", help="only process the first N")
    r.add_argument("--yes", action="store_true", help="skip the live-run confirmation")
    r.add_argument("--stub-verdict", default="Yes", help="verdict the offline stub returns")
    r.set_defaults(func=_cmd_respond)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
