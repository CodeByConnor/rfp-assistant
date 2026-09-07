"""Single source of truth for the Alderwood RFP fixture.

Every output format (.md, .xlsx, .pdf) is generated from this module, so the
requirement set cannot drift between them. Requirement IDs are hierarchical
(section.subsection.item), matching how real enterprise RFPs number line items.

Fields per requirement:
    rid       hierarchical id, e.g. "4.2.3"
    text      requirement text as written by the buyer
    priority  "Must" | "Should" | "Nice"   (buyer-set)
    weight    numeric scoring weight       (buyer-set)
    dupe      optional tag marking a near-duplicate cluster. Real RFPs are
              committee-written, so the same capability gets asked in two
              sections with different wording. Requirements sharing a dupe tag
              are semantically the same ask; a good pipeline should detect the
              cluster instead of answering it twice from scratch.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Req:
    rid: str
    text: str
    priority: str = "Should"
    weight: int = 3
    dupe: str | None = None


@dataclass(frozen=True)
class Subsection:
    number: str
    title: str
    items: list[Req] = field(default_factory=list)


@dataclass(frozen=True)
class Section:
    number: str
    title: str
    tab: str          # which workbook tab this section lands on
    subsections: list[Subsection] = field(default_factory=list)
    intro: str = ""


RFP_META = {
    "buyer": "Alderwood Retail Group",
    "reference": "ARG-CDP-2026-014",
    "title": "Customer Data Platform",
    "issued": "1 July 2026",
    "questions_due": "25 July 2026",
    "due": "15 August 2026",
    "due_time": "5:00 p.m. Pacific",
    "contact": "procurement@alderwoodretail.example",
}

COMPLIANCE_LEVELS = [
    "Standard",
    "Configuration",
    "Customization",
    "Third-Party",
    "Roadmap",
    "Not Supported",
]

COMPLIANCE_DEFINITIONS = [
    ("Standard", "Available out of the box in the current shipping release, with no configuration beyond initial setup."),
    ("Configuration", "Available in the current release but requires configuration by an administrator. No vendor code changes."),
    ("Customization", "Requires custom development by the vendor or a partner. Must be itemized in the Cost Impact column."),
    ("Third-Party", "Delivered by a third-party product or partner. Name the third party and state whether its licence is included."),
    ("Roadmap", "Not available today but committed on the product roadmap. State the target release and whether the date is contractual."),
    ("Not Supported", "Not available and not planned."),
]

PRIORITY_DEFINITIONS = [
    ("Must", "Mandatory. A 'Not Supported' response against a Must requirement may disqualify the response."),
    ("Should", "Important but not disqualifying. Scored."),
    ("Nice", "Desirable. Scored at reduced weight."),
]


SECTIONS: list[Section] = [
    # ------------------------------------------------------------------ 1
    Section(
        "1", "Vendor Profile and Corporate Information", "Vendor Profile",
        intro=(
            "This section establishes vendor viability. Responses are narrative "
            "rather than compliance-scored, and are evaluated on a pass/fail "
            "basis by Alderwood's procurement and finance teams."
        ),
        subsections=[
            Subsection("1.1", "Corporate Background", [
                Req("1.1.1", "State your full legal entity name, jurisdiction of incorporation, headquarters address, and any parent or holding company.", "Must", 1),
                Req("1.1.2", "State the year the company was founded and the year the product offered in this response first became generally available.", "Must", 1),
                Req("1.1.3", "State your current total headcount, broken out by engineering, customer support, professional services, and sales.", "Should", 1),
                Req("1.1.4", "Describe your ownership structure and funding history. If venture-backed, state your most recent funding round and date.", "Must", 2),
                Req("1.1.5", "Confirm whether the company has been profitable for the last two consecutive fiscal years, or state your current cash runway in months.", "Must", 2),
                Req("1.1.6", "Disclose any merger, acquisition, or change-of-control event involving your company in the last 36 months, whether as acquirer or target.", "Must", 2),
                Req("1.1.7", "Disclose any material litigation, regulatory enforcement action, or data protection authority investigation involving your company in the last 60 months.", "Must", 3),
            ]),
            Subsection("1.2", "Customer Base and References", [
                Req("1.2.1", "State the total number of customers currently in production on the platform offered in this response.", "Must", 2),
                Req("1.2.2", "State how many of those customers are in retail or grocery, and how many operate more than 100 physical store locations.", "Should", 2),
                Req("1.2.3", "Provide three reference customers of comparable size and industry, including contact name, title, and a summary of the deployment. References will be contacted only for shortlisted vendors.", "Must", 3),
                Req("1.2.4", "State your gross and net revenue retention rates for the most recent completed fiscal year.", "Should", 2),
                Req("1.2.5", "Disclose any customer with more than 10 percent of total company revenue.", "Nice", 1),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 2
    Section(
        "2", "Functional Requirements", "Functional",
        intro=(
            "Functional requirements describe the customer data platform "
            "capabilities Alderwood expects to operate. Respond to every line "
            "item with a compliance level and a supporting explanation."
        ),
        subsections=[
            Subsection("2.1", "Data Ingestion and Source Connectivity", [
                Req("2.1.1", "The platform must ingest customer event data from a web storefront via a JavaScript tag or SDK.", "Must", 5),
                Req("2.1.2", "The platform must ingest customer event data from native iOS and Android mobile applications.", "Must", 4),
                Req("2.1.3", "The platform must ingest transaction records from in-store point-of-sale systems via batch file delivery.", "Must", 5),
                Req("2.1.4", "Describe supported batch ingestion mechanisms, including SFTP, cloud object storage, and any file format constraints.", "Must", 4),
                Req("2.1.5", "The platform must support server-side event ingestion over HTTP for systems that cannot run a client SDK.", "Must", 4),
                Req("2.1.6", "Confirm native connector support for Shopify Plus, which hosts Alderwood's e-commerce storefront.", "Must", 5, dupe="shopify"),
                Req("2.1.7", "Confirm native connector support for Salesforce Marketing Cloud, which Alderwood uses for email and SMS execution.", "Must", 5, dupe="sfmc"),
                Req("2.1.8", "Describe ingestion from a cloud data warehouse. Alderwood operates Snowflake as its analytics warehouse.", "Must", 4, dupe="snowflake"),
                Req("2.1.9", "Describe how the platform handles late-arriving or out-of-order events, including any correction of previously computed segment membership.", "Should", 4),
                Req("2.1.10", "Describe schema validation on ingestion and the disposition of records that fail validation.", "Should", 3),
                Req("2.1.11", "State the maximum sustained and burst event ingestion rate supported per account.", "Should", 3),
            ]),
            Subsection("2.2", "Identity Resolution", [
                Req("2.2.1", "The platform must resolve customer identity across web, mobile, and offline point-of-sale sources into a single unified profile.", "Must", 5),
                Req("2.2.2", "Describe whether identity matching is deterministic, probabilistic, or both, and state which is applied by default.", "Must", 5),
                Req("2.2.3", "Describe the identifiers supported for matching, including email, phone, loyalty number, device identifier, and hashed identifiers.", "Must", 4),
                Req("2.2.4", "The platform must support a customer-defined match rule hierarchy rather than a fixed vendor-defined precedence.", "Should", 4),
                Req("2.2.5", "Describe how identity graph conflicts are surfaced and resolved, including the ability for an operator to manually merge or split profiles.", "Should", 4),
                Req("2.2.6", "Describe how an unauthenticated web session is later associated with a known customer profile upon authentication.", "Must", 4),
                Req("2.2.7", "State the expected match rate for a retailer with an anonymous-to-known ratio of approximately 8:1, and describe how that figure is measured.", "Should", 3),
                Req("2.2.8", "Describe support for household-level or address-level grouping in addition to individual identity.", "Should", 3),
                Req("2.2.9", "Describe the audit trail available for identity merge operations, including whether a merge can be reversed.", "Should", 3),
                Req("2.2.10", "Describe how identity resolution behaves when a loyalty number is shared across multiple household members, a common pattern in Alderwood's programme.", "Should", 3),
                Req("2.2.11", "State whether identity resolution runs in real time on event arrival, on a scheduled batch, or both.", "Must", 4),
                Req("2.2.12", "Describe any limits on identity graph size, including maximum identifiers per profile.", "Nice", 2),
            ]),
            Subsection("2.3", "Customer Profile Management", [
                Req("2.3.1", "The platform must maintain a unified customer profile combining behavioural events, transaction history, and customer attributes.", "Must", 5),
                Req("2.3.2", "State any limit on the number of custom attributes that may be defined on a customer profile.", "Must", 4, dupe="custom-attrs"),
                Req("2.3.3", "Describe support for computed or derived attributes, including whether they are recalculated in real time.", "Must", 4),
                Req("2.3.4", "The platform must expose a single-customer view in the user interface, showing profile attributes and a chronological event timeline.", "Must", 4),
                Req("2.3.5", "Describe the API available for retrieving a single customer profile by identifier, including expected response latency.", "Must", 4),
                Req("2.3.6", "Describe support for profile-level data corrections applied by a business user without engineering involvement.", "Should", 3),
                Req("2.3.7", "State the default and maximum configurable retention period for profile and event data.", "Must", 4, dupe="retention"),
                Req("2.3.8", "Describe how the platform handles profiles that have had no activity for an extended period, including any archival behaviour.", "Should", 3),
                Req("2.3.9", "Describe whether profile schema changes can be made without reprocessing historical data.", "Should", 3),
                Req("2.3.10", "Describe support for storing consent state as a first-class profile attribute rather than a custom field.", "Must", 4, dupe="consent-attr"),
            ]),
            Subsection("2.4", "Segmentation", [
                Req("2.4.1", "The platform must provide a visual segment builder usable by a marketing user without SQL knowledge.", "Must", 5),
                Req("2.4.2", "The platform must support segment definitions expressed in SQL for advanced analytical users.", "Should", 4),
                Req("2.4.3", "Describe support for real-time segment membership evaluation, and state the expected latency from qualifying event to segment membership.", "Must", 5),
                Req("2.4.4", "Describe support for behavioural segmentation based on event sequence and event recency.", "Must", 4),
                Req("2.4.5", "Describe support for segment membership based on predicted values such as churn likelihood or predicted lifetime value.", "Should", 3),
                Req("2.4.6", "The platform must support nested or composite segments referencing other segments.", "Should", 3),
                Req("2.4.7", "Describe how segment size is estimated before a segment is activated, and whether estimation is exact or sampled.", "Should", 3),
                Req("2.4.8", "Describe version history for segment definitions, including the ability to see who changed a definition and when.", "Should", 3),
                Req("2.4.9", "State any limit on the number of active segments per account.", "Nice", 2),
                Req("2.4.10", "Describe support for suppression or exclusion segments applied globally across activations.", "Must", 4),
                Req("2.4.11", "Describe how segment membership changes are made available to downstream systems, including whether entry and exit are both emitted.", "Should", 4),
                Req("2.4.12", "Describe support for A/B or holdout group assignment within a segment for measurement purposes.", "Should", 3),
            ]),
            Subsection("2.5", "Activation and Orchestration", [
                Req("2.5.1", "The platform must activate segments to Salesforce Marketing Cloud for email and SMS campaign execution.", "Must", 5, dupe="sfmc"),
                Req("2.5.2", "Describe activation to paid media destinations, including Meta and Google advertising audiences.", "Should", 4),
                Req("2.5.3", "Describe reverse ETL capability for writing computed segments and traits back into a data warehouse.", "Must", 4, dupe="snowflake"),
                Req("2.5.4", "The platform must support outbound webhooks triggered on segment entry or exit.", "Must", 4),
                Req("2.5.5", "Describe any journey or campaign orchestration capability native to the platform, as distinct from activation into an external tool.", "Should", 3),
                Req("2.5.6", "Describe throttling and rate-limit handling when a destination system rejects or delays writes.", "Should", 3),
                Req("2.5.7", "Describe error visibility for failed activations, including whether a business user can see and retry failures without vendor support.", "Must", 4),
                Req("2.5.8", "State the expected end-to-end latency from qualifying event to delivery of an audience update at a downstream destination.", "Should", 4),
                Req("2.5.9", "Describe support for activation of individual profile attributes, as distinct from segment membership alone.", "Should", 3),
                Req("2.5.10", "Describe how consent state is enforced at activation time to prevent contacting a customer who has withdrawn consent.", "Must", 5, dupe="consent-enforce"),
                Req("2.5.11", "Describe support for scheduled versus continuously syncing activations.", "Should", 3),
            ]),
            Subsection("2.6", "Analytics and Reporting", [
                Req("2.6.1", "Describe the standard reporting available on segment performance and audience growth.", "Should", 3),
                Req("2.6.2", "The platform must allow a business user to build an ad hoc report without engineering involvement.", "Should", 3),
                Req("2.6.3", "Describe support for funnel and cohort analysis on ingested event data.", "Should", 3),
                Req("2.6.4", "Describe export of reporting data to a business intelligence tool.", "Should", 3),
                Req("2.6.5", "Describe any attribution modelling capability, and state which models are supported.", "Nice", 2),
                Req("2.6.6", "State the data freshness of reporting relative to event ingestion.", "Should", 3),
                Req("2.6.7", "Describe dashboarding capability, including whether dashboards can be shared with users who do not hold a full platform licence.", "Nice", 2),
                Req("2.6.8", "Describe alerting on anomalous changes in segment size or ingestion volume.", "Should", 3),
                Req("2.6.9", "Describe availability of raw event data for independent analysis outside the platform.", "Should", 3, dupe="raw-export"),
            ]),
            Subsection("2.7", "Consent and Preference Management", [
                Req("2.7.1", "The platform must record and store customer consent state per processing purpose.", "Must", 5, dupe="consent-attr"),
                Req("2.7.2", "Describe integration with a consent management platform, and name any supported vendors.", "Should", 4),
                Req("2.7.3", "The platform must prevent activation of a customer to a destination for which consent has not been granted.", "Must", 5, dupe="consent-enforce"),
                Req("2.7.4", "Describe the audit trail retained for consent state changes, including timestamp and source of the change.", "Must", 4),
                Req("2.7.5", "Describe support for granular communication preferences, such as channel-level and frequency-level opt-out.", "Should", 4),
                Req("2.7.6", "Describe how consent withdrawal propagates to downstream destinations already holding the customer record.", "Must", 5),
                Req("2.7.7", "Describe support for jurisdiction-specific consent models, including opt-in versus opt-out defaults.", "Should", 4),
                Req("2.7.8", "Describe handling of consent for customers whose age or jurisdiction is unknown.", "Should", 3),
                Req("2.7.9", "Describe any capability to capture consent directly through a platform-hosted preference centre.", "Nice", 2),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 3
    Section(
        "3", "Technical Requirements", "Technical",
        intro=(
            "Technical requirements cover platform architecture, scale, and "
            "extensibility. Responses will be evaluated by Alderwood's "
            "enterprise architecture and data engineering teams."
        ),
        subsections=[
            Subsection("3.1", "Architecture and Deployment", [
                Req("3.1.1", "Describe the platform's deployment architecture, including cloud provider and the degree of tenant isolation.", "Must", 4),
                Req("3.1.2", "Confirm whether a single-tenant or dedicated-infrastructure deployment is available. Alderwood's security team has a stated preference for single-tenant deployment for PII-heavy workloads.", "Must", 4, dupe="single-tenant"),
                Req("3.1.3", "State the regions in which customer data may be hosted. Alderwood requires United States data residency at minimum.", "Must", 5, dupe="residency"),
                Req("3.1.4", "Describe the environment model available to customers, including whether a non-production sandbox is provided and whether it is separately licensed.", "Must", 4),
                Req("3.1.5", "Describe how platform upgrades are delivered, including whether customers may defer a release and what notice is given.", "Should", 3),
                Req("3.1.6", "Describe the change management process for breaking API changes, including the deprecation window offered.", "Must", 4),
                Req("3.1.7", "Describe any dependency on third-party subprocessors within the request path for real-time operations.", "Should", 3),
                Req("3.1.8", "Confirm whether the platform is offered as a customer-managed deployment within Alderwood's own cloud account.", "Nice", 2, dupe="single-tenant"),
                Req("3.1.9", "Describe the platform's multi-region failover architecture and whether failover is automatic.", "Should", 4),
            ]),
            Subsection("3.2", "Scalability and Performance", [
                Req("3.2.1", "State the largest production deployment on the platform today, measured in tracked customer profiles and monthly event volume.", "Must", 4),
                Req("3.2.2", "Confirm the platform can support 2.1 million tracked customer profiles with headroom for 20 percent annual growth.", "Must", 5),
                Req("3.2.3", "State expected peak event throughput supported, and describe behaviour when that ceiling is exceeded.", "Must", 4),
                Req("3.2.4", "Describe platform behaviour during a retail peak event such as the week following American Thanksgiving, when Alderwood's traffic increases approximately fivefold.", "Must", 5),
                Req("3.2.5", "State the published API rate limits and describe whether they can be raised contractually.", "Must", 4),
                Req("3.2.6", "State the p50 and p99 latency for a single profile lookup by identifier.", "Should", 4),
                Req("3.2.7", "Describe how query performance degrades as profile count and event history grow.", "Should", 3),
                Req("3.2.8", "Describe any batch processing windows during which platform functionality is reduced.", "Should", 3),
                Req("3.2.9", "Describe capacity planning support provided ahead of a known traffic peak.", "Nice", 2),
            ]),
            Subsection("3.3", "APIs, SDKs, and Extensibility", [
                Req("3.3.1", "Describe the REST APIs available for profile read and write operations.", "Must", 4),
                Req("3.3.2", "Describe the APIs available for programmatic segment creation and management.", "Should", 4),
                Req("3.3.3", "State whether API documentation is publicly accessible without a customer login, and provide the URL.", "Should", 3),
                Req("3.3.4", "Describe supported single sign-on protocols for administrative console access.", "Must", 4, dupe="sso"),
                Req("3.3.5", "Describe available client SDKs by language and platform, and state which are vendor-maintained.", "Should", 3),
                Req("3.3.6", "Describe webhook capability, including delivery guarantees, retry behaviour, and signature verification.", "Must", 4),
                Req("3.3.7", "Confirm whether a managed connector is available for streaming raw event data into a Kafka topic for downstream consumption by Alderwood's data engineering team.", "Must", 4, dupe="kafka"),
                Req("3.3.8", "Describe support for customer-authored transformation logic executed within the platform.", "Should", 3),
                Req("3.3.9", "List pre-built connectors for e-commerce platforms and state which are vendor-maintained versus partner-maintained.", "Should", 3, dupe="shopify"),
                Req("3.3.10", "Describe the process and typical timeline for building a connector not present in the catalogue.", "Should", 3),
                Req("3.3.11", "Describe API versioning policy, including how long a prior version remains supported.", "Should", 3),
            ]),
            Subsection("3.4", "Data Management", [
                Req("3.4.1", "Describe the data model, including whether the event schema is fixed or customer-defined.", "Must", 4),
                Req("3.4.2", "State any limit on the number of custom attributes that may be defined per customer profile.", "Should", 3, dupe="custom-attrs"),
                Req("3.4.3", "Confirm that Alderwood may export the full contents of its data at any time, and state whether an export fee applies.", "Must", 5, dupe="raw-export"),
                Req("3.4.4", "Describe supported export formats and the mechanism by which an export is initiated.", "Must", 4, dupe="raw-export"),
                Req("3.4.5", "Describe data deletion behaviour on contract termination, including the period after which data is irrecoverably destroyed.", "Must", 5),
                Req("3.4.6", "Describe data lineage capability, specifically the ability to trace a profile attribute back to the source record that produced it.", "Should", 4),
                Req("3.4.7", "Describe data quality monitoring available on ingested data, including detection of schema drift.", "Should", 3),
                Req("3.4.8", "Describe support for backfilling historical data at initial load, and state any volume limits on backfill.", "Must", 4),
                Req("3.4.9", "Describe deduplication of identical events delivered more than once.", "Should", 3),
            ]),
            Subsection("3.5", "Monitoring and Observability", [
                Req("3.5.1", "Describe the operational dashboards available to a customer administrator for monitoring ingestion health.", "Should", 3),
                Req("3.5.2", "Describe alerting available on ingestion failure or pipeline delay, including supported notification channels.", "Must", 4),
                Req("3.5.3", "Confirm the availability of a public status page and state whether historical uptime is published.", "Must", 3),
                Req("3.5.4", "Describe how planned maintenance is communicated and the notice period given.", "Should", 3),
                Req("3.5.5", "Describe whether platform logs can be forwarded to a customer-operated SIEM.", "Should", 4),
                Req("3.5.6", "State the retention period for operational and diagnostic logs.", "Should", 3),
                Req("3.5.7", "Describe support for tracing an individual record through the ingestion pipeline for troubleshooting.", "Should", 3),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 4
    Section(
        "4", "Information Security", "Security",
        intro=(
            "This section follows a standardised security questionnaire "
            "structure. Alderwood's information security team will score this "
            "section independently. A 'Not Supported' response against a Must "
            "requirement in this section is presumptively disqualifying."
        ),
        subsections=[
            Subsection("4.1", "Security Governance and Certification", [
                Req("4.1.1", "List all current security certifications and attestations, including SOC 2, ISO 27001, and PCI DSS, and state the availability of each report.", "Must", 5, dupe="certs"),
                Req("4.1.2", "Confirm whether you hold a current SOC 2 Type II attestation and state the date of the most recent report.", "Must", 5, dupe="certs"),
                Req("4.1.3", "Confirm whether you hold ISO 27001 certification. If certification is in progress, state the expected completion date.", "Must", 4, dupe="iso"),
                Req("4.1.4", "Confirm whether you maintain a documented information security policy reviewed at least annually by executive management.", "Must", 4),
                Req("4.1.5", "State whether you employ a dedicated Chief Information Security Officer or equivalent, and to whom that role reports.", "Should", 3),
                Req("4.1.6", "Describe mandatory security awareness training for employees, including frequency.", "Should", 3),
                Req("4.1.7", "Describe background screening performed on employees with access to customer production data.", "Must", 4),
            ]),
            Subsection("4.2", "Identity and Access Management", [
                Req("4.2.1", "Confirm support for SAML 2.0 single sign-on for platform user authentication.", "Must", 5, dupe="sso"),
                Req("4.2.2", "Confirm support for OpenID Connect as an alternative federation protocol.", "Should", 3, dupe="sso"),
                Req("4.2.3", "Confirm support for multi-factor authentication on platform administrator accounts, and state whether it can be enforced organisation-wide.", "Must", 5, dupe="mfa"),
                Req("4.2.4", "Confirm support for SCIM-based automated user provisioning and deprovisioning.", "Must", 4, dupe="scim"),
                Req("4.2.5", "Describe role-based access control, including whether custom roles may be defined by a customer administrator without vendor involvement.", "Must", 5),
                Req("4.2.6", "Describe whether permissions can be scoped to a subset of customer records, for example restricting a regional manager to loyalty members associated with that region.", "Should", 4),
                Req("4.2.7", "Describe whether access grants can be issued on a time-bound basis that expires without administrator intervention.", "Should", 3),
                Req("4.2.8", "Describe the process governing vendor personnel access to customer production data, including whether customer approval is required.", "Must", 5),
                Req("4.2.9", "Confirm that all administrative actions are captured in an audit log, and state the retention period for that log.", "Must", 4, dupe="audit-log"),
                Req("4.2.10", "Confirm that the audit log is exportable via API for ingestion into a customer-operated SIEM.", "Must", 4, dupe="audit-log"),
                Req("4.2.11", "Describe password policy enforcement for accounts not federated through single sign-on.", "Should", 3),
            ]),
            Subsection("4.3", "Data Protection", [
                Req("4.3.1", "Confirm that customer data is encrypted at rest, and state the cipher and key length used.", "Must", 5, dupe="enc-rest"),
                Req("4.3.2", "Confirm that customer data is encrypted in transit, and state the minimum TLS version enforced on external endpoints.", "Must", 5),
                Req("4.3.3", "Describe encryption key management, including whether keys are unique per tenant and who holds custody.", "Must", 5),
                Req("4.3.4", "Confirm whether customer-managed encryption keys are supported.", "Should", 4),
                Req("4.3.5", "Describe data masking or tokenisation available for sensitive profile attributes.", "Should", 3),
                Req("4.3.6", "Describe controls preventing production customer data from being copied into non-production environments.", "Must", 4),
                Req("4.3.7", "Confirm whether production data is used in testing, and if so under what controls.", "Must", 4),
                Req("4.3.8", "Describe secure media disposal procedures for decommissioned storage hardware.", "Should", 3),
                Req("4.3.9", "Confirm that all storage tiers, including backups and archives, are encrypted at rest.", "Must", 4, dupe="enc-rest"),
            ]),
            Subsection("4.4", "Application Security", [
                Req("4.4.1", "Describe your secure software development lifecycle, including security review gates prior to release.", "Must", 4),
                Req("4.4.2", "Describe your penetration testing programme, including cadence, whether testing is performed by an independent third party, and the availability of results.", "Must", 5, dupe="pentest"),
                Req("4.4.3", "State the date of your most recent third-party penetration test and confirm whether an executive summary can be shared.", "Must", 4, dupe="pentest"),
                Req("4.4.4", "Describe static and dynamic application security testing performed in your build pipeline.", "Should", 4),
                Req("4.4.5", "Describe dependency and container vulnerability scanning, including remediation service levels by severity.", "Must", 4),
                Req("4.4.6", "Confirm whether you operate a vulnerability disclosure programme or bug bounty, and name the platform used.", "Should", 3),
                Req("4.4.7", "Describe your process for notifying customers of a critical vulnerability affecting the platform.", "Must", 4),
                Req("4.4.8", "Describe controls against common web application vulnerabilities, with reference to a recognised framework.", "Should", 3),
            ]),
            Subsection("4.5", "Infrastructure and Network Security", [
                Req("4.5.1", "Describe network segmentation between the platform's public-facing tier and its data tier.", "Must", 4),
                Req("4.5.2", "Describe intrusion detection and prevention controls in the production environment.", "Must", 4),
                Req("4.5.3", "Describe denial of service mitigation for public-facing endpoints.", "Should", 3),
                Req("4.5.4", "Confirm whether IP allow-listing is supported for administrative console access.", "Should", 3),
                Req("4.5.5", "Describe physical security controls at facilities hosting customer data, or name the cloud provider whose controls apply.", "Must", 4),
                Req("4.5.6", "Describe endpoint protection deployed on employee workstations with access to production systems.", "Should", 3),
                Req("4.5.7", "Describe hardening standards applied to production servers and container images.", "Should", 3),
            ]),
            Subsection("4.6", "Incident Response", [
                Req("4.6.1", "Confirm that you maintain a documented incident response plan and state how frequently it is tested.", "Must", 5),
                Req("4.6.2", "State the contractual notification period following confirmation of a security incident affecting customer data.", "Must", 5),
                Req("4.6.3", "Describe the information provided to affected customers during an active incident, and the cadence of updates.", "Must", 4),
                Req("4.6.4", "Confirm whether customers receive a written post-incident report including root cause and corrective actions.", "Must", 4),
                Req("4.6.5", "Disclose any security incident affecting customer data in the last 36 months, including its resolution.", "Must", 5),
                Req("4.6.6", "Describe forensic support available to a customer following an incident.", "Should", 3),
            ]),
            Subsection("4.7", "Business Continuity and Disaster Recovery", [
                Req("4.7.1", "State your Recovery Point Objective for the production environment.", "Must", 5, dupe="rpo-rto"),
                Req("4.7.2", "State your Recovery Time Objective for the production environment.", "Must", 5, dupe="rpo-rto"),
                Req("4.7.3", "Describe backup frequency and backup retention period.", "Must", 4),
                Req("4.7.4", "Confirm how frequently backup restoration is tested, and state the date of the most recent successful restoration test.", "Must", 4),
                Req("4.7.5", "Describe the redundancy model within a hosting region.", "Should", 4),
                Req("4.7.6", "Confirm whether a business continuity plan is maintained and tested at least annually.", "Must", 4),
            ]),
            Subsection("4.8", "Third-Party and Supply Chain Risk", [
                Req("4.8.1", "Provide a current list of subprocessors with access to customer data, including the purpose of each.", "Must", 5),
                Req("4.8.2", "State the notice period given to customers before a new subprocessor is engaged, and whether customers may object.", "Must", 4),
                Req("4.8.3", "Describe security due diligence performed on subprocessors prior to engagement.", "Must", 4),
                Req("4.8.4", "Confirm whether you carry cyber liability insurance, and state the coverage limit.", "Must", 4),
                Req("4.8.5", "Describe controls governing use of generative AI tooling by your engineering staff on customer data or customer-derived code.", "Should", 3),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 5
    Section(
        "5", "Privacy and Regulatory Compliance", "Privacy",
        intro=(
            "Alderwood operates a loyalty programme covering 2.1 million "
            "members and captures transaction data from 22 in-store pharmacy "
            "counters. Responses in this section will be reviewed by "
            "Alderwood's legal and compliance functions."
        ),
        subsections=[
            Subsection("5.1", "Regulatory Compliance", [
                Req("5.1.1", "Confirm compliance with the California Consumer Privacy Act as amended, including support for consumer access and deletion requests.", "Must", 5),
                Req("5.1.2", "Confirm compliance with the General Data Protection Regulation and the availability of a Data Processing Agreement.", "Must", 4),
                Req("5.1.3", "Confirm compliance with applicable Washington State health data legislation as it applies to consumer health data collected outside a clinical setting.", "Must", 5),
                Req("5.1.4", "Alderwood's loyalty programme captures purchase data originating from 22 in-store pharmacy counters. Confirm whether your platform is HIPAA compliant and whether you will execute a Business Associate Agreement.", "Must", 5, dupe="hipaa"),
                Req("5.1.5", "Describe how the platform supports segregation of health-adjacent purchase data from general loyalty data.", "Must", 4, dupe="hipaa"),
                Req("5.1.6", "Confirm whether you will execute Alderwood's standard Data Processing Addendum, or state your required exceptions.", "Must", 4),
                Req("5.1.7", "State the default and maximum configurable data retention period, and confirm retention can be set per data category.", "Must", 4, dupe="retention"),
                Req("5.1.8", "Describe your policy on using customer data to train machine learning models, including whether customers may opt out.", "Must", 5),
            ]),
            Subsection("5.2", "Data Subject Rights", [
                Req("5.2.1", "Describe the mechanism by which a consumer access request is fulfilled, including whether it can be initiated via API.", "Must", 5),
                Req("5.2.2", "Describe the mechanism by which a consumer deletion request is fulfilled across all storage tiers including backups.", "Must", 5),
                Req("5.2.3", "State the maximum elapsed time between a deletion request and irrecoverable deletion of the record.", "Must", 4),
                Req("5.2.4", "Describe how a deletion request propagates to downstream destinations to which the profile was previously activated.", "Must", 5),
                Req("5.2.5", "Describe support for data portability, providing a consumer's data in a machine-readable format.", "Should", 3),
                Req("5.2.6", "Describe the audit record retained to evidence fulfilment of a data subject request.", "Must", 4),
                Req("5.2.7", "Describe handling of a deletion request for a profile that is a member of an active segment.", "Should", 3),
            ]),
            Subsection("5.3", "Data Residency and Cross-Border Transfer", [
                Req("5.3.1", "State all regions in which customer data may be stored at rest.", "Must", 5, dupe="residency"),
                Req("5.3.2", "Confirm that Alderwood's data can be stored exclusively within the United States.", "Must", 5, dupe="residency"),
                Req("5.3.3", "Alderwood anticipates expanding operations into Canada within 18 months. Confirm whether customer data can be hosted so as to meet Canadian data residency expectations.", "Must", 4, dupe="canada"),
                Req("5.3.4", "Describe whether support and engineering personnel outside the storage region may access customer data, and under what controls.", "Must", 4),
                Req("5.3.5", "Describe the legal transfer mechanism relied upon for any cross-border transfer of personal data.", "Should", 3),
                Req("5.3.6", "Confirm whether data may be processed, as distinct from stored, outside the elected region.", "Must", 4),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 6
    Section(
        "6", "Implementation and Professional Services", "Implementation",
        subsections=[
            Subsection("6.1", "Implementation Approach", [
                Req("6.1.1", "Describe your implementation methodology and typical project phases.", "Must", 4),
                Req("6.1.2", "State the typical elapsed time to first production value for a customer of Alderwood's size and source complexity.", "Must", 5, dupe="timeline"),
                Req("6.1.3", "Provide an indicative project plan for a deployment covering web, mobile, point-of-sale, and loyalty data sources.", "Must", 4),
                Req("6.1.4", "State the Alderwood resources and roles you expect to be committed during implementation, and the approximate time commitment of each.", "Must", 4),
                Req("6.1.5", "Describe how historical data migration is handled at initial load.", "Must", 4),
                Req("6.1.6", "Describe your approach to validating that migrated data is complete and accurate.", "Must", 4),
                Req("6.1.7", "Describe the acceptance criteria you propose for implementation sign-off.", "Should", 3),
            ]),
            Subsection("6.2", "Services and Enablement", [
                Req("6.2.1", "State which professional services are included in the subscription and which are billed separately.", "Must", 4),
                Req("6.2.2", "State your standard professional services rates by role.", "Must", 3),
                Req("6.2.3", "Describe training provided for administrators and for business users, and state whether it is included.", "Must", 3),
                Req("6.2.4", "Describe available certification programmes for customer staff.", "Nice", 2),
                Req("6.2.5", "Confirm whether implementation may be delivered by a third-party systems integrator, and name any certified partners in North America.", "Should", 3),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 7
    Section(
        "7", "Support and Service Levels", "Support",
        subsections=[
            Subsection("7.1", "Service Level Commitments", [
                Req("7.1.1", "State the uptime service level commitment offered, and confirm whether it is contractual.", "Must", 5),
                Req("7.1.2", "State the remedy available in the event of a service level breach, including the service credit schedule.", "Must", 4),
                Req("7.1.3", "State how uptime is measured and confirm whether the measurement is independently verifiable.", "Must", 4),
                Req("7.1.4", "State what is excluded from the uptime calculation, including planned maintenance.", "Must", 4),
                Req("7.1.5", "State whether a data freshness or processing latency service level is offered in addition to uptime.", "Should", 4),
            ]),
            Subsection("7.2", "Support Model", [
                Req("7.2.1", "State support response time commitments by severity level for the tier proposed in this response.", "Must", 5),
                Req("7.2.2", "Confirm whether 24-hour support is available every day of the year, and state through which channels.", "Must", 5),
                Req("7.2.3", "State the geographic locations from which support is delivered.", "Should", 3),
                Req("7.2.4", "Confirm whether a named Technical Account Manager or Customer Success Manager is assigned, and state whether that is included in the proposed tier.", "Must", 4),
                Req("7.2.5", "Describe the escalation path available when a severity one issue is not progressing.", "Must", 4),
                Req("7.2.6", "Describe the support ticketing system provided and whether it integrates with a customer-operated service desk.", "Should", 3),
                Req("7.2.7", "State your published support hours and confirm coverage of Alderwood's peak retail trading period.", "Must", 4),
            ]),
        ],
    ),

    # ------------------------------------------------------------------ 8
    Section(
        "8", "Commercial Terms and Corporate Responsibility", "Commercial",
        subsections=[
            Subsection("8.1", "Pricing and Commercial Structure", [
                Req("8.1.1", "Provide pricing for a deployment covering approximately 2.1 million tracked customer profiles, including any volume discount structure.", "Must", 5, dupe="pricing"),
                Req("8.1.2", "State your overage billing policy in the event tracked profile volume exceeds the contracted tier mid-term.", "Must", 4, dupe="pricing"),
                Req("8.1.3", "State your pricing metric and confirm whether it is based on tracked profiles, events, or another unit.", "Must", 4),
                Req("8.1.4", "State your standard annual uplift on renewal and confirm whether it can be capped contractually.", "Must", 4),
                Req("8.1.5", "Confirm whether multi-year pricing is available and state the discount offered for a three-year commitment.", "Should", 3),
                Req("8.1.6", "State your standard payment terms and confirm whether annual invoicing in advance is required.", "Should", 3),
                Req("8.1.7", "Confirm whether a non-production sandbox environment is separately chargeable.", "Should", 3),
            ]),
            Subsection("8.2", "Contractual Terms", [
                Req("8.2.1", "State your standard contract term and any minimum commitment.", "Must", 4),
                Req("8.2.2", "Describe termination rights available to the customer, including termination for convenience.", "Must", 4),
                Req("8.2.3", "State your limitation of liability and confirm whether it can be raised for data protection breaches.", "Must", 5),
            ]),
            Subsection("8.3", "Corporate Responsibility", [
                Req("8.3.1", "Describe your environmental sustainability programme, including any data centre carbon footprint commitments, offset purchases, or published emissions reporting.", "Should", 2, dupe="sustainability"),
                Req("8.3.2", "State whether you publish a modern slavery or supply chain transparency statement, and provide the URL.", "Nice", 1),
                Req("8.3.3", "Describe your supplier diversity programme, if any.", "Nice", 1),
            ]),
        ],
    ),
]


def all_requirements() -> list[Req]:
    return [
        req
        for section in SECTIONS
        for sub in section.subsections
        for req in sub.items
    ]


def dupe_clusters() -> dict[str, list[str]]:
    """Near-duplicate clusters, keyed by tag -> requirement ids."""
    clusters: dict[str, list[str]] = {}
    for req in all_requirements():
        if req.dupe:
            clusters.setdefault(req.dupe, []).append(req.rid)
    return {tag: rids for tag, rids in clusters.items() if len(rids) > 1}
