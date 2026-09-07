# Meridian — Integrations Catalog

*Doc type: public | Last updated: 2026-05-20*

## Native integrations (pre-built connectors)

| Category      | Integrations                                              |
|---------------|-------------------------------------------------------------|
| CRM           | Salesforce Sales Cloud, Salesforce Marketing Cloud, HubSpot |
| E-commerce    | Shopify, Shopify Plus, BigCommerce                          |
| Data warehouse| Snowflake, BigQuery, Redshift (reverse ETL + ingestion)      |
| Email/SMS     | Klaviyo, Braze, Twilio                                      |
| Advertising   | Meta Ads, Google Ads (audience activation)                  |
| Automation    | Zapier                                                       |

## APIs & SDKs

- REST API for profile read/write, segment management, and event ingestion.
- Web and mobile (iOS/Android) event-tracking SDKs.
- Server-side event ingestion via HTTP API.
- Webhooks for outbound event notification (segment entry/exit, profile
  updates).

## Streaming

- Real-time segmentation is supported natively within Meridian (sub-second
  segment membership updates on qualifying events).
- A managed Kafka connector for streaming raw event data out of Meridian in
  real time is **not yet available** — see `roadmap.md`.

## Custom integrations

Any source or destination not covered by a native connector can be integrated
via the REST API or webhooks. Professional Services can build custom
connectors under a statement of work for Enterprise tier customers.
