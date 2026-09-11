# RFP Requirement Extractor & Gap Mapper

Ingests an enterprise RFP, extracts each requirement as a discrete item,
retrieves supporting product knowledge, classifies every requirement as
**Yes / Partial / No / Roadmap / Needs Input**, drafts a cited answer, and
flags the gaps for human review.

**Core design commitment:** the system never answers a requirement it cannot
cite. Every verdict must name a source document and quote it verbatim, and the
quote is verified against that document before the answer is kept. RFP answers
become contractual commitments — a confidently wrong "Yes" on HIPAA is a
materially worse outcome than an honest "we need to check this."

> **Status: M4.** Parsing, retrieval, classification, the guardrail, the gap
> report, and the review app all work and are tested end to end offline. No
> live model run has been made yet. See [Milestones](#milestones).

## Running it costs nothing by default

`respond` uses an offline stub client unless you pass `--live`, so the whole
pipeline — retrieval, prompting, citation verification, the guardrail, the gap
report — runs and is tested without an API key and without spending anything.
`--live` prints a cost estimate and requires confirmation before the first
call, and `--limit N` caps the run. Both safeguards are covered by tests.

```bash
python -m rfp_assistant respond                      # offline, free
python -m rfp_assistant eval-retrieval               # offline, free
python -m rfp_assistant respond --live --limit 20 --model claude-haiku-4-5
```

A full 248-requirement live run is roughly **$2.60 on Opus 5, $1.05 on Sonnet
5, or $0.52 on Haiku 4.5** — measured from real token counts in an offline
run, not guessed.

## The review app

```bash
python -m rfp_assistant serve          # http://127.0.0.1:8765, offline demo
```

Upload an RFP (or load the sample), work through the answers, and download
**the buyer's own workbook with approved answers written into it** — the
filled-in spreadsheet is the actual deliverable, so the export writes into
the original rather than producing a new file. The buyer's scoring formulas,
dropdowns, and formatting survive the round trip.

The approval rules are where the guardrail meets the human:

- A row with no compliance level cannot be approved. Only unambiguous verdicts
  pre-fill one (`Yes` → Standard, `No` → Not Supported, `Roadmap` → Roadmap).
  `Partial` could be Configuration, Customization, or Third-Party, and the
  buyer scores those differently, so a person picks.
- A `Needs Input` row cannot be approved with the guardrail's placeholder
  text. Someone has to write the answer.
- Editing an approved answer sends it back to pending.
- Only approved rows reach the export. Citations to internal documents are
  never written, and a run made with internal documents visible cannot be
  exported at all.

By default the app runs in **demo mode**: verdicts are replayed from the
hand-labelled answer key rather than produced by a model, and a banner on
every page says so. The guardrail still runs over every replayed response, so
the demo shows real holds. `serve --live` switches to the real model after a
terminal confirmation with a per-upload cost estimate and cap; nothing in the
browser can switch modes.

## Demo data is fictional

This isn't built against a real company's documentation. Everything targets a
fictional customer data platform, **Meridian**, evaluated by a fictional
retailer, **Alderwood Retail Group**. All content in `docs/` and `fixtures/`
is invented for this project — no real vendor, buyer, pricing, or security
posture is represented.

## Usage

```bash
python -m rfp_assistant parse fixtures/rfp-alderwood-retail.xlsx
python -m rfp_assistant parse fixtures/rfp-alderwood-retail.pdf --show 5
python -m rfp_assistant parse <file> --json > requirements.json
pytest                      # 117 tests, all offline (1 known-gap xfail)
```

## Layout

```
rfp_assistant/
  models.py              Requirement: id, text, section, priority, locator.
  parsers/               One parser per format, dispatched on extension.
  knowledge.py           Chunking + access tagging of the knowledge base.
  retrieval.py           BM25, with access filtering applied before scoring.
  llm.py                 Client boundary. StubClient is free and offline;
                         AnthropicClient is the only thing that can spend.
  classify.py            Prompting, citation verification, the guardrail.
  report.py              Gap report, risk-ranked.
  evaluate.py            Retrieval scoring against the gold key (free).
  review.py              Review runs: approval rules, storage.
  export.py              Write approved answers into the buyer's workbook.
  workbook.py            Vendor-column discovery shared by review and export.
  web/                   FastAPI app + a single-page review UI, no build step.
tests/                   117 tests, all offline.
docs/knowledge-base/     11 Meridian documents: product, architecture,
                         security, privacy, integrations, SLA/support,
                         implementation, company profile, roadmap, past
                         answers. pricing-packaging.md is tagged
                         internal-only to exercise RBAC-filtered retrieval.
                         No contractual-terms doc exists, deliberately —
                         that absence is what makes 8.2.x a guardrail test.
fixtures/
  requirements_data.py   Source of truth: 248 requirements, 8 sections.
  build_*_fixture.py     Generators for the md / xlsx / pdf forms.
  gold-answers.json      Stratified answer key (126 labeled).
```

## Fixtures

**248 requirements** across 8 sections, hierarchically numbered (`4.2.3`), at
the scale a real enterprise CDP RFP actually runs. All three formats generate
from one source of truth — `fixtures/requirements_data.py` — so they cannot
drift apart, and one answer key covers all three.

```bash
.venv/bin/python fixtures/build_md_fixture.py     # control format
.venv/bin/python fixtures/build_xlsx_fixture.py   # 12-tab response workbook
.venv/bin/python fixtures/build_pdf_fixture.py    # 19-page prose RFP
```

| Format | Path under test | Hazards |
|---|---|---|
| `.md` | control | none — the baseline. A parser that can't get 248/248 here has a bug unrelated to document format |
| `.xlsx` | structured table parse | **12 tabs, only 8 holding requirements** — Instructions, Pricing Workbook, Scoring Summary and Exceptions Log must not be parsed as requirement tables; metadata block above the header row on every tab; merged subsection banners interleaved with requirement rows; a worked `EXAMPLE` row per tab; buyer-owned columns (Priority, Weight, Score) interleaved with vendor-owned ones; a locked dropdown on the compliance column |
| `.pdf` | prose extraction | requirements in flowing numbered prose, not tables; cover page and TOC whose entries resemble requirements; **188 `must`/`shall` occurrences**, with 4 pages of front matter and appendices that are pure obligation language containing *zero* requirements; repeating header/footer noise on all 19 pages |

The PDF front matter is the real trap. Submission instructions, terms and
conditions, and the attestation page are written in dense obligation language —
*"Responses must be submitted as a single PDF"*, *"The vendor shall maintain
commercial general liability insurance"* — and contain no requirements at all.
A keyword extractor files them as requirements 249 through 280.

### Near-duplicate requirements

18 clusters of semantically-equivalent requirements asked in different
sections with different wording, because committee-written RFPs do exactly
this. SSO is asked in both Technical and Security; data residency in both
Technical and Privacy; retention in both Functional and Privacy. Deduplication
is a real feature with a real test set here, not a hypothetical.

One cluster diverges on purpose: `4.1.1` asks for *all* certifications
(`Partial` — SOC 2 yes, ISO 27001 not yet) while `4.1.2` asks only about SOC 2
(`Yes`). Clustering should catch them; forcing them to share an answer is
wrong.

### The answer key

`fixtures/gold-answers.json` labels **126 of the 248** requirements — a
stratified subset covering every verdict class, both RBAC roles, and each
deliberate gap. Labeling all 248 would mean generating most labels
mechanically, which is worse than labeling fewer honestly.

The cases that carry the design:

- **`8.3.1` sustainability, `8.2.1`–`8.2.3` contractual terms** — the
  knowledge base has nothing, and says so. Must return `Needs Input`. `8.2.3`
  is the sharpest: nearby docs state a cyber liability *insurance* limit,
  which is not a contractual *limitation of liability*. Answering from it is a
  hallucination that reads as correct.
- **`5.1.3` Washington health data** — the KB explicitly records that no
  assessment was done. The failure mode is inferring compliance from the CCPA
  and GDPR answers sitting beside it in the same document.
- **`8.1.x`, `6.2.2` pricing and rates** — answerable only from the
  internal-only doc, labeled for both `public` and `internal` roles. A public
  query must never retrieve or cite pricing.
- **`3.1.2` vs `3.3.7`** — single-tenant is "requested but not planned" →
  `No`; the Kafka connector has a targeted quarter → `Roadmap`. Both mention
  the roadmap. Getting these two different is the whole point: promising an
  uncommitted capability in an RFP response is how an SE creates a
  contractual problem.
- **`5.1.4` HIPAA** — a flat `No` on a Must requirement, against a buyer with
  pharmacy PII. The gap report should surface this as deal-threatening rather
  than burying it among 247 others.

## Parsers

All three parsers are **structural** — no LLM call. Requirements are found by
position and identifier shape, not by vocabulary, because vocabulary is
exactly what the boilerplate shares with the requirements.

- **xlsx** — finds requirement tables by looking for a header row pairing an
  id-like column with a requirement-like column, rather than hardcoding tab
  names. That correctly rejects the pricing, scoring, instructions and
  exceptions tabs, and generalises to workbooks that name their tabs
  differently.
- **pdf** — drops page furniture, then treats a hierarchical identifier at the
  start of a line as a requirement opener and stitches wrapped continuation
  lines back on.
- Section membership is derived from the requirement id, not the display
  heading. The PDF numbers its requirement sections 7–14 because front matter
  occupies 1–6, while the ids inside them still begin `1.x`. The id is the
  thing that is stable across formats.

**Limitation, stated plainly:** the fixture numbers every requirement `N.N.N`,
and the PDF parser keys on that. A real RFP may use `REQ-4.2.3`, `4.2.3)`, or
prose with no identifiers at all, and this parser will find nothing in those.
That is why `parse_pdf_detailed` reports body-line coverage: a collapse toward
zero is the signal to escalate to an LLM extraction pass rather than silently
return a short list. The LLM fallback is not built yet.

### Bugs this suite caught

The fixture hazards earned their keep — each of these produced a plausible
looking result rather than an error:

- The table of contents contains *"Appendix A. Terms and Conditions"*. Treating
  it as the appendix heading put the parser into a mode that discarded every
  continuation line, truncating 106 requirements to their first sentence while
  still reporting a confident 248 found.
- The page footer extracts as one merged line (`Customer Data Platform -
  Issued 1 July 2026 Page 7`), so a pattern anchored on the date missed it and
  the footer was appended to whichever requirement ended the page.
- Detecting page furniture by repetition alone ate the `[Must]` priority tags
  that wrap onto a line of their own: they recur on nearly every page, exactly
  like a footer. Furniture now has to sit at a page edge as well as repeat.

## What the measurements changed

Two design decisions were reversed by evidence before any money was spent.
Both measurements run offline, against the gold key, in under a second.

### The similarity threshold does not work

The original design — stated in this README until it was tested — was: if
retrieval returns nothing above a similarity threshold, force `Needs Input`.

Measured against the gold key, the score distributions overlap almost
entirely:

| | min | median | max |
|---|---|---|---|
| Answerable (n=113) | 4.50 | 15.09 | 40.48 |
| `Needs Input` (n=11) | 5.13 | 10.47 | 32.54 |

The highest-scoring unanswerable requirement (`8.3.1`, sustainability) outranks
75% of the answerable ones. The lowest-scoring answerable one (`4.2.1`, SAML)
falls below *every* unanswerable one. No threshold separates them.

The reason is conceptual, and it generalises well beyond this project:
**relevance and answerability are different properties.** Retrieval correctly
surfaces the sustainability chunk — it is genuinely the most relevant passage
in the corpus. It just says the company has no position on the topic. A
similarity score cannot distinguish "here is your answer" from "here is the
document confirming no answer exists."

Scanning all retrieved chunks for escalation language fails too, for a related
reason: at six chunks per query it fired on **42 of 113** answerable
requirements, because a marker in chunk five says nothing about whether chunk
one answers the question.

So the guardrail runs *after* the model commits to its evidence:

1. The model names one document and quotes it verbatim.
2. The quote is verified to appear in that document. A quote that does not is
   fabricated evidence, and the verdict is discarded.
3. Escalation language is checked in two passages: the one holding the
   model's quote, and the one across all supplied evidence that best matches
   the requirement. If either says "route to Legal", the answer becomes
   `Needs Input` however confident the verdict. Why two is below.

Only the degenerate case — retrieval returned nothing at all — is handled
before the call, because there is nothing to send. That path is tested to make
no model call at all.

### Escalating on the whole cited chunk over-fired

The first version scanned the entire cited chunk for escalation language. The
review app's demo mode exposed the problem at once: clean answers were being
held. Two causes, both measured:

- **A loose marker.** A bare `route to` matched *"no direct public route to the
  data tier"* in the security whitepaper and held every network-security answer.
- **Chunk granularity.** CCPA, GDPR, and model-training answers share a section
  with the Washington health-data bullet that says "route to Legal". One bullet
  held the whole section.

Checking only the passage holding the model's quote fixes that, but it can be
evaded: a model could quote a harmless neighbouring sentence and step around
the escalation beside it. So the second check keys on the passage that best
matches the *requirement*, which depends on nothing the model chose.

Measured on the gold key's 124 public-role items with two clients: a replay of
the labelled verdicts (realistic citations), and an adversarial stub that
answers "Yes" to everything and cites its first evidence block.

| Rule | Replay: `Needs Input` caught | Replay: false holds | Adversarial: caught | Adversarial: false holds |
|---|---|---|---|---|
| Whole cited chunk (original) | 11/11 | 6 | 7/11 | 6 |
| Whole cited chunk, marker fixed | 11/11 | 6 | 8/11 | 6 |
| Quote's passage only | 11/11 | 0 | 6/11 | 0 |
| **Quote's passage + best-matching passage** | **11/11** | **1** | **8/11** | **1** |

The chosen rule keeps every catch of the whole-chunk rule at one-sixth the
false holds. It catches two more than quote-only checking, including `5.1.3`,
where the stub quoted a harmless sentence right beside the Washington
escalation — the evasion case. It costs one false hold (`5.1.1`, a lexical tie
between the CCPA and Washington bullets), which costs a reviewer a click.
Getting there needed one more fix: splitting passages on blank lines separated
a question in the answer library from the "route to Legal" answer beneath it,
so passages now split only at bullets and table rows.

**The gap this cannot close.** All three adversarial misses are public-role
pricing questions (`8.1.1`, `8.1.2`, `8.1.4`). No public document mentions
pricing, so there is no escalation language anywhere to trigger on, and a
model that answers "Yes" while quoting a real but irrelevant sentence passes
every lexical check. That case rests on the model's own judgment, which is
what the one live eval run exists to measure. It is pinned in the suite as a
strict `xfail`: the day it starts passing, the test fails and forces an update
here.

### Embeddings were not needed

BM25 over 66 chunks, measured against the gold key's expected citations:

| top_k | recall | all expected docs |
|---|---|---|
| 3 | 97.5% | 93.3% |
| 4 | 97.5% | 95.8% |
| **6 (default)** | **98.3%** | **97.5%** |
| 8 | 100% | 100% |

At 98.3% recall with zero dependencies, no model download, and millisecond
queries, an embedding model would add hundreds of megabytes to buy at most 1.7
points — and those points may be noise, since the key has only 120
retrieval-scored items and tuning `top_k` to hit exactly 100% on it would be
fitting to my own labels. Lexical matching works here because requirements and
documentation share vocabulary almost verbatim: "SAML", "HIPAA", "Kafka",
"RPO" appear on both sides.

The remaining misses are interesting rather than broken. `6.2.4` asks about
staff *certification programmes* and retrieves the *security certifications*
section — a real lexical ambiguity that embeddings might actually fix. That is
the measurement that would justify adding them; 1.7 points of recall is not.

### RBAC is structural, not a ranking preference

Access filtering happens *before* scoring, so an internal-only chunk is never
a candidate rather than merely ranked low. Verified across all 248
requirements at `top_k=8`: **zero** public-role queries surface the internal
pricing document, while the internal role reaches it for every pricing
requirement.

Untagged documents default to internal. Wrongly withholding a document costs a
human review; wrongly exposing one puts confidential material in a customer's
hands.

One test caught a subtlety worth keeping: the *public* implementation doc
legitimately mentions `pricing-packaging.md` by name ("rates are commercially
sensitive — see pricing-packaging.md"). That is a pointer, not a leak, and it
doubles as an escalation signal. The test asserts on the sensitive figures and
on chunk provenance, not on the filename string.

## Planned architecture

```
RFP (pdf/xlsx/md) → parser → Requirement[]
                                 ↓
                   retrieval (embed + search, filtered by requester role)
                                 ↓
                   classify + draft (structured output; forced "Needs Input"
                   below similarity threshold)
                                 ↓
                   review UI (approve/edit) → export + gap report
```

Python, Claude API for classification, BM25 over the knowledge base. No
embedding model, no vector DB — see below for why that was a measurement
rather than a preference.

## Milestones

- [x] **M0** — Knowledge base, 248-requirement RFP fixtures (md/xlsx/pdf),
      stratified answer key
- [x] **M1** — Parsing: RFP file → structured `Requirement[]`, all three
      formats at 248/248 with exact text match
- [x] **M2** — BM25 retrieval + classification + draft answers (CLI)
- [x] **M3** — Citation enforcement, `Needs Input` guardrail, RBAC filtering,
      gap report
- [x] **M4** — Review app: upload, approve/edit, export into the buyer's
      own workbook
- [ ] **M5** — Live classification eval against the gold key, deploy

## Testing

- **Parsers** — each format must yield exactly 248 requirements with matching
  IDs: skipping the xlsx `EXAMPLE` rows, subsection banners, and the 4
  non-requirement tabs, and ignoring the pdf's front matter and appendices.
- **Retrieval** — does each requirement surface its expected citation doc?
- **Classification** — predicted verdict vs. the key's `verdict`; the primary
  quality metric across iterations.
- **Guardrail** — a stub that fabricates its supporting quote must be caught
  every time; a stub that confidently answers `Yes` to `8.3.1` and `5.1.3`
  must be overridden to `Needs Input` by the escalation check on its own cited
  evidence; a requirement with no retrievable evidence must produce no model
  call at all.
- **RBAC** — no internal-sourced chunk may reach a public-role prompt, checked
  across all 248 requirements rather than the labelled subset.
- **Spending safety** — `respond` must not construct the live client without
  `--live`, and a `--live` run must show its cost estimate before prompting
  and abort on anything but an explicit yes.
- **Review and export** — approval requires a compliance level on scored rows
  and a written answer on `Needs Input` rows; only approved rows are exported;
  the buyer's formulas and dropdowns survive; internal citations are withheld
  and internal-role runs refuse to export; run ids and upload filenames can
  never reach the filesystem.
- **Deduplication** — the 18 near-duplicate clusters should be detected, with
  the `certs` cluster's intentional divergence preserved.
