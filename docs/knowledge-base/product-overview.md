# Meridian — Product Overview

*Doc type: public | Last updated: 2026-06-01*

Meridian is a customer data platform for mid-market retail, e-commerce, and
subscription businesses. It unifies customer data from web, mobile,
point-of-sale, and third-party sources into a single profile, enabling
real-time segmentation and activation.

## Data ingestion

- **Web**: JavaScript tag and browser SDK for event collection.
- **Mobile**: native iOS and Android SDKs, vendor-maintained.
- **Server-side**: HTTP event ingestion API for systems that cannot run a
  client SDK.
- **Batch**: SFTP drop, Amazon S3, Google Cloud Storage, and Azure Blob.
  Accepted formats are CSV, TSV, JSON Lines, and Parquet. Maximum single file
  size is 5 GB; larger loads must be split.
- **Warehouse**: bidirectional Snowflake, BigQuery, and Redshift connectors.
- **Late and out-of-order events** are accepted within a 72-hour window and
  trigger recomputation of affected segment membership. Events older than 72
  hours are ingested for profile history but do not retroactively alter
  segment membership.
- **Schema validation** runs on ingestion. Records failing validation are
  routed to a dead-letter queue visible in the admin console and retained 14
  days for inspection and replay.
- **Throughput**: 50,000 events per second sustained per account, burst to
  150,000 for up to 15 minutes.
- **Deduplication**: events carrying a client-supplied idempotency key are
  deduplicated within a 24-hour window.

## Identity resolution

- Deterministic and probabilistic matching, both available. Deterministic
  matching is applied by default; probabilistic matching is opt-in per
  account.
- Supported identifiers: email, phone, loyalty number, customer ID, device
  identifier, cookie ID, and SHA-256 hashed email or phone.
- **Customer-defined match rule hierarchy**: administrators define
  identifier precedence rather than accepting a fixed vendor order.
- Anonymous-to-known stitching: an anonymous session's event history is
  merged into the known profile on authentication.
- Typical deterministic match rate for retailers at an 8:1 anonymous-to-known
  ratio is 62–71 percent, measured as the share of anonymous sessions
  subsequently resolved to a known profile within 30 days.
- **Household grouping** by normalised postal address is supported as a
  secondary grouping above individual identity.
- Identity merges are recorded in the audit log and are individually
  reversible for 90 days.
- Shared identifiers (for example one loyalty number used by several
  household members) can be flagged as non-unique in the match hierarchy so
  they group at household level rather than collapsing distinct individuals.
- Identity resolution runs in real time on event arrival, with a nightly
  batch reconciliation pass.
- Limits: 500 identifiers per profile.

## Customer profiles

- Unified profile combining behavioural events, transactions, and attributes.
- **Up to 200 custom attributes per profile.**
- Computed attributes recalculate in real time on qualifying events.
- Single-customer view in the console with attribute panel and chronological
  event timeline.
- Profile API: read by any supported identifier, p50 42 ms, p99 180 ms.
- Business users can correct profile attributes directly in the console
  where granted the Data Steward role.
- **Retention**: default 25 months, configurable from 3 to 84 months, and
  configurable per data category.
- Profiles with no activity for the configured retention period are purged,
  not archived.
- Schema additions do not require reprocessing history; attribute removals do.
- **Consent is a first-class profile object**, not a custom attribute.

## Segmentation

- Visual segment builder for non-technical users, plus SQL segments for
  analysts.
- Real-time segment evaluation; median latency from qualifying event to
  segment membership is under 2 seconds.
- Behavioural segmentation on event sequence, frequency, and recency.
- Predictive traits (churn likelihood, predicted lifetime value) available on
  Growth and Enterprise tiers.
- Nested and composite segments referencing other segments are supported.
- Segment size estimation is exact, computed against current membership.
- Segment definitions are versioned with author and timestamp; prior versions
  are restorable.
- Limits: 500 active segments per account on Enterprise, 150 on Growth.
- **Global suppression lists** apply across all activations.
- Both segment entry and exit events are emitted to downstream destinations.
- Holdout groups can be defined as a random percentage of a segment for
  measurement.

## Activation

- Native activation to Salesforce Marketing Cloud, Klaviyo, Braze, Twilio,
  Meta Ads, and Google Ads.
- Reverse ETL of computed traits and segments into Snowflake, BigQuery, and
  Redshift.
- Outbound webhooks on segment entry and exit, with HMAC signature
  verification, at-least-once delivery, and exponential-backoff retry for 24
  hours.
- Meridian provides audience activation, not multi-step journey
  orchestration. Journey building is expected to occur in the connected
  execution tool.
- Destination rate limits are respected automatically with backoff; sustained
  rejection raises an alert.
- Failed activations are visible in the console with per-record error detail
  and can be retried by a business user without vendor involvement.
- End-to-end latency from qualifying event to downstream audience update is
  typically 30–90 seconds, destination-dependent.
- Individual profile attributes can be activated, not only segment
  membership.
- **Consent is enforced at activation time**: a profile lacking consent for
  the destination's purpose is excluded from the payload.
- Activations run either on a schedule or continuously.

## Analytics

- Standard reporting on segment size over time, activation delivery, and
  ingestion volume.
- Ad hoc report builder for business users.
- Funnel and cohort analysis on ingested events.
- Scheduled export of reporting data to CSV or a connected warehouse.
- Meridian does not provide marketing attribution modelling.
- Reporting data freshness is under 5 minutes behind ingestion.
- Dashboards are shareable by link to authenticated users only; there is no
  view-only licence tier.
- Alerting on anomalous segment size change or ingestion volume drop, via
  email, Slack, or webhook.
- Raw event data is available for independent analysis via warehouse export.

## Consent and preference management

- Consent state stored per processing purpose, per profile.
- Native integrations with OneTrust and Didomi consent management platforms.
- Activation-time enforcement prevents contacting a profile without the
  relevant consent.
- All consent changes are audit-logged with timestamp, source system, and
  prior value.
- Granular preferences: channel-level and frequency-level opt-out.
- Consent withdrawal propagates to connected destinations within 15 minutes
  and triggers a suppression instruction where the destination supports one.
- Jurisdiction-specific consent models are supported, with opt-in or opt-out
  defaults set per region.
- Where jurisdiction or age is unknown, Meridian applies the most restrictive
  configured policy.
- Meridian does not host a customer-facing preference centre; it integrates
  with one.

## Deployment and regions

Multi-tenant SaaS on AWS. Data is logically isolated per tenant with
per-tenant encryption keys. **Meridian does not offer single-tenant,
dedicated-infrastructure, or customer-managed deployments.**

Data may be hosted in **US (us-east-1)** or **EU (eu-west-1)**, elected at
provisioning. No other region is available today — see `roadmap.md`.

## Data export and portability

Full self-serve export of all account data in CSV or Parquet, via console or
API, at any time, with no export fee. On termination, data remains
retrievable for 30 days and is irrecoverably destroyed within 60 days.
