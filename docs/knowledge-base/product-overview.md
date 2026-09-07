# Meridian — Product Overview

*Doc type: public | Last updated: 2026-06-01*

Meridian is a B2B customer data platform (CDP) for mid-market retail, e-commerce,
and subscription businesses. It unifies customer data from web, mobile, point-of-sale,
and third-party sources into a single customer profile, enabling real-time
personalization and segmentation.

## Core capabilities

- **Identity resolution**: deterministic and probabilistic matching across web,
  app, offline POS, and CRM sources into a unified customer profile.
- **Segmentation**: real-time (streaming) and batch audience segmentation with a
  visual rule builder and SQL-based custom segments.
- **Activation**: push segments to ad platforms, email/SMS tools, and CRMs via
  native integrations or the REST API.
- **Customer 360 profile**: a queryable, API-accessible profile store combining
  behavioral events, transactional history, and custom attributes.
- **Reverse ETL**: sync computed traits and segments back into a data warehouse
  or downstream operational tools.

## Deployment model

Meridian is a multi-tenant SaaS platform hosted on AWS. Each customer's data is
logically isolated by tenant ID with per-tenant encryption keys. Meridian does
not offer single-tenant or dedicated-infrastructure deployments at this time.

## Supported regions

Data can be hosted in the **US (us-east-1)** or **EU (eu-west-1)** region at
the customer's choice, set at account provisioning time. Data residency
outside these two regions (e.g. Canada, APAC) is not currently supported —
see `roadmap.md`.

## Data model

- Custom event schemas with up to 200 custom attributes per profile.
- Configurable data retention (default 25 months, adjustable per contract).
- Full self-serve data export (CSV/Parquet) at any time via the admin console
  or API — no export fees.
