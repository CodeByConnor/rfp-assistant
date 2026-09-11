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
from .llm import DEFAULT_MODEL, PRICING, AnthropicClient, StubClient
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


def _confirm_live(count: int, model: str, *, assume_yes: bool) -> bool:
    """Show what a live run will cost, then require an explicit yes."""
    from .llm import estimate_run_cost

    print("LIVE RUN - this will call the Anthropic API and incur charges.")
    print(f"  model            : {model}")
    print(f"  requirements     : {count}")
    print(f"  estimated cost   : ~${estimate_run_cost(count, model):.2f}")
    print("  (estimate only; actual usage is reported when the run finishes)")
    if assume_yes:
        return True
    try:
        reply = input("\nProceed? [y/N] ").strip().lower()
    except EOFError:
        reply = ""
    if reply in {"y", "yes"}:
        return True
    print("aborted - nothing was sent, nothing was charged.")
    return False


def _live_client(model: str):
    try:
        return AnthropicClient(model=model)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return None


def _cmd_eval_classify(args) -> int:
    from .evaluate import evaluate_classification, load_gold
    from .llm import ReplayClient

    entries = load_gold(args.gold)
    if args.limit:
        entries = entries[: args.limit]

    if args.live:
        if not _confirm_live(len(entries), args.model, assume_yes=args.yes):
            return 1
        client = _live_client(args.model)
        if client is None:
            return 2
        mode = f"live ({args.model})"
    elif args.offline == "replay":
        client = ReplayClient(args.gold)
        mode = "offline replay"
    else:
        client = StubClient(verdict=args.stub_verdict)
        mode = f"offline stub, verdict={args.stub_verdict}"

    score = evaluate_classification(
        args.rfp, args.kb, args.gold, client, top_k=args.top_k, limit=args.limit
    )

    print(f"classification eval over {score.total} labelled items  [{mode}]")
    print(f"  accuracy                  : {score.accuracy:.1%}  ({score.correct}/{score.total})")
    print(
        f"  overstatements            : {len(score.overstatements)}"
        f"  ({score.overstatement_rate:.1%}) - predicted more favourable than the label"
    )
    print(f"  unanswerable held         : {score.guardrail_correct}/{score.guardrail_total}")
    print(f"  internal citations leaked : {len(score.leaks)}")
    if not args.live and args.offline == "replay":
        print()
        print("  note: replay returns the labelled verdicts, so this measures what the")
        print("        guardrail changes, not how well a model classifies. Use --live")
        print("        for that.")

    print("\n  expected     | predicted")
    for expected in ["Yes", "Partial", "Roadmap", "No", "Needs Input"]:
        row = score.confusion.get(expected)
        if not row:
            continue
        cells = ", ".join(f"{k} {n}" for k, n in sorted(row.items(), key=lambda kv: -kv[1]))
        print(f"  {expected:<12} | {cells}")

    if score.wrong and args.show_wrong:
        print(f"\n  mismatches ({len(score.wrong)}):")
        for rid, role, expected, predicted in score.wrong[: args.show_wrong]:
            print(f"    {rid:<8} [{role:<13}] expected {expected:<11} got {predicted}")
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
        if not _confirm_live(len(requirements), args.model, assume_yes=args.yes):
            return 1
        client = _live_client(args.model)
        if client is None:
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

    ec = sub.add_parser("eval-classify", help="score verdicts against the gold key")
    ec.add_argument("--rfp", default=str(DEFAULT_RFP))
    ec.add_argument("--kb", default=str(DEFAULT_KB))
    ec.add_argument("--gold", default=str(DEFAULT_GOLD))
    ec.add_argument("--top-k", type=int, default=6)
    ec.add_argument("--offline", choices=["replay", "stub"], default="replay")
    ec.add_argument("--stub-verdict", default="Yes")
    ec.add_argument(
        "--live",
        action="store_true",
        help="score a real model (costs money). Without this, runs offline for free.",
    )
    ec.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(PRICING))
    ec.add_argument("--limit", type=int, metavar="N")
    ec.add_argument("--yes", action="store_true", help="skip the live-run confirmation")
    ec.add_argument("--show-wrong", type=int, default=10, metavar="N")
    ec.set_defaults(func=_cmd_eval_classify)

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

    s = sub.add_parser("serve", help="run the local review app")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--store", default=str(ROOT / "runs"), help="where review runs are kept")
    s.add_argument("--kb", default=str(DEFAULT_KB))
    s.add_argument("--gold", default=str(DEFAULT_GOLD))
    s.add_argument("--role", choices=["public", "internal"], default="public")
    s.add_argument(
        "--offline",
        choices=["replay", "stub"],
        default="replay",
        help="offline client: replay the hand-labelled key (demo), or placeholder verdicts",
    )
    s.add_argument(
        "--live",
        action="store_true",
        help="uploads call the real API (costs money). Asks before starting.",
    )
    s.add_argument("--model", default=DEFAULT_MODEL, choices=sorted(PRICING))
    s.add_argument("--limit", type=int, metavar="N", help="cap requirements per upload (live default: 25)")
    s.add_argument("--yes", action="store_true", help="skip the live-server confirmation")
    s.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


def _cmd_serve(args) -> int:
    try:
        import uvicorn

        from .web.app import create_app
    except ImportError:
        print(
            "error: the review app needs extra packages: "
            "pip install fastapi uvicorn python-multipart",
            file=sys.stderr,
        )
        return 2
    from .llm import ReplayClient, estimate_run_cost

    role = INTERNAL if args.role == "internal" else PUBLIC

    if args.live:
        limit = args.limit or 25
        print("LIVE SERVER - every upload will call the Anthropic API and incur charges.")
        print(f"  model                : {args.model}")
        print(f"  cap per upload       : {limit} requirements")
        print(f"  estimated per upload : up to ~${estimate_run_cost(limit, args.model):.2f}")
        if not args.yes:
            try:
                reply = input("\nStart the live server? [y/N] ").strip().lower()
            except EOFError:
                reply = ""
            if reply not in {"y", "yes"}:
                print("aborted - server not started, nothing was charged.")
                return 1
        try:
            AnthropicClient(model=args.model)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        model = args.model
        factory = lambda: AnthropicClient(model=model)  # noqa: E731
        mode = f"live:{model}"
    else:
        limit = args.limit
        model = None
        if args.offline == "replay":
            gold = args.gold
            factory = lambda: ReplayClient(gold)  # noqa: E731
            mode = "replay"
        else:
            factory = StubClient
            mode = "stub"

    app = create_app(
        store_dir=args.store,
        kb_dir=args.kb,
        client_factory=factory,
        mode=mode,
        model=model,
        live=args.live,
        limit=limit,
        role=role,
        sample_path=DEFAULT_RFP,
    )
    print(f"RFP Assistant review app: http://{args.host}:{args.port}  [{mode}]")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
