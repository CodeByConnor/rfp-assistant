# Meridian — Integrations Catalog

*Doc type: public | Last updated: 2026-05-20*

All connectors below are vendor-maintained unless marked partner-maintained.

## Sources (ingestion)

| Category | Connectors |
|---|---|
| E-commerce | **Shopify**, **Shopify Plus**, BigCommerce, Magento (partner-maintained) |
| CRM | Salesforce Sales Cloud, HubSpot, Microsoft Dynamics 365 |
| Data warehouse | Snowflake, BigQuery, Redshift, Databricks |
| Point of sale | Generic batch file (CSV/Parquet via SFTP or object storage), Toast, Square |
| Loyalty | Generic batch file, Antavo (partner-maintained) |
| Consent | OneTrust, Didomi |
| Web / mobile | JavaScript tag, iOS SDK, Android SDK, server-side HTTP API |

## Destinations (activation)

| Category | Connectors |
|---|---|
| Marketing execution | **Salesforce Marketing Cloud**, Klaviyo, Braze, Iterable, Twilio |
| Advertising | Meta Ads, Google Ads, The Trade Desk |
| Data warehouse | Snowflake, BigQuery, Redshift (reverse ETL) |
| Automation | Zapier, generic webhook |
| Support | Zendesk, Intercom |

## Streaming

- Real-time segmentation is native, with sub-2-second median latency from
  qualifying event to segment membership.
- **A managed Kafka connector for streaming raw event data out of Meridian is
  not available.** See `roadmap.md` — targeted for design Q3 2026, no
  committed ship date.

## Custom connectors

Any source or destination absent from this catalogue can be integrated via the
REST API or webhooks. Professional Services builds custom connectors under a
statement of work; typical delivery is 6–10 weeks. See
`implementation-services.md`.
