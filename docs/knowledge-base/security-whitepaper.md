# Meridian — Security & Compliance Whitepaper

*Doc type: public | Last updated: 2026-04-15*

## Certifications

- **SOC 2 Type II**: attained March 2023, renewed annually. Report available
  under NDA upon request.
- **ISO 27001**: certification audit in progress, expected completion Q1 2027.
  Not yet certified.
- **PCI DSS**: Meridian does not store or process payment card data and is
  out of scope for PCI DSS.

## Encryption

- Data at rest: AES-256, per-tenant encryption keys managed via AWS KMS.
- Data in transit: TLS 1.2 or higher enforced on all external endpoints.

## Authentication & access control

- **SSO**: SAML 2.0 and OpenID Connect (OIDC) supported for all paid tiers.
- **SCIM provisioning**: available in **beta** for Enterprise tier customers;
  not yet generally available.
- **RBAC**: role-based access control with predefined roles (Admin, Analyst,
  Viewer) and custom role support on Enterprise tier.
- **Audit logs**: all admin actions and data access events are logged and
  retained for 12 months, exportable via API.

## Penetration testing & vulnerability management

- Annual third-party penetration test performed by an independent security
  firm. Executive summary available under NDA.
- Continuous automated vulnerability scanning of infrastructure and
  dependencies.
- Public bug bounty program via HackerOne.

## Data privacy & compliance

- GDPR compliant; Data Processing Agreement (DPA) available for all
  customers processing EU personal data.
- CCPA compliant; supports consumer data deletion and access requests via
  API and admin console.
- **HIPAA**: Meridian is not HIPAA compliant and does not sign Business
  Associate Agreements (BAAs). Customers should not submit protected health
  information (PHI) to Meridian.

## Backup & disaster recovery

- Daily automated backups, retained for 30 days.
- Recovery Point Objective (RPO): 24 hours.
- Recovery Time Objective (RTO): 4 hours.
- Multi-AZ deployment within each supported region for infrastructure
  redundancy.
