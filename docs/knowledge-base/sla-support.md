# Meridian — SLA & Support

*Doc type: public | Last updated: 2026-03-01*

## Uptime commitment

| Tier | Uptime SLA | Contractual | Service credit |
|---|---|---|---|
| Standard | 99.5% | No — target only | None |
| Growth | 99.5% | Yes | 5% of monthly fee per 0.5% below target |
| Enterprise | 99.9% | Yes | 10% of monthly fee per 0.1% below target, capped at 30% |

- Uptime is measured as successful responses to the platform health endpoint,
  sampled at one-minute intervals from three external locations, aggregated
  monthly.
- Measurement is published on the public status page and is independently
  verifiable against it.
- **Excluded from the calculation**: announced planned maintenance, customer-caused
  incidents, force majeure, and degradation attributable to a third-party
  destination system.
- **Data freshness SLA**: Enterprise customers may contract a 95th-percentile
  ingestion-to-availability latency of 5 minutes. This is offered in addition
  to the uptime SLA and carries its own credit schedule.

## Support response targets

| Tier | P1 Critical | P2 High | P3 Normal |
|---|---|---|---|
| Standard | Next business day | 2 business days | 5 business days |
| Growth | 4 hours | 1 business day | 3 business days |
| Enterprise | 1 hour, 24/7/365 | 4 hours | 1 business day |

## Support model

- **Standard / Growth**: email and in-app chat, Mon–Fri 08:00–18:00 US
  Eastern.
- **Enterprise**: 24/7/365 phone, email, and chat.
- Support is delivered from Seattle (US) and Dublin (Ireland). Follow-the-sun
  coverage is provided by these two locations only.
- **Named Technical Account Manager** included on Enterprise tier. A Customer
  Success Manager is assigned on Growth and Enterprise. Standard tier has no
  named contact.
- **Escalation**: a P1 not progressing within 2 hours escalates to the
  Support Director, and at 4 hours to the VP of Engineering. Enterprise
  customers may invoke escalation directly through their TAM.
- Ticketing is through the Meridian support portal. A bidirectional
  ServiceNow and Jira Service Management integration is available for
  Enterprise customers.
- Peak retail trading periods are covered by standard 24/7 Enterprise
  support; Meridian additionally operates a change freeze from 15 November to
  2 January.

## Onboarding

- Standard/Growth: self-serve onboarding, guided documentation, onboarding
  webinars.
- Enterprise: dedicated CSM plus an implementation specialist for the first
  90 days. See `implementation-services.md`.
