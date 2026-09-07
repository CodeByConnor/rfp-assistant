# Request for Proposal: Customer Data Platform

**Issuing organization:** Alderwood Retail Group
**RFP reference:** ARG-CDP-2026-014
**Issued:** 2026-07-01
**Response due:** 2026-08-15

## Background

Alderwood Retail Group operates 118 grocery and general-merchandise stores
across the Pacific Northwest and Mountain West, plus an e-commerce storefront
on Shopify Plus and a loyalty program with 2.1M enrolled members (including
purchases made at 22 in-store pharmacy counters). Alderwood is evaluating
customer data platform (CDP) vendors to unify online, in-store, and loyalty
data for unified customer profiles and marketing personalization. Alderwood
currently uses Salesforce Marketing Cloud for email/SMS campaigns.

This document lists Alderwood's requirements. Vendors should respond to each
numbered item with one of: **Yes**, **Partial**, **No**, **Planned/Roadmap**,
along with a brief explanation.

---

## Section A — Company & Product Overview

A1. Describe your platform's core identity resolution capability across web,
    mobile, and offline (in-store POS) data sources.

A2. Describe your data model and any limits on custom customer attributes.

A3. Confirm whether your platform is offered as single-tenant / dedicated
    infrastructure, or multi-tenant SaaS only. Alderwood's security team has
    a stated preference for single-tenant deployments for PII-heavy workloads.

A4. What regions can customer data be hosted in? Alderwood requires U.S.
    data residency at minimum and may expand into Canada within 18 months.

---

## Section B — Security & Compliance

B1. List all current security certifications (SOC 2, ISO 27001, PCI DSS,
    etc.) and provide certificate/report availability.

B2. Describe encryption of data at rest and in transit.

B3. Describe supported single sign-on (SSO) protocols for admin console
    access.

B4. Do you support SCIM-based automated user provisioning/deprovisioning?

B5. Describe role-based access control (RBAC) capabilities.

B6. Describe your penetration testing program and cadence.

B7. Given that Alderwood's loyalty program captures purchase data from
    in-store pharmacy counters, is your platform HIPAA compliant, and will
    you sign a Business Associate Agreement (BAA)?

B8. Describe your disaster recovery capabilities, including RPO and RTO.

B9. Do you support multi-factor authentication (MFA) for platform admin
    accounts?

B10. Describe your approach to sub-processors and third-party data sharing
     disclosure.

---

## Section C — Data Privacy & Residency

C1. Confirm GDPR compliance and availability of a Data Processing Agreement
    (DPA), in case Alderwood expands to EU markets in the future.

C2. Confirm CCPA compliance, including support for consumer data deletion
    and access requests.

C3. If Alderwood expands operations into Canada within the next 18 months,
    can customer data be hosted to meet Canadian data residency
    expectations?

C4. What is your default and maximum configurable data retention period?

---

## Section D — Integrations & Technical Architecture

D1. Confirm native integration support for Salesforce Marketing Cloud.

D2. Confirm native integration support for Shopify Plus.

D3. Describe support for real-time (sub-minute latency) audience
    segmentation and activation.

D4. Do you offer a managed connector for streaming raw event data into a
    Kafka topic for downstream consumption by Alderwood's data engineering
    team?

D5. Describe available REST APIs and SDKs for custom event ingestion.

D6. Describe reverse ETL capabilities to sync computed segments into a data
    warehouse (Alderwood uses Snowflake).

---

## Section E — Reliability, SLA & Support

E1. What uptime SLA do you offer, and what remedy is provided for SLA
    breaches?

E2. Describe support response time commitments by severity level for your
    highest support tier.

E3. Is 24/7 support available, and through which channels?

E4. Will Alderwood be assigned a dedicated Customer Success Manager (CSM)
    and/or Technical Account Manager (TAM)?

---

## Section F — Implementation & Change Management

F1. Describe your typical implementation timeline for a customer of
    Alderwood's size and complexity.

F2. What professional services or implementation support is included versus
    billed separately?

---

## Section G — Corporate Responsibility

G1. Describe your company's environmental sustainability program, including
    any data center carbon footprint commitments or offsets.

---

## Section H — Commercial Terms

H1. Provide pricing for a deployment covering approximately 2.1 million
    tracked customer profiles, including any volume discount structure.

H2. Describe your overage billing policy if tracked profile volume exceeds
    the contracted tier mid-term.
