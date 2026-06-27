# Integration Guide - Third-Party Systems & API Reference

## Overview
This guide covers the setup, configuration, and troubleshooting of integrations between the XLVentures HR Platform and common enterprise systems.

## Supported Integrations

### Enterprise Resource Planning (ERP)
- **SAP SuccessFactors**: Full bidirectional sync for employee data, org hierarchy, and payroll records.
- **Oracle HCM Cloud**: Employee lifecycle events and compensation data sync.
- **Workday**: Core HR data, benefits enrollment, and time tracking integration.

### Payroll Systems
- **ADP Workforce Now**: Payroll batch processing, tax document generation.
- **Paychex Flex**: Employee pay records and deductions sync.

### Identity Providers
- **Azure Active Directory**: SSO via SAML 2.0, automated user provisioning via SCIM.
- **Okta**: SSO and lifecycle management with real-time deprovisioning.
- **Google Workspace**: OAuth 2.0 authentication and directory sync.

## SAP Integration - Detailed Troubleshooting

### Sync Failures During Payroll Batch Processing
- **Symptom**: Sync jobs fail or timeout during peak payroll windows.
- **Root Cause**: API rate limits enforced at 1,000 requests per 15-minute window. Large batches exceed this.
- **Resolution**: Schedule payroll sync outside peak hours (before 7 AM or after 7 PM). For 500+ employees, request rate limit increase. Break batches into groups of 200 records.

### Intermittent Data Sync Delays
- **Symptom**: Employee changes take 12-24 hours instead of 4-hour window.
- **Root Cause**: OAuth tokens expire every 90 days. Without rotation, system falls back to slower polling.
- **Resolution**: Verify API credentials quarterly. Enable "Auto-Refresh Token" option (Growth/Enterprise plans).

## API Rate Limits

| Plan | Rate Limit | Burst Limit | Recommended Batch Size |
|---|---|---|---|
| Starter | 500 req/15 min | 50 req/sec | 100 records |
| Growth | 1,000 req/15 min | 100 req/sec | 250 records |
| Enterprise | 5,000 req/15 min | 250 req/sec | 1,000 records |

## Best Practices
- Use pagination for exports exceeding 500 records.
- Implement exponential backoff on 429 responses.
- Cache reference data (departments, locations, job codes) locally.
- Monitor via Integration Dashboard (Settings > Integrations > Health Monitor).