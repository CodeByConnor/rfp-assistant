# Request for Proposal: Customer Data Platform

**Issuing organization:** Alderwood Retail Group  
**RFP reference:** ARG-CDP-2026-014  
**Issued:** 1 July 2026  
**Clarification questions due:** 25 July 2026  
**Responses due:** 15 August 2026, 5:00 p.m. Pacific  
**Submit to:** procurement@alderwoodretail.example

> Generated from `fixtures/requirements_data.py`. Do not edit by hand —
> edit the data module and re-run `build_md_fixture.py`.

Respond to every numbered requirement with one of: **Standard**,
**Configuration**, **Customization**, **Third-Party**, **Roadmap**, or
**Not Supported**, together with a supporting explanation.

---

## Section 1 — Vendor Profile and Corporate Information

This section establishes vendor viability. Responses are narrative rather than compliance-scored, and are evaluated on a pass/fail basis by Alderwood's procurement and finance teams.

### 1.1 Corporate Background

**1.1.1** _[Must, weight 1]_  
State your full legal entity name, jurisdiction of incorporation, headquarters address, and any parent or holding company.

**1.1.2** _[Must, weight 1]_  
State the year the company was founded and the year the product offered in this response first became generally available.

**1.1.3** _[Should, weight 1]_  
State your current total headcount, broken out by engineering, customer support, professional services, and sales.

**1.1.4** _[Must, weight 2]_  
Describe your ownership structure and funding history. If venture-backed, state your most recent funding round and date.

**1.1.5** _[Must, weight 2]_  
Confirm whether the company has been profitable for the last two consecutive fiscal years, or state your current cash runway in months.

**1.1.6** _[Must, weight 2]_  
Disclose any merger, acquisition, or change-of-control event involving your company in the last 36 months, whether as acquirer or target.

**1.1.7** _[Must, weight 3]_  
Disclose any material litigation, regulatory enforcement action, or data protection authority investigation involving your company in the last 60 months.

### 1.2 Customer Base and References

**1.2.1** _[Must, weight 2]_  
State the total number of customers currently in production on the platform offered in this response.

**1.2.2** _[Should, weight 2]_  
State how many of those customers are in retail or grocery, and how many operate more than 100 physical store locations.

**1.2.3** _[Must, weight 3]_  
Provide three reference customers of comparable size and industry, including contact name, title, and a summary of the deployment. References will be contacted only for shortlisted vendors.

**1.2.4** _[Should, weight 2]_  
State your gross and net revenue retention rates for the most recent completed fiscal year.

**1.2.5** _[Nice, weight 1]_  
Disclose any customer with more than 10 percent of total company revenue.

---

## Section 2 — Functional Requirements

Functional requirements describe the customer data platform capabilities Alderwood expects to operate. Respond to every line item with a compliance level and a supporting explanation.

### 2.1 Data Ingestion and Source Connectivity

**2.1.1** _[Must, weight 5]_  
The platform must ingest customer event data from a web storefront via a JavaScript tag or SDK.

**2.1.2** _[Must, weight 4]_  
The platform must ingest customer event data from native iOS and Android mobile applications.

**2.1.3** _[Must, weight 5]_  
The platform must ingest transaction records from in-store point-of-sale systems via batch file delivery.

**2.1.4** _[Must, weight 4]_  
Describe supported batch ingestion mechanisms, including SFTP, cloud object storage, and any file format constraints.

**2.1.5** _[Must, weight 4]_  
The platform must support server-side event ingestion over HTTP for systems that cannot run a client SDK.

**2.1.6** _[Must, weight 5]_  
Confirm native connector support for Shopify Plus, which hosts Alderwood's e-commerce storefront.

**2.1.7** _[Must, weight 5]_  
Confirm native connector support for Salesforce Marketing Cloud, which Alderwood uses for email and SMS execution.

**2.1.8** _[Must, weight 4]_  
Describe ingestion from a cloud data warehouse. Alderwood operates Snowflake as its analytics warehouse.

**2.1.9** _[Should, weight 4]_  
Describe how the platform handles late-arriving or out-of-order events, including any correction of previously computed segment membership.

**2.1.10** _[Should, weight 3]_  
Describe schema validation on ingestion and the disposition of records that fail validation.

**2.1.11** _[Should, weight 3]_  
State the maximum sustained and burst event ingestion rate supported per account.

### 2.2 Identity Resolution

**2.2.1** _[Must, weight 5]_  
The platform must resolve customer identity across web, mobile, and offline point-of-sale sources into a single unified profile.

**2.2.2** _[Must, weight 5]_  
Describe whether identity matching is deterministic, probabilistic, or both, and state which is applied by default.

**2.2.3** _[Must, weight 4]_  
Describe the identifiers supported for matching, including email, phone, loyalty number, device identifier, and hashed identifiers.

**2.2.4** _[Should, weight 4]_  
The platform must support a customer-defined match rule hierarchy rather than a fixed vendor-defined precedence.

**2.2.5** _[Should, weight 4]_  
Describe how identity graph conflicts are surfaced and resolved, including the ability for an operator to manually merge or split profiles.

**2.2.6** _[Must, weight 4]_  
Describe how an unauthenticated web session is later associated with a known customer profile upon authentication.

**2.2.7** _[Should, weight 3]_  
State the expected match rate for a retailer with an anonymous-to-known ratio of approximately 8:1, and describe how that figure is measured.

**2.2.8** _[Should, weight 3]_  
Describe support for household-level or address-level grouping in addition to individual identity.

**2.2.9** _[Should, weight 3]_  
Describe the audit trail available for identity merge operations, including whether a merge can be reversed.

**2.2.10** _[Should, weight 3]_  
Describe how identity resolution behaves when a loyalty number is shared across multiple household members, a common pattern in Alderwood's programme.

**2.2.11** _[Must, weight 4]_  
State whether identity resolution runs in real time on event arrival, on a scheduled batch, or both.

**2.2.12** _[Nice, weight 2]_  
Describe any limits on identity graph size, including maximum identifiers per profile.

### 2.3 Customer Profile Management

**2.3.1** _[Must, weight 5]_  
The platform must maintain a unified customer profile combining behavioural events, transaction history, and customer attributes.

**2.3.2** _[Must, weight 4]_  
State any limit on the number of custom attributes that may be defined on a customer profile.

**2.3.3** _[Must, weight 4]_  
Describe support for computed or derived attributes, including whether they are recalculated in real time.

**2.3.4** _[Must, weight 4]_  
The platform must expose a single-customer view in the user interface, showing profile attributes and a chronological event timeline.

**2.3.5** _[Must, weight 4]_  
Describe the API available for retrieving a single customer profile by identifier, including expected response latency.

**2.3.6** _[Should, weight 3]_  
Describe support for profile-level data corrections applied by a business user without engineering involvement.

**2.3.7** _[Must, weight 4]_  
State the default and maximum configurable retention period for profile and event data.

**2.3.8** _[Should, weight 3]_  
Describe how the platform handles profiles that have had no activity for an extended period, including any archival behaviour.

**2.3.9** _[Should, weight 3]_  
Describe whether profile schema changes can be made without reprocessing historical data.

**2.3.10** _[Must, weight 4]_  
Describe support for storing consent state as a first-class profile attribute rather than a custom field.

### 2.4 Segmentation

**2.4.1** _[Must, weight 5]_  
The platform must provide a visual segment builder usable by a marketing user without SQL knowledge.

**2.4.2** _[Should, weight 4]_  
The platform must support segment definitions expressed in SQL for advanced analytical users.

**2.4.3** _[Must, weight 5]_  
Describe support for real-time segment membership evaluation, and state the expected latency from qualifying event to segment membership.

**2.4.4** _[Must, weight 4]_  
Describe support for behavioural segmentation based on event sequence and event recency.

**2.4.5** _[Should, weight 3]_  
Describe support for segment membership based on predicted values such as churn likelihood or predicted lifetime value.

**2.4.6** _[Should, weight 3]_  
The platform must support nested or composite segments referencing other segments.

**2.4.7** _[Should, weight 3]_  
Describe how segment size is estimated before a segment is activated, and whether estimation is exact or sampled.

**2.4.8** _[Should, weight 3]_  
Describe version history for segment definitions, including the ability to see who changed a definition and when.

**2.4.9** _[Nice, weight 2]_  
State any limit on the number of active segments per account.

**2.4.10** _[Must, weight 4]_  
Describe support for suppression or exclusion segments applied globally across activations.

**2.4.11** _[Should, weight 4]_  
Describe how segment membership changes are made available to downstream systems, including whether entry and exit are both emitted.

**2.4.12** _[Should, weight 3]_  
Describe support for A/B or holdout group assignment within a segment for measurement purposes.

### 2.5 Activation and Orchestration

**2.5.1** _[Must, weight 5]_  
The platform must activate segments to Salesforce Marketing Cloud for email and SMS campaign execution.

**2.5.2** _[Should, weight 4]_  
Describe activation to paid media destinations, including Meta and Google advertising audiences.

**2.5.3** _[Must, weight 4]_  
Describe reverse ETL capability for writing computed segments and traits back into a data warehouse.

**2.5.4** _[Must, weight 4]_  
The platform must support outbound webhooks triggered on segment entry or exit.

**2.5.5** _[Should, weight 3]_  
Describe any journey or campaign orchestration capability native to the platform, as distinct from activation into an external tool.

**2.5.6** _[Should, weight 3]_  
Describe throttling and rate-limit handling when a destination system rejects or delays writes.

**2.5.7** _[Must, weight 4]_  
Describe error visibility for failed activations, including whether a business user can see and retry failures without vendor support.

**2.5.8** _[Should, weight 4]_  
State the expected end-to-end latency from qualifying event to delivery of an audience update at a downstream destination.

**2.5.9** _[Should, weight 3]_  
Describe support for activation of individual profile attributes, as distinct from segment membership alone.

**2.5.10** _[Must, weight 5]_  
Describe how consent state is enforced at activation time to prevent contacting a customer who has withdrawn consent.

**2.5.11** _[Should, weight 3]_  
Describe support for scheduled versus continuously syncing activations.

### 2.6 Analytics and Reporting

**2.6.1** _[Should, weight 3]_  
Describe the standard reporting available on segment performance and audience growth.

**2.6.2** _[Should, weight 3]_  
The platform must allow a business user to build an ad hoc report without engineering involvement.

**2.6.3** _[Should, weight 3]_  
Describe support for funnel and cohort analysis on ingested event data.

**2.6.4** _[Should, weight 3]_  
Describe export of reporting data to a business intelligence tool.

**2.6.5** _[Nice, weight 2]_  
Describe any attribution modelling capability, and state which models are supported.

**2.6.6** _[Should, weight 3]_  
State the data freshness of reporting relative to event ingestion.

**2.6.7** _[Nice, weight 2]_  
Describe dashboarding capability, including whether dashboards can be shared with users who do not hold a full platform licence.

**2.6.8** _[Should, weight 3]_  
Describe alerting on anomalous changes in segment size or ingestion volume.

**2.6.9** _[Should, weight 3]_  
Describe availability of raw event data for independent analysis outside the platform.

### 2.7 Consent and Preference Management

**2.7.1** _[Must, weight 5]_  
The platform must record and store customer consent state per processing purpose.

**2.7.2** _[Should, weight 4]_  
Describe integration with a consent management platform, and name any supported vendors.

**2.7.3** _[Must, weight 5]_  
The platform must prevent activation of a customer to a destination for which consent has not been granted.

**2.7.4** _[Must, weight 4]_  
Describe the audit trail retained for consent state changes, including timestamp and source of the change.

**2.7.5** _[Should, weight 4]_  
Describe support for granular communication preferences, such as channel-level and frequency-level opt-out.

**2.7.6** _[Must, weight 5]_  
Describe how consent withdrawal propagates to downstream destinations already holding the customer record.

**2.7.7** _[Should, weight 4]_  
Describe support for jurisdiction-specific consent models, including opt-in versus opt-out defaults.

**2.7.8** _[Should, weight 3]_  
Describe handling of consent for customers whose age or jurisdiction is unknown.

**2.7.9** _[Nice, weight 2]_  
Describe any capability to capture consent directly through a platform-hosted preference centre.

---

## Section 3 — Technical Requirements

Technical requirements cover platform architecture, scale, and extensibility. Responses will be evaluated by Alderwood's enterprise architecture and data engineering teams.

### 3.1 Architecture and Deployment

**3.1.1** _[Must, weight 4]_  
Describe the platform's deployment architecture, including cloud provider and the degree of tenant isolation.

**3.1.2** _[Must, weight 4]_  
Confirm whether a single-tenant or dedicated-infrastructure deployment is available. Alderwood's security team has a stated preference for single-tenant deployment for PII-heavy workloads.

**3.1.3** _[Must, weight 5]_  
State the regions in which customer data may be hosted. Alderwood requires United States data residency at minimum.

**3.1.4** _[Must, weight 4]_  
Describe the environment model available to customers, including whether a non-production sandbox is provided and whether it is separately licensed.

**3.1.5** _[Should, weight 3]_  
Describe how platform upgrades are delivered, including whether customers may defer a release and what notice is given.

**3.1.6** _[Must, weight 4]_  
Describe the change management process for breaking API changes, including the deprecation window offered.

**3.1.7** _[Should, weight 3]_  
Describe any dependency on third-party subprocessors within the request path for real-time operations.

**3.1.8** _[Nice, weight 2]_  
Confirm whether the platform is offered as a customer-managed deployment within Alderwood's own cloud account.

**3.1.9** _[Should, weight 4]_  
Describe the platform's multi-region failover architecture and whether failover is automatic.

### 3.2 Scalability and Performance

**3.2.1** _[Must, weight 4]_  
State the largest production deployment on the platform today, measured in tracked customer profiles and monthly event volume.

**3.2.2** _[Must, weight 5]_  
Confirm the platform can support 2.1 million tracked customer profiles with headroom for 20 percent annual growth.

**3.2.3** _[Must, weight 4]_  
State expected peak event throughput supported, and describe behaviour when that ceiling is exceeded.

**3.2.4** _[Must, weight 5]_  
Describe platform behaviour during a retail peak event such as the week following American Thanksgiving, when Alderwood's traffic increases approximately fivefold.

**3.2.5** _[Must, weight 4]_  
State the published API rate limits and describe whether they can be raised contractually.

**3.2.6** _[Should, weight 4]_  
State the p50 and p99 latency for a single profile lookup by identifier.

**3.2.7** _[Should, weight 3]_  
Describe how query performance degrades as profile count and event history grow.

**3.2.8** _[Should, weight 3]_  
Describe any batch processing windows during which platform functionality is reduced.

**3.2.9** _[Nice, weight 2]_  
Describe capacity planning support provided ahead of a known traffic peak.

### 3.3 APIs, SDKs, and Extensibility

**3.3.1** _[Must, weight 4]_  
Describe the REST APIs available for profile read and write operations.

**3.3.2** _[Should, weight 4]_  
Describe the APIs available for programmatic segment creation and management.

**3.3.3** _[Should, weight 3]_  
State whether API documentation is publicly accessible without a customer login, and provide the URL.

**3.3.4** _[Must, weight 4]_  
Describe supported single sign-on protocols for administrative console access.

**3.3.5** _[Should, weight 3]_  
Describe available client SDKs by language and platform, and state which are vendor-maintained.

**3.3.6** _[Must, weight 4]_  
Describe webhook capability, including delivery guarantees, retry behaviour, and signature verification.

**3.3.7** _[Must, weight 4]_  
Confirm whether a managed connector is available for streaming raw event data into a Kafka topic for downstream consumption by Alderwood's data engineering team.

**3.3.8** _[Should, weight 3]_  
Describe support for customer-authored transformation logic executed within the platform.

**3.3.9** _[Should, weight 3]_  
List pre-built connectors for e-commerce platforms and state which are vendor-maintained versus partner-maintained.

**3.3.10** _[Should, weight 3]_  
Describe the process and typical timeline for building a connector not present in the catalogue.

**3.3.11** _[Should, weight 3]_  
Describe API versioning policy, including how long a prior version remains supported.

### 3.4 Data Management

**3.4.1** _[Must, weight 4]_  
Describe the data model, including whether the event schema is fixed or customer-defined.

**3.4.2** _[Should, weight 3]_  
State any limit on the number of custom attributes that may be defined per customer profile.

**3.4.3** _[Must, weight 5]_  
Confirm that Alderwood may export the full contents of its data at any time, and state whether an export fee applies.

**3.4.4** _[Must, weight 4]_  
Describe supported export formats and the mechanism by which an export is initiated.

**3.4.5** _[Must, weight 5]_  
Describe data deletion behaviour on contract termination, including the period after which data is irrecoverably destroyed.

**3.4.6** _[Should, weight 4]_  
Describe data lineage capability, specifically the ability to trace a profile attribute back to the source record that produced it.

**3.4.7** _[Should, weight 3]_  
Describe data quality monitoring available on ingested data, including detection of schema drift.

**3.4.8** _[Must, weight 4]_  
Describe support for backfilling historical data at initial load, and state any volume limits on backfill.

**3.4.9** _[Should, weight 3]_  
Describe deduplication of identical events delivered more than once.

### 3.5 Monitoring and Observability

**3.5.1** _[Should, weight 3]_  
Describe the operational dashboards available to a customer administrator for monitoring ingestion health.

**3.5.2** _[Must, weight 4]_  
Describe alerting available on ingestion failure or pipeline delay, including supported notification channels.

**3.5.3** _[Must, weight 3]_  
Confirm the availability of a public status page and state whether historical uptime is published.

**3.5.4** _[Should, weight 3]_  
Describe how planned maintenance is communicated and the notice period given.

**3.5.5** _[Should, weight 4]_  
Describe whether platform logs can be forwarded to a customer-operated SIEM.

**3.5.6** _[Should, weight 3]_  
State the retention period for operational and diagnostic logs.

**3.5.7** _[Should, weight 3]_  
Describe support for tracing an individual record through the ingestion pipeline for troubleshooting.

---

## Section 4 — Information Security

This section follows a standardised security questionnaire structure. Alderwood's information security team will score this section independently. A 'Not Supported' response against a Must requirement in this section is presumptively disqualifying.

### 4.1 Security Governance and Certification

**4.1.1** _[Must, weight 5]_  
List all current security certifications and attestations, including SOC 2, ISO 27001, and PCI DSS, and state the availability of each report.

**4.1.2** _[Must, weight 5]_  
Confirm whether you hold a current SOC 2 Type II attestation and state the date of the most recent report.

**4.1.3** _[Must, weight 4]_  
Confirm whether you hold ISO 27001 certification. If certification is in progress, state the expected completion date.

**4.1.4** _[Must, weight 4]_  
Confirm whether you maintain a documented information security policy reviewed at least annually by executive management.

**4.1.5** _[Should, weight 3]_  
State whether you employ a dedicated Chief Information Security Officer or equivalent, and to whom that role reports.

**4.1.6** _[Should, weight 3]_  
Describe mandatory security awareness training for employees, including frequency.

**4.1.7** _[Must, weight 4]_  
Describe background screening performed on employees with access to customer production data.

### 4.2 Identity and Access Management

**4.2.1** _[Must, weight 5]_  
Confirm support for SAML 2.0 single sign-on for platform user authentication.

**4.2.2** _[Should, weight 3]_  
Confirm support for OpenID Connect as an alternative federation protocol.

**4.2.3** _[Must, weight 5]_  
Confirm support for multi-factor authentication on platform administrator accounts, and state whether it can be enforced organisation-wide.

**4.2.4** _[Must, weight 4]_  
Confirm support for SCIM-based automated user provisioning and deprovisioning.

**4.2.5** _[Must, weight 5]_  
Describe role-based access control, including whether custom roles may be defined by a customer administrator without vendor involvement.

**4.2.6** _[Should, weight 4]_  
Describe whether permissions can be scoped to a subset of customer records, for example restricting a regional manager to loyalty members associated with that region.

**4.2.7** _[Should, weight 3]_  
Describe whether access grants can be issued on a time-bound basis that expires without administrator intervention.

**4.2.8** _[Must, weight 5]_  
Describe the process governing vendor personnel access to customer production data, including whether customer approval is required.

**4.2.9** _[Must, weight 4]_  
Confirm that all administrative actions are captured in an audit log, and state the retention period for that log.

**4.2.10** _[Must, weight 4]_  
Confirm that the audit log is exportable via API for ingestion into a customer-operated SIEM.

**4.2.11** _[Should, weight 3]_  
Describe password policy enforcement for accounts not federated through single sign-on.

### 4.3 Data Protection

**4.3.1** _[Must, weight 5]_  
Confirm that customer data is encrypted at rest, and state the cipher and key length used.

**4.3.2** _[Must, weight 5]_  
Confirm that customer data is encrypted in transit, and state the minimum TLS version enforced on external endpoints.

**4.3.3** _[Must, weight 5]_  
Describe encryption key management, including whether keys are unique per tenant and who holds custody.

**4.3.4** _[Should, weight 4]_  
Confirm whether customer-managed encryption keys are supported.

**4.3.5** _[Should, weight 3]_  
Describe data masking or tokenisation available for sensitive profile attributes.

**4.3.6** _[Must, weight 4]_  
Describe controls preventing production customer data from being copied into non-production environments.

**4.3.7** _[Must, weight 4]_  
Confirm whether production data is used in testing, and if so under what controls.

**4.3.8** _[Should, weight 3]_  
Describe secure media disposal procedures for decommissioned storage hardware.

**4.3.9** _[Must, weight 4]_  
Confirm that all storage tiers, including backups and archives, are encrypted at rest.

### 4.4 Application Security

**4.4.1** _[Must, weight 4]_  
Describe your secure software development lifecycle, including security review gates prior to release.

**4.4.2** _[Must, weight 5]_  
Describe your penetration testing programme, including cadence, whether testing is performed by an independent third party, and the availability of results.

**4.4.3** _[Must, weight 4]_  
State the date of your most recent third-party penetration test and confirm whether an executive summary can be shared.

**4.4.4** _[Should, weight 4]_  
Describe static and dynamic application security testing performed in your build pipeline.

**4.4.5** _[Must, weight 4]_  
Describe dependency and container vulnerability scanning, including remediation service levels by severity.

**4.4.6** _[Should, weight 3]_  
Confirm whether you operate a vulnerability disclosure programme or bug bounty, and name the platform used.

**4.4.7** _[Must, weight 4]_  
Describe your process for notifying customers of a critical vulnerability affecting the platform.

**4.4.8** _[Should, weight 3]_  
Describe controls against common web application vulnerabilities, with reference to a recognised framework.

### 4.5 Infrastructure and Network Security

**4.5.1** _[Must, weight 4]_  
Describe network segmentation between the platform's public-facing tier and its data tier.

**4.5.2** _[Must, weight 4]_  
Describe intrusion detection and prevention controls in the production environment.

**4.5.3** _[Should, weight 3]_  
Describe denial of service mitigation for public-facing endpoints.

**4.5.4** _[Should, weight 3]_  
Confirm whether IP allow-listing is supported for administrative console access.

**4.5.5** _[Must, weight 4]_  
Describe physical security controls at facilities hosting customer data, or name the cloud provider whose controls apply.

**4.5.6** _[Should, weight 3]_  
Describe endpoint protection deployed on employee workstations with access to production systems.

**4.5.7** _[Should, weight 3]_  
Describe hardening standards applied to production servers and container images.

### 4.6 Incident Response

**4.6.1** _[Must, weight 5]_  
Confirm that you maintain a documented incident response plan and state how frequently it is tested.

**4.6.2** _[Must, weight 5]_  
State the contractual notification period following confirmation of a security incident affecting customer data.

**4.6.3** _[Must, weight 4]_  
Describe the information provided to affected customers during an active incident, and the cadence of updates.

**4.6.4** _[Must, weight 4]_  
Confirm whether customers receive a written post-incident report including root cause and corrective actions.

**4.6.5** _[Must, weight 5]_  
Disclose any security incident affecting customer data in the last 36 months, including its resolution.

**4.6.6** _[Should, weight 3]_  
Describe forensic support available to a customer following an incident.

### 4.7 Business Continuity and Disaster Recovery

**4.7.1** _[Must, weight 5]_  
State your Recovery Point Objective for the production environment.

**4.7.2** _[Must, weight 5]_  
State your Recovery Time Objective for the production environment.

**4.7.3** _[Must, weight 4]_  
Describe backup frequency and backup retention period.

**4.7.4** _[Must, weight 4]_  
Confirm how frequently backup restoration is tested, and state the date of the most recent successful restoration test.

**4.7.5** _[Should, weight 4]_  
Describe the redundancy model within a hosting region.

**4.7.6** _[Must, weight 4]_  
Confirm whether a business continuity plan is maintained and tested at least annually.

### 4.8 Third-Party and Supply Chain Risk

**4.8.1** _[Must, weight 5]_  
Provide a current list of subprocessors with access to customer data, including the purpose of each.

**4.8.2** _[Must, weight 4]_  
State the notice period given to customers before a new subprocessor is engaged, and whether customers may object.

**4.8.3** _[Must, weight 4]_  
Describe security due diligence performed on subprocessors prior to engagement.

**4.8.4** _[Must, weight 4]_  
Confirm whether you carry cyber liability insurance, and state the coverage limit.

**4.8.5** _[Should, weight 3]_  
Describe controls governing use of generative AI tooling by your engineering staff on customer data or customer-derived code.

---

## Section 5 — Privacy and Regulatory Compliance

Alderwood operates a loyalty programme covering 2.1 million members and captures transaction data from 22 in-store pharmacy counters. Responses in this section will be reviewed by Alderwood's legal and compliance functions.

### 5.1 Regulatory Compliance

**5.1.1** _[Must, weight 5]_  
Confirm compliance with the California Consumer Privacy Act as amended, including support for consumer access and deletion requests.

**5.1.2** _[Must, weight 4]_  
Confirm compliance with the General Data Protection Regulation and the availability of a Data Processing Agreement.

**5.1.3** _[Must, weight 5]_  
Confirm compliance with applicable Washington State health data legislation as it applies to consumer health data collected outside a clinical setting.

**5.1.4** _[Must, weight 5]_  
Alderwood's loyalty programme captures purchase data originating from 22 in-store pharmacy counters. Confirm whether your platform is HIPAA compliant and whether you will execute a Business Associate Agreement.

**5.1.5** _[Must, weight 4]_  
Describe how the platform supports segregation of health-adjacent purchase data from general loyalty data.

**5.1.6** _[Must, weight 4]_  
Confirm whether you will execute Alderwood's standard Data Processing Addendum, or state your required exceptions.

**5.1.7** _[Must, weight 4]_  
State the default and maximum configurable data retention period, and confirm retention can be set per data category.

**5.1.8** _[Must, weight 5]_  
Describe your policy on using customer data to train machine learning models, including whether customers may opt out.

### 5.2 Data Subject Rights

**5.2.1** _[Must, weight 5]_  
Describe the mechanism by which a consumer access request is fulfilled, including whether it can be initiated via API.

**5.2.2** _[Must, weight 5]_  
Describe the mechanism by which a consumer deletion request is fulfilled across all storage tiers including backups.

**5.2.3** _[Must, weight 4]_  
State the maximum elapsed time between a deletion request and irrecoverable deletion of the record.

**5.2.4** _[Must, weight 5]_  
Describe how a deletion request propagates to downstream destinations to which the profile was previously activated.

**5.2.5** _[Should, weight 3]_  
Describe support for data portability, providing a consumer's data in a machine-readable format.

**5.2.6** _[Must, weight 4]_  
Describe the audit record retained to evidence fulfilment of a data subject request.

**5.2.7** _[Should, weight 3]_  
Describe handling of a deletion request for a profile that is a member of an active segment.

### 5.3 Data Residency and Cross-Border Transfer

**5.3.1** _[Must, weight 5]_  
State all regions in which customer data may be stored at rest.

**5.3.2** _[Must, weight 5]_  
Confirm that Alderwood's data can be stored exclusively within the United States.

**5.3.3** _[Must, weight 4]_  
Alderwood anticipates expanding operations into Canada within 18 months. Confirm whether customer data can be hosted so as to meet Canadian data residency expectations.

**5.3.4** _[Must, weight 4]_  
Describe whether support and engineering personnel outside the storage region may access customer data, and under what controls.

**5.3.5** _[Should, weight 3]_  
Describe the legal transfer mechanism relied upon for any cross-border transfer of personal data.

**5.3.6** _[Must, weight 4]_  
Confirm whether data may be processed, as distinct from stored, outside the elected region.

---

## Section 6 — Implementation and Professional Services

### 6.1 Implementation Approach

**6.1.1** _[Must, weight 4]_  
Describe your implementation methodology and typical project phases.

**6.1.2** _[Must, weight 5]_  
State the typical elapsed time to first production value for a customer of Alderwood's size and source complexity.

**6.1.3** _[Must, weight 4]_  
Provide an indicative project plan for a deployment covering web, mobile, point-of-sale, and loyalty data sources.

**6.1.4** _[Must, weight 4]_  
State the Alderwood resources and roles you expect to be committed during implementation, and the approximate time commitment of each.

**6.1.5** _[Must, weight 4]_  
Describe how historical data migration is handled at initial load.

**6.1.6** _[Must, weight 4]_  
Describe your approach to validating that migrated data is complete and accurate.

**6.1.7** _[Should, weight 3]_  
Describe the acceptance criteria you propose for implementation sign-off.

### 6.2 Services and Enablement

**6.2.1** _[Must, weight 4]_  
State which professional services are included in the subscription and which are billed separately.

**6.2.2** _[Must, weight 3]_  
State your standard professional services rates by role.

**6.2.3** _[Must, weight 3]_  
Describe training provided for administrators and for business users, and state whether it is included.

**6.2.4** _[Nice, weight 2]_  
Describe available certification programmes for customer staff.

**6.2.5** _[Should, weight 3]_  
Confirm whether implementation may be delivered by a third-party systems integrator, and name any certified partners in North America.

---

## Section 7 — Support and Service Levels

### 7.1 Service Level Commitments

**7.1.1** _[Must, weight 5]_  
State the uptime service level commitment offered, and confirm whether it is contractual.

**7.1.2** _[Must, weight 4]_  
State the remedy available in the event of a service level breach, including the service credit schedule.

**7.1.3** _[Must, weight 4]_  
State how uptime is measured and confirm whether the measurement is independently verifiable.

**7.1.4** _[Must, weight 4]_  
State what is excluded from the uptime calculation, including planned maintenance.

**7.1.5** _[Should, weight 4]_  
State whether a data freshness or processing latency service level is offered in addition to uptime.

### 7.2 Support Model

**7.2.1** _[Must, weight 5]_  
State support response time commitments by severity level for the tier proposed in this response.

**7.2.2** _[Must, weight 5]_  
Confirm whether 24-hour support is available every day of the year, and state through which channels.

**7.2.3** _[Should, weight 3]_  
State the geographic locations from which support is delivered.

**7.2.4** _[Must, weight 4]_  
Confirm whether a named Technical Account Manager or Customer Success Manager is assigned, and state whether that is included in the proposed tier.

**7.2.5** _[Must, weight 4]_  
Describe the escalation path available when a severity one issue is not progressing.

**7.2.6** _[Should, weight 3]_  
Describe the support ticketing system provided and whether it integrates with a customer-operated service desk.

**7.2.7** _[Must, weight 4]_  
State your published support hours and confirm coverage of Alderwood's peak retail trading period.

---

## Section 8 — Commercial Terms and Corporate Responsibility

### 8.1 Pricing and Commercial Structure

**8.1.1** _[Must, weight 5]_  
Provide pricing for a deployment covering approximately 2.1 million tracked customer profiles, including any volume discount structure.

**8.1.2** _[Must, weight 4]_  
State your overage billing policy in the event tracked profile volume exceeds the contracted tier mid-term.

**8.1.3** _[Must, weight 4]_  
State your pricing metric and confirm whether it is based on tracked profiles, events, or another unit.

**8.1.4** _[Must, weight 4]_  
State your standard annual uplift on renewal and confirm whether it can be capped contractually.

**8.1.5** _[Should, weight 3]_  
Confirm whether multi-year pricing is available and state the discount offered for a three-year commitment.

**8.1.6** _[Should, weight 3]_  
State your standard payment terms and confirm whether annual invoicing in advance is required.

**8.1.7** _[Should, weight 3]_  
Confirm whether a non-production sandbox environment is separately chargeable.

### 8.2 Contractual Terms

**8.2.1** _[Must, weight 4]_  
State your standard contract term and any minimum commitment.

**8.2.2** _[Must, weight 4]_  
Describe termination rights available to the customer, including termination for convenience.

**8.2.3** _[Must, weight 5]_  
State your limitation of liability and confirm whether it can be raised for data protection breaches.

### 8.3 Corporate Responsibility

**8.3.1** _[Should, weight 2]_  
Describe your environmental sustainability programme, including any data centre carbon footprint commitments, offset purchases, or published emissions reporting.

**8.3.2** _[Nice, weight 1]_  
State whether you publish a modern slavery or supply chain transparency statement, and provide the URL.

**8.3.3** _[Nice, weight 1]_  
Describe your supplier diversity programme, if any.

---
