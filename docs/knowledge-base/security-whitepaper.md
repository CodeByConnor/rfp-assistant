# Meridian — Security & Compliance Whitepaper

*Doc type: public | Last updated: 2026-04-15*

## Security governance

- Documented information security policy, reviewed and approved annually by
  the executive team. Last review February 2026.
- A dedicated Chief Information Security Officer reports directly to the CEO.
- Mandatory security awareness training at onboarding and annually
  thereafter, with phishing simulation quarterly.
- Background screening (criminal record, employment, education) for all
  employees with access to customer production data, subject to local law.

## Certifications and attestations

- **SOC 2 Type II**: attained March 2023, renewed annually. Most recent
  report covers 1 January 2025 to 31 December 2025. Available under NDA.
- **ISO 27001**: certification audit in progress, targeting Q1 2027.
  **Not yet certified.**
- **PCI DSS**: Meridian does not store, process, or transmit payment card
  data and is out of scope.
- **HIPAA**: Meridian is **not** HIPAA compliant and **does not execute
  Business Associate Agreements**. Customers must not submit protected health
  information. Meridian provides no mechanism to segregate health-adjacent
  data from general data.

## Identity and access management

- **SSO**: SAML 2.0 and OpenID Connect, available on all paid tiers.
- **MFA**: TOTP-based, available on all accounts, enforceable
  organisation-wide by an administrator.
- **SCIM provisioning**: available in **beta** on Enterprise tier only.
  Not generally available; no committed GA date beyond the roadmap target.
- **RBAC**: predefined roles (Admin, Analyst, Data Steward, Viewer). Custom
  roles are definable by a customer administrator without vendor involvement
  on Enterprise tier only.
- **Record-level scoping**: permissions can be scoped to a subset of profiles
  by attribute filter, for example restricting a regional manager to profiles
  associated with that region.
- **Time-bound access**: grants can be issued with an expiry, after which
  access is revoked automatically.
- **Vendor access to customer data**: Meridian support and engineering
  personnel cannot access customer production data without a customer-approved,
  time-boxed access grant raised through the console. All such access is
  logged and reported to the customer monthly.
- **Audit logging**: all administrative actions and data access events are
  logged, retained 12 months, and exportable via API for ingestion into a
  customer-operated SIEM.
- Password policy for non-federated accounts: 12-character minimum,
  complexity enforced, breach-corpus checked, 90-day rotation optional.

## Data protection

- **At rest**: AES-256, with per-tenant keys managed in AWS KMS. All storage
  tiers including backups and archives are encrypted.
- **In transit**: TLS 1.2 minimum on all external endpoints; TLS 1.3
  preferred.
- **Key custody**: keys are unique per tenant and held by Meridian in AWS
  KMS. **Customer-managed encryption keys (BYOK) are not supported.**
- **Masking**: attributes may be marked sensitive, which masks them in the
  console for users lacking the Data Steward role.
- Production data is never copied into non-production environments.
  Non-production environments are seeded with synthetic data only.
- Media disposal follows NIST SP 800-88 guidance; storage is
  cryptographically erased on decommission by the cloud provider.

## Application security

- Secure SDLC with mandatory peer review, and a security review gate for any
  change touching authentication, authorisation, or data export.
- **Penetration testing**: annual third-party penetration test. Most recent
  test completed November 2025 by an independent security firm. Executive
  summary available under NDA.
- SAST and dependency scanning on every build; DAST against staging weekly.
- Container and dependency vulnerability remediation targets: critical 7
  days, high 30 days, medium 90 days.
- Public vulnerability disclosure programme and bug bounty via HackerOne.
- Customers are notified of a critical vulnerability affecting the platform
  within 5 business days of remediation, or immediately where customer action
  is required.
- Controls are mapped to the OWASP Application Security Verification
  Standard, level 2.

## Infrastructure and network security

- Network segmentation between public-facing, application, and data tiers,
  with no direct public route to the data tier.
- Intrusion detection via AWS GuardDuty with 24/7 alerting to an on-call
  security engineer.
- DDoS mitigation via AWS Shield Advanced.
- **IP allow-listing for administrative console access is supported on
  Enterprise tier.**
- Physical security is inherited from AWS; Meridian operates no data centres
  of its own.
- Managed endpoint detection and response on all employee workstations with
  production access; full-disk encryption enforced.
- Server and container images are hardened to CIS Benchmark level 1 and
  rebuilt weekly from a patched base image.

## Incident response

- Documented incident response plan, tested by tabletop exercise twice
  annually. Last exercise January 2026.
- **Contractual notification within 48 hours** of confirming a security
  incident affecting customer data.
- During an active incident, affected customers receive an initial
  notification, then updates at least every 12 hours until resolution.
- A written post-incident report including root cause and corrective actions
  is provided within 10 business days of resolution.
- **Incident disclosure**: Meridian has experienced no security incident
  resulting in unauthorised access to customer data in the last 36 months.
  One availability incident occurred in August 2025 (a 4-hour partial
  ingestion outage caused by a misapplied configuration change); no data was
  exposed.
- Forensic support: Meridian provides relevant logs and engineering support
  to a customer's own forensic process at no charge.

## Business continuity and disaster recovery

- **RPO: 24 hours. RTO: 4 hours.**
- Daily automated backups, retained 30 days.
- Backup restoration tested quarterly. Most recent successful restoration
  test March 2026.
- Multi-AZ deployment within each region.
- **Cross-region failover is not automatic.** Recovery into a second region
  is a manual, vendor-initiated procedure and is not covered by the stated
  RTO.
- Business continuity plan maintained and tested annually.

## Third-party and supply chain

- Current subprocessor list is published at the Meridian trust centre and
  covers cloud infrastructure, email delivery, monitoring, and support
  tooling.
- **30 days' notice** before engaging a new subprocessor. Customers may
  object; an unresolved objection gives the customer a right to terminate
  without penalty.
- Security due diligence (questionnaire, certification review, and where
  applicable penetration test summary) is performed before engaging any
  subprocessor with access to customer data.
- **Cyber liability insurance: 10 million USD limit.** Professional liability
  5 million USD. Certificates available on request.
- Generative AI tooling: engineering staff may use approved AI coding
  assistants configured to exclude customer data and to disable training on
  submitted content. Customer production data may never be submitted to any
  third-party AI service.
