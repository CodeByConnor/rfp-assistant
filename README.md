# RFP Requirement Extractor & Gap Mapper

Ingests an enterprise RFP, extracts each requirement as a discrete item,
retrieves supporting product knowledge, classifies every requirement as
**Yes / Partial / No / Roadmap / Needs Input**, drafts a cited answer, and
flags the gaps for human review.

**Core design commitment:** the system never answers a requirement it cannot
cite. If retrieval turns up nothing above a similarity threshold, the verdict
is forced to `Needs Input` rather than letting the model improvise. RFP answers
become contractual commitments — a confidently wrong "Yes" on HIPAA is a
materially worse outcome than an honest "we need to check this."

> **Status: M0.** Test fixtures and knowledge base are built; the pipeline is
> not. See [Milestones](#milestones). Nothing here is a working product yet.

## Demo data is fictional

This isn't built against a real company's documentation. Everything targets a
fictional customer data platform, **Meridian**, evaluated by a fictional
retailer, **Alderwood Retail Group**. All content in `docs/` and `fixtures/`
is invented for this project — no real vendor, buyer, pricing, or security
posture is represented.

## Layout

```
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
| `.pdf` | LLM fallback extraction | requirements in flowing numbered prose, not tables; cover page and TOC whose entries resemble requirements; **188 `must`/`shall` occurrences**, with 4 pages of front matter and appendices that are pure obligation language containing *zero* requirements; repeating header/footer noise on all 19 pages |

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

Python/FastAPI backend, Claude API for extraction and classification,
embeddings + cosine similarity over the knowledge base (no heavyweight vector
DB at this scale), small React review table on top.

## Milestones

- [x] **M0** — Knowledge base, 248-requirement RFP fixtures (md/xlsx/pdf),
      stratified answer key
- [ ] **M1** — Parsing: RFP file → structured `Requirement[]`
- [ ] **M2** — Retrieval + classification + draft answers (CLI)
- [ ] **M3** — Citation enforcement, `Needs Input` guardrail, RBAC filtering
- [ ] **M4** — Review UI: upload, approve/edit, export
- [ ] **M5** — Eval suite, deploy

## Testing

- **Parsers** — each format must yield exactly 248 requirements with matching
  IDs: skipping the xlsx `EXAMPLE` rows, subsection banners, and the 4
  non-requirement tabs, and ignoring the pdf's front matter and appendices.
- **Retrieval** — does each requirement surface its expected citation doc?
- **Classification** — predicted verdict vs. the key's `verdict`; the primary
  quality metric across iterations.
- **Guardrail regression** — `8.3.1` and `8.2.1`–`8.2.3` must always resolve
  to `Needs Input`.
- **RBAC regression** — `8.1.x` and `6.2.2` under a `public` role must never
  retrieve or cite `pricing-packaging.md`.
- **Deduplication** — the 18 near-duplicate clusters should be detected, with
  the `certs` cluster's intentional divergence preserved.
