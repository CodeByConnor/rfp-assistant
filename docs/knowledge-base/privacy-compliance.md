# Meridian — Privacy & Regulatory Compliance

*Doc type: public | Last updated: 2026-05-12*

## Regulatory posture

- **CCPA/CPRA**: compliant. Consumer access, deletion, correction, and
  opt-out of sale/share are supported via console and API.
- **GDPR**: compliant. A Data Processing Agreement incorporating the EU
  standard contractual clauses is available to all customers.
- **Washington My Health My Data Act**: Meridian has **not** completed an
  assessment against Washington's consumer health data legislation and does
  not represent compliance with it. Customers subject to that Act should not
  process consumer health data in Meridian. Route any such requirement to
  Legal before responding.
- **HIPAA**: not compliant, no BAA executed, no PHI permitted. Meridian
  provides **no capability to segregate health-adjacent purchase data** from
  general profile data — a data category cannot be given a separate
  encryption boundary, access model, or processing restriction beyond
  standard attribute-level masking.
- **Data Processing Addendum**: Meridian will execute its own standard DPA.
  Customer-paper DPAs are reviewed case by case by Legal; expect exceptions
  on liability and audit-frequency clauses.
- **Model training**: Meridian does **not** use customer data to train
  machine learning models that serve other customers. Predictive traits are
  trained per tenant on that tenant's data only. There is no opt-out to
  configure because there is no cross-tenant training.

## Data subject rights

- **Access requests**: fulfilled via console or the DSR API, returning the
  complete profile and event history in machine-readable JSON.
- **Deletion requests**: initiated via console or API. Deletion propagates
  across live storage immediately and across backups on the backup expiry
  cycle.
- **Maximum elapsed time to irrecoverable deletion: 35 days**, bounded by the
  30-day backup retention cycle.
- **Downstream propagation**: a deletion request emits a suppression and
  delete instruction to every destination the profile was previously
  activated to, where that destination supports one. Destinations without
  deletion APIs are listed in the console so the customer can act manually.
- **Portability**: consumer data is exportable in JSON or CSV.
- Every DSR is recorded in an immutable audit record with requester,
  timestamp, action, and completion time, retained 7 years.
- Deleting a profile that is a member of an active segment removes it from
  the segment and emits a segment-exit event to downstream destinations.

## Data residency and cross-border transfer

- Data may be stored at rest in **US (us-east-1)** or **EU (eu-west-1)**
  only.
- A US-only election is fully supported; no data leaves the elected region at
  rest.
- **Canada**: not a supported storage region. Data for Canadian operations
  would reside in the US region. Meridian makes no representation that this
  satisfies Canadian data residency expectations. Additional regions
  including Canada are under evaluation with **no committed timeline** — see
  `roadmap.md`.
- **Support and engineering access from outside the region**: support
  personnel located in the US and Ireland may access customer data from
  outside the storage region under a customer-approved, time-boxed,
  fully-logged access grant. Customers requiring in-region-only support
  personnel cannot be accommodated today.
- Cross-border transfer relies on the EU standard contractual clauses and the
  UK international data transfer addendum where applicable.
- **Processing outside the elected region**: real-time processing occurs
  wholly within the elected region. Aggregate operational telemetry that
  contains no personal data is processed in the US.
