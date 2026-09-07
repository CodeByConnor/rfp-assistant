# Meridian — Architecture, Scale & Platform Operations

*Doc type: public | Last updated: 2026-05-28*

## Deployment architecture

Multi-tenant SaaS on AWS. Tenants are logically isolated by tenant ID at
every layer, with per-tenant encryption keys. **Single-tenant, dedicated, and
customer-managed (in your own cloud account) deployments are not offered.**

Supported regions: **US (us-east-1)** and **EU (eu-west-1)**, elected at
provisioning and not changeable afterwards without a data migration
engagement.

### Environments

Every Enterprise account includes one non-production sandbox at no additional
charge. Growth accounts may purchase a sandbox. Standard accounts have no
sandbox option. Sandboxes are seeded with synthetic data only.

### Release and change management

- Continuous delivery to production, typically 8–14 releases per week.
- Customers cannot defer a release. Meridian operates a single production
  version.
- **Breaking API changes carry a 12-month deprecation window** with written
  notice at announcement, 6 months, and 30 days.
- No third-party subprocessor sits in the request path for real-time profile
  reads or segment evaluation.

### Redundancy and failover

Multi-AZ within the elected region, with automatic failover between
availability zones. **Cross-region failover is manual and vendor-initiated,
and is not covered by the published RTO.**

## Scale and performance

- Largest production deployment: 41 million tracked profiles, 3.2 billion
  events per month.
- A 2.1 million profile deployment with 20 percent annual growth is well
  within normal operating range.
- Sustained ingestion 50,000 events/sec per account; burst 150,000 for up to
  15 minutes. Beyond burst capacity, events are queued and processed with
  delay rather than rejected; queue depth is visible in the console.
- Retail peak events are routine. Meridian pre-scales capacity for known peak
  windows on request with 10 business days' notice, at no charge. A fivefold
  traffic increase is within standard headroom.
- **API rate limits**: 1,000 requests/sec per account on the profile API,
  100 requests/sec on the segment management API. Limits are raisable
  contractually on Enterprise.
- Profile lookup latency: p50 42 ms, p99 180 ms.
- Query performance is largely independent of profile count; segment
  evaluation cost scales with event volume in the evaluation window rather
  than total history.
- **There are no batch processing windows during which functionality is
  reduced.** All maintenance is online.
- Capacity planning review is offered ahead of a known peak for Enterprise
  customers as part of the TAM engagement.

## APIs, SDKs, and extensibility

- **REST APIs**: profile read/write, event ingestion, segment management,
  audit log export, consent read/write, and data export.
- API documentation is **publicly accessible without a login** at
  docs.meridiandata.example.
- **SDKs**: JavaScript (browser), Node, Python, Java, Go, iOS (Swift), and
  Android (Kotlin). All are vendor-maintained.
- **Webhooks**: at-least-once delivery, HMAC-SHA256 signature verification,
  exponential-backoff retry over 24 hours, dead-letter visibility in console.
- **Kafka**: a managed connector for streaming raw event data into a customer
  Kafka topic is **not available today**. See `roadmap.md` — targeted for
  design in Q3 2026, no committed ship date.
- Customer-authored transformation logic runs in a sandboxed JavaScript
  runtime executed on ingestion, limited to 50 ms per event.
- Connector maintenance: all connectors listed in `integrations-catalog.md`
  are vendor-maintained unless explicitly marked partner-maintained.
- A connector not in the catalogue can be built by Professional Services
  under a statement of work; typical delivery is 6–10 weeks.
- **API versioning**: versions are dated (e.g. `2026-01-15`). A version
  remains supported for 24 months from the release of its successor.

## Data management

- Event schema is customer-defined. Meridian does not impose a fixed event
  taxonomy.
- Up to 200 custom attributes per profile.
- **Full data export at any time, in CSV or Parquet, with no export fee**,
  initiated from the console or the export API.
- On termination, data remains retrievable for 30 days, then is
  irrecoverably destroyed within 60 days. A certificate of destruction is
  provided on request.
- **Data lineage**: every profile attribute records the source system, source
  record identifier, and ingestion timestamp that last wrote it, queryable
  via the profile API.
- Data quality monitoring detects schema drift, null-rate change, and volume
  anomaly, with alerting.
- Historical backfill is supported at initial load with no volume limit;
  Professional Services sizes the load window during implementation.
- Deduplication on client-supplied idempotency key within a 24-hour window.

## Monitoring and observability

- Operational dashboards in the console covering ingestion volume, pipeline
  lag, activation delivery, and error rate.
- Alerting on ingestion failure and pipeline delay via email, Slack, PagerDuty,
  or webhook.
- **Public status page** at status.meridiandata.example, publishing current
  status and 12 months of historical uptime.
- Planned maintenance is announced at least 5 business days in advance; all
  maintenance is online with no functional reduction.
- **Platform logs can be forwarded to a customer-operated SIEM** via the
  audit log export API or an S3 delivery stream.
- Operational and diagnostic log retention: 12 months.
- **Record-level tracing**: an individual event can be traced through
  ingestion, identity resolution, and activation using its event ID, in the
  console troubleshooting view.
