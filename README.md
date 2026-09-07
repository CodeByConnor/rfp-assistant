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
docs/knowledge-base/     Meridian's product docs, security whitepaper,
                         integrations, SLA, roadmap, past RFP answers.
                         pricing-packaging.md is tagged internal-only to
                         exercise RBAC-filtered retrieval.
fixtures/                The Alderwood RFP in three formats + answer key.
```

## Fixtures

The same 33 requirements in three formats with identical IDs, so one answer key
(`fixtures/gold-answers.json`) covers all three. Each format exercises a
different parse path and carries deliberate hazards:

| Format | Path under test | Hazards |
|---|---|---|
| `.md` | control | none — the baseline |
| `.xlsx` | structured table parse | `Instructions` sheet ahead of the data sheet; 6-row metadata block above the header row; merged section banners interleaved with requirement rows; a worked `EXAMPLE` row that must **not** parse as a requirement |
| `.pdf` | LLM fallback extraction | requirements in flowing numbered prose, not tables; cover page; repeating header/footer noise on all 5 pages; 11 `must`/`shall` sentences in background and appendix prose that are **not** requirements |

The PDF distractors are the point: a regex extractor will pull *"Proposals
shall be submitted in electronic form only"* out of the background section and
file it as requirement 34. Correct output is 33, exactly.

`gold-answers.json` labels the expected verdict and citations per requirement,
including the cases that matter most:

- **`G1`** — nothing in the knowledge base addresses sustainability. Must
  return `Needs Input`. This is the hallucination guardrail regression test.
- **`H1`/`H2`** — answerable only from the internal-only pricing doc. Labeled
  twice, for `public` and `internal` roles: a public-role query must never
  retrieve or cite pricing.
- **`A3` vs `D4`** — single-tenant is "customers asked, not committed" →
  `No`; the Kafka connector has a targeted quarter → `Roadmap`. Tests whether
  the classifier separates real roadmap commitments from wishful mentions,
  which is exactly where naive RAG produces an answer that gets an SE in
  trouble.

Regenerate the binary fixtures after editing a builder:

```bash
.venv/bin/python fixtures/build_xlsx_fixture.py
.venv/bin/python fixtures/build_pdf_fixture.py
```

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

- [x] **M0** — Knowledge base, RFP fixtures (md/xlsx/pdf), gold answer key
- [ ] **M1** — Parsing: RFP file → structured `Requirement[]`
- [ ] **M2** — Retrieval + classification + draft answers (CLI)
- [ ] **M3** — Citation enforcement, `Needs Input` guardrail, RBAC filtering
- [ ] **M4** — Review UI: upload, approve/edit, export
- [ ] **M5** — Eval suite, deploy

## Testing

- **Parsers** — each format must yield exactly 33 requirements with matching
  IDs, skipping the xlsx `EXAMPLE` row and banners, and ignoring pdf
  `must`/`shall` prose.
- **Retrieval** — does each requirement surface its expected citation doc?
- **Classification** — verdict vs. `expected_verdict`; the primary quality
  metric across iterations.
- **Guardrail regression** — `G1` must always resolve to `Needs Input`.
- **RBAC regression** — `H1`/`H2` under a `public` role must never cite
  `pricing-packaging.md`.
