# Meridian — Implementation & Professional Services

*Doc type: public | Last updated: 2026-04-02*

## Methodology

Meridian implementations run in five phases: Discovery, Data Onboarding,
Identity Configuration, Activation Enablement, and Hypercare.

## Timeline

- Typical time to first production value: **4–8 weeks** for a standard
  deployment; **10–14 weeks** where in-store point-of-sale and loyalty data
  are in scope, because POS batch feeds usually require customer-side
  extract work.
- A deployment spanning web, mobile, POS, and loyalty sources should be
  planned at 12–16 weeks to full production.

## Indicative plan (web + mobile + POS + loyalty)

| Phase | Duration | Key outputs |
|---|---|---|
| Discovery | 2 weeks | Source inventory, identity strategy, success criteria |
| Data Onboarding | 4–6 weeks | Web/mobile SDK live, POS batch feed landing, loyalty load |
| Identity Configuration | 2–3 weeks | Match hierarchy tuned, match rate validated |
| Activation Enablement | 2–3 weeks | Destinations connected, first segments live |
| Hypercare | 4 weeks | Daily monitoring, issue triage, handover |

## Customer resources expected

- Executive sponsor — 2 hours per week
- Marketing/CRM lead — 1 day per week throughout
- Data engineer with POS extract knowledge — 3 days per week during Data
  Onboarding
- Web and mobile developer — 2 days per week during Data Onboarding
- Security/privacy reviewer — as needed during Discovery

## Data migration and validation

- Historical backfill is performed during Data Onboarding, with no volume
  limit. Meridian sizes the load window during Discovery.
- Validation compares source record counts, distinct identifier counts, and
  a sampled field-level reconciliation against the source system. A written
  reconciliation report is produced before sign-off.

## Acceptance

Meridian proposes acceptance on: all in-scope sources ingesting at agreed
volume; match rate meeting the target agreed in Discovery; and at least one
segment activating end to end to a production destination.

## Services and commercials

- **Included in subscription**: Discovery workshop, standard connector
  configuration, and Hypercare for Enterprise customers.
- **Billed separately**: historical backfill beyond 24 months, custom
  connector development, bespoke transformation logic, and any additional
  environment.
- Professional services rates are commercially sensitive — see
  `pricing-packaging.md` (internal only). Do not quote rates in a written
  response without Deal Desk approval.
- **Training**: administrator and business-user training is included, both
  delivered remotely. On-site training is billable.
- **Certification**: Meridian offers no formal certification programme.
- **Partners**: implementation may be delivered by a certified systems
  integrator. Certified North American partners are Beacon Digital, Kestrel
  Consulting, and Northgate Analytics.
