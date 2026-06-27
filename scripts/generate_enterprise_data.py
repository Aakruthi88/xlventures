"""
Enterprise Synthetic Data Generation Pipeline
==============================================
Generates realistic, cross-referenced synthetic data for the
Intelligent Next Best Action Platform (Customer Success domain).

Usage:
    python scripts/generate_enterprise_data.py

Generates:
    data/customers.csv
    data/usage.csv
    data/crm.json
    data/support_tickets.csv
    data/recommendation_history.json
    data/meeting_transcripts/*.txt
    data/knowledge_base/*.md
"""

import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
TRANSCRIPTS_DIR = BASE_DIR / "meeting_transcripts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"

TODAY = datetime.now().date()
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# CSM team names
CSM_NAMES = [
    "Sarah Mitchell", "James Rodriguez", "Emily Watson",
    "David Chen", "Priya Kapoor", "Michael Torres"
]

# ============================================================
# CUSTOMER PROFILES - Archetype-driven design
# ============================================================
# Each customer is an intentional archetype, not random data.
# This ensures the AI agents have meaningful patterns to discover.

CUSTOMER_PROFILES = [
    # 🔴 CRISIS - High risk, renewal imminent, low adoption
    {
        "CustomerID": "C001", "Company": "ABC Manufacturing",
        "Plan": "Growth", "Industry": "Manufacturing",
        "RenewalDays": 20, "HealthScore": 42,
        "LicensedUsers": 500, "ActiveUsers": 160,
        "DashboardUsagePct": 32, "APICalls": 15000,
        "TicketsOpen": 7, "Owner": "Sarah Mitchell",
        "LastMeetingDaysAgo": 43, "LastLoginDaysAgo": 7,
        "Notes": "Q1 QBR postponed twice by client. Champion (VP of HR, Priya Sharma) left in April. New VP not responding to outreach. Account at high risk.",
        "Archetype": "crisis"
    },
    {
        "CustomerID": "C002", "Company": "Pinnacle Healthcare",
        "Plan": "Enterprise", "Industry": "Healthcare",
        "RenewalDays": 12, "HealthScore": 28,
        "LicensedUsers": 1200, "ActiveUsers": 340,
        "DashboardUsagePct": 18, "APICalls": 52000,
        "TicketsOpen": 9, "Owner": "James Rodriguez",
        "LastMeetingDaysAgo": 60, "LastLoginDaysAgo": 12,
        "Notes": "Multiple critical tickets unresolved 3+ weeks. HIPAA compliance concerns raised. CFO mentioned budget review in Q3. Last QBR cancelled by client.",
        "Archetype": "crisis"
    },
    # 🟡 SILENT CHURN - Looks okay, subtle red flags
    {
        "CustomerID": "C003", "Company": "NovaTech Solutions",
        "Plan": "Growth", "Industry": "Finance",
        "RenewalDays": 45, "HealthScore": 55,
        "LicensedUsers": 300, "ActiveUsers": 175,
        "DashboardUsagePct": 41, "APICalls": 22000,
        "TicketsOpen": 3, "Owner": "Sarah Mitchell",
        "LastMeetingDaysAgo": 17, "LastLoginDaysAgo": 14,
        "Notes": "Was daily active until mid-May - usage dropped sharply. Engineering team restructured, new CTO started June 1. No complaints but engagement fading.",
        "Archetype": "silent_churn"
    },
    {
        "CustomerID": "C004", "Company": "GreenLeaf Retail",
        "Plan": "Starter", "Industry": "Retail",
        "RenewalDays": 38, "HealthScore": 48,
        "LicensedUsers": 120, "ActiveUsers": 52,
        "DashboardUsagePct": 35, "APICalls": 4800,
        "TicketsOpen": 2, "Owner": "David Chen",
        "LastMeetingDaysAgo": 22, "LastLoginDaysAgo": 5,
        "Notes": "Seasonal business - Q3 is slow period. Mentioned exploring competitor PeopleForce during last check-in. Using only basic features.",
        "Archetype": "silent_churn"
    },
    # 🟢 EXPANSION READY - Healthy, outgrowing current plan
    {
        "CustomerID": "C005", "Company": "Meridian Logistics",
        "Plan": "Starter", "Industry": "Technology",
        "RenewalDays": 52, "HealthScore": 78,
        "LicensedUsers": 80, "ActiveUsers": 73,
        "DashboardUsagePct": 82, "APICalls": 8500,
        "TicketsOpen": 0, "Owner": "Emily Watson",
        "LastMeetingDaysAgo": 3, "LastLoginDaysAgo": 0,
        "Notes": "Extremely engaged. Opening 2 new distribution centers in Q3 - 150+ new employees. Asked about Enterprise features and API rate limits. Strong upsell candidate.",
        "Archetype": "expansion"
    },
    {
        "CustomerID": "C006", "Company": "Atlas Finserv",
        "Plan": "Growth", "Industry": "Finance",
        "RenewalDays": 35, "HealthScore": 82,
        "LicensedUsers": 400, "ActiveUsers": 362,
        "DashboardUsagePct": 76, "APICalls": 45000,
        "TicketsOpen": 1, "Owner": "Emily Watson",
        "LastMeetingDaysAgo": 7, "LastLoginDaysAgo": 1,
        "Notes": "Power user team. Compliance team loves audit trail. Asked about advanced analytics module. Growth plan may be limiting API usage soon.",
        "Archetype": "expansion"
    },
    # 🔵 HEALTHY CHAMPION - Model customers, no false alarms
    {
        "CustomerID": "C007", "Company": "Orion Enterprises",
        "Plan": "Enterprise", "Industry": "Manufacturing",
        "RenewalDays": 55, "HealthScore": 91,
        "LicensedUsers": 2000, "ActiveUsers": 1920,
        "DashboardUsagePct": 91, "APICalls": 125000,
        "TicketsOpen": 0, "Owner": "James Rodriguez",
        "LastMeetingDaysAgo": 9, "LastLoginDaysAgo": 0,
        "Notes": "Model customer. 96% seat utilization. Renewed early last cycle with 2-year commitment. Potential case study and referral candidate.",
        "Archetype": "healthy"
    },
    {
        "CustomerID": "C008", "Company": "Vanguard Media",
        "Plan": "Enterprise", "Industry": "Technology",
        "RenewalDays": 48, "HealthScore": 88,
        "LicensedUsers": 1500, "ActiveUsers": 1380,
        "DashboardUsagePct": 87, "APICalls": 98000,
        "TicketsOpen": 0, "Owner": "David Chen",
        "LastMeetingDaysAgo": 5, "LastLoginDaysAgo": 1,
        "Notes": "Creative team uses dashboards extensively for workforce analytics. Recently featured platform in industry blog. Happy customer - nurture relationship.",
        "Archetype": "healthy"
    },
    # ⚪ NEW ONBOARDING - Recently joined, needs guidance not alerts
    {
        "CustomerID": "C009", "Company": "FreshHire Staffing",
        "Plan": "Starter", "Industry": "Technology",
        "RenewalDays": 58, "HealthScore": 35,
        "LicensedUsers": 60, "ActiveUsers": 14,
        "DashboardUsagePct": 15, "APICalls": 1200,
        "TicketsOpen": 2, "Owner": "Sarah Mitchell",
        "LastMeetingDaysAgo": 11, "LastLoginDaysAgo": 2,
        "Notes": "Onboarded 3 weeks ago. Still in implementation phase. IT team setting up SSO and bulk user import. Normal new-customer ramp-up trajectory.",
        "Archetype": "new_onboarding"
    },
    {
        "CustomerID": "C010", "Company": "BrightPath Education",
        "Plan": "Growth", "Industry": "Healthcare",
        "RenewalDays": 42, "HealthScore": 40,
        "LicensedUsers": 250, "ActiveUsers": 58,
        "DashboardUsagePct": 22, "APICalls": 5600,
        "TicketsOpen": 2, "Owner": "David Chen",
        "LastMeetingDaysAgo": 8, "LastLoginDaysAgo": 4,
        "Notes": "Onboarded 2 weeks ago. University HR team - academic calendar impacts adoption. Requested training materials for department heads. Needs guided onboarding.",
        "Archetype": "new_onboarding"
    }
]


# ============================================================
# SUPPORT TICKET TEMPLATES - Realistic HR SaaS issues
# ============================================================

TICKET_TEMPLATES = {
    "crisis": [
        ("SAP integration sync failing intermittently during payroll batch", "High"),
        ("Dashboard analytics not loading for newly onboarded team members", "Medium"),
        ("API rate limit errors during peak payroll processing hours", "High"),
        ("Request for custom compliance report template for audit", "Low"),
        ("Employee data sync delay between HRIS and platform exceeding 24 hours", "High"),
        ("Bulk user import timing out for batches above 300 records", "High"),
        ("Role-based access control not reflecting updated org hierarchy", "Medium"),
        ("SSO login failures affecting shift-based staff", "Critical"),
        ("HIPAA audit log export missing timestamps on bulk operations", "Critical"),
        ("Mobile app crash when accessing patient-staff scheduling", "Medium"),
        ("Data export to EHR system returning incomplete records", "Critical"),
        ("Password reset emails delayed 30+ minutes for admin accounts", "Medium"),
    ],
    "silent_churn": [
        ("Custom workflow automation triggers not firing on status change", "Medium"),
        ("Report generation timeout on datasets exceeding 10k records", "Medium"),
        ("API webhook delivery intermittent failures to Slack integration", "Low"),
        ("Seasonal employee bulk onboarding template formatting errors", "Medium"),
        ("Shift scheduling module not syncing with Google Calendar", "Low"),
    ],
    "expansion": [
        ("Feature request: advanced audit trail filtering by department", "Low"),
    ],
    "new_onboarding": [
        ("SSO configuration error during initial Azure AD setup", "Medium"),
        ("Bulk employee CSV import column mapping not saving correctly", "Medium"),
        ("Custom role creation wizard unclear for department head permissions", "Low"),
        ("Training module video playback buffering on campus network", "Low"),
    ],
    "healthy": []
}


# ============================================================
# MEETING TRANSCRIPT TEMPLATES
# ============================================================

TRANSCRIPT_TEMPLATES = {
    "abc_manufacturing": """Meeting Transcript - ABC Manufacturing
Date: {meeting_date}
Attendees: Rajesh Kapoor (HR Director, ABC Manufacturing), Sarah Mitchell (CSM, XLVentures)
Duration: 28 minutes

Sarah: Hi Rajesh, thanks for making time today. I know it's been a while since we last connected - how are things going on your end?

Rajesh: Yeah, hi Sarah. Honestly? It's been a rough couple of months. Since Priya left in April, there's been kind of a leadership vacuum around the HR tech stack. Nobody's really championing the platform internally anymore, and I've been stretched thin trying to cover her responsibilities on top of mine.

Sarah: I'm sorry to hear about Priya's departure. She was definitely a strong advocate for the platform. How's the rest of the team adapting?

Rajesh: Not great, if I'm being honest. The SAP integration has been painfully slow - like, my team spends probably 20 minutes every morning just waiting for the payroll sync to complete. We've raised tickets about it but nothing's really changed. And the dashboards? Most of my team has just stopped using them altogether. They export everything to Excel because the analytics take forever to load, especially for the newer hires who were never properly trained on it.

Sarah: That's concerning. Are they using the self-service reporting features at all?

Rajesh: Barely. Look, I'll be straight with you - our renewal is coming up in about three weeks and I've been asked by my VP to evaluate two other vendors before we commit. I need to show tangible ROI, and right now the numbers aren't there. We're paying for 500 seats and I think maybe 160 people actually log in regularly. That's not a conversation I want to have with finance.

Sarah: I appreciate you being upfront about that. What would need to change for you to feel confident about renewing?

Rajesh: Honestly, three things. Fix the SAP integration - that's non-negotiable. Get someone to actually train my team on the dashboards and analytics, because the adoption is embarrassing. And I need some kind of compliance reporting template for our manufacturing audit that's coming up in September. If we can't get those sorted, I don't see how I justify the spend. Management is already looking at competitors like BambooHR and Workday - and frankly, their demos looked pretty slick.

Sarah: Those are all actionable items. Let me take these back to the team and get you a concrete plan by end of week.

Rajesh: I appreciate that, Sarah. But I need it fast - we don't have a lot of runway here.""",

    "meridian_logistics": """Meeting Transcript - Meridian Logistics
Date: {meeting_date}
Attendees: Anita Desai (COO, Meridian Logistics), Emily Watson (CSM, XLVentures)
Duration: 22 minutes

Emily: Anita, great to see you again! How's everything going at Meridian?

Anita: Emily, honestly, things are going really well. Your platform has completely transformed how we handle onboarding at our main distribution center. What used to take us three weeks per batch of new hires is now down to about four days. The HR team loves it.

Emily: That's amazing to hear! I saw your usage numbers - 91% seat activation. That's one of the highest in our entire customer base.

Anita: Yeah, the team's really adopted it. Actually, that's partly why I wanted to chat. We're opening two new distribution centers next quarter - one in Chennai and one in Hyderabad. That's roughly 150 new employees we'll need to onboard, and we'd love to replicate what we've done at the Bangalore center.

Emily: That's exciting! Your current Starter plan supports up to 80 seats. You'd definitely need to scale up for that kind of growth.

Anita: Right, exactly. So I wanted to understand what the Growth or Enterprise options look like. We're especially interested in the advanced analytics module - our operations team has been asking for workforce productivity dashboards, and right now we're kind of jury-rigging things with the basic reports. Also, we'd love better API access. Our warehouse management system is custom-built and we want to push employee scheduling data directly into your platform.

Emily: Both of those are included in the Growth plan, and Enterprise gives you unlimited API calls plus custom integrations support. I can put together a comparison for you.

Anita: That would be great. And honestly? Budget isn't really the constraint here - our CEO is fully behind this expansion. We just need to make sure the migration to a higher plan is smooth and doesn't disrupt the existing workflows. Can we do a phased rollout?

Emily: Absolutely. We actually have a dedicated migration team for exactly that. Let me loop them in and we can set up a planning session.

Anita: Perfect. Let's aim for next week if possible - we want to have everything in place before the new centers go live in September.""",

    "novatech_solutions": """Meeting Transcript - NovaTech Solutions
Date: {meeting_date}
Attendees: Mark Fernandez (VP Engineering, NovaTech Solutions), Sarah Mitchell (CSM, XLVentures)
Duration: 18 minutes

Sarah: Hey Mark, thanks for jumping on. I noticed your team's usage has dipped a bit over the past few weeks - just wanted to check in and see how things are going.

Mark: Oh yeah, things are fine. No major complaints or anything. We've just been, you know, heads-down on a big product release so the team hasn't had much bandwidth to explore new features. The platform is working fine for what we use it for.

Sarah: Got it, makes sense. I saw you had a CTO transition recently - how's that going?

Mark: Yeah, Vikram started June 1st. He's still getting up to speed on all our tooling. He hasn't really had a chance to look at the HR platform yet, to be honest. He's been focused on the engineering stack first, which is fair.

Sarah: Totally understandable. Have you had a chance to check out the new workflow automation features we launched last month? They're really designed for engineering-heavy orgs like yours.

Mark: Um, not really. I saw the email about it but we just haven't had the bandwidth. I think a couple of people on the team tried it and ran into some issues with the trigger configurations? They filed a ticket I think. But it's not really been a priority.

Sarah: No worries. If it would help, we could set up a quick walkthrough session with your team to get them up to speed.

Mark: Maybe, yeah. Let me check with Vikram first. He might want to do a broader review of all our SaaS tools anyway. A colleague of his at his previous company used a platform that auto-generates compliance reports, and he was pretty impressed by that. So he might want to do some comparisons.

Sarah: Sure, we actually have compliance reporting capabilities too - happy to demo those. Should I send over some materials?

Mark: Yeah, go ahead and send them. I'll forward to Vikram. No promises on timeline though - like I said, we're pretty buried right now.

Sarah: Totally understand. I'll send those over today and we can reconnect in a couple of weeks?

Mark: Sounds good. Thanks, Sarah."""
}


# ============================================================
# KNOWLEDGE BASE DOCUMENTS
# ============================================================

KNOWLEDGE_BASE_DOCS = {
    "onboarding_guide.md": """# Customer Onboarding Guide - Implementation & Adoption Framework

## Overview
This guide outlines the standard onboarding process for new customers, from contract signing through full platform adoption. A well-executed onboarding experience is the strongest predictor of long-term customer success and retention.

## Onboarding Timeline

### Week 1: Technical Setup
- Assign a dedicated Implementation Specialist to the account.
- Complete SSO/SAML configuration with the customer's identity provider (Azure AD, Okta, Google Workspace).
- Set up bulk user import using the provided CSV template. Verify column mapping before processing batches larger than 200 records.
- Configure role-based access control (RBAC) according to the customer's organizational hierarchy.
- Establish API credentials for any third-party integrations (HRIS, payroll, ERP systems).

### Week 2: Data Migration & Configuration
- Import historical employee data and verify data integrity.
- Configure custom workflows, approval chains, and notification rules.
- Set up department-level dashboard views with appropriate permission scoping.
- Run a pilot test with 10-15 power users to identify configuration issues early.

### Week 3: Training & Adoption Checkpoint
- Conduct a 90-minute admin training session covering platform navigation, reporting, and user management.
- Deliver role-specific training for HR managers, department heads, and end users (30 minutes each).
- **Critical checkpoint: verify that more than 50% of licensed seats have been activated. If activation is below 50% at the Week 3 mark, escalate to the assigned CSM for an adoption intervention.**
- If dashboard usage is low, schedule customer training sessions to demonstrate analytics capabilities and drive adoption.

### Week 4: Go-Live & Handoff
- Transition from Implementation Specialist to Customer Success Manager.
- Schedule the first 30-day check-in call to review adoption metrics.
- Ensure the customer has completed at least one full workflow cycle.

## Adoption Best Practices
- Schedule personalized training sessions for teams with dashboard usage below 40%. Hands-on workshops are 3x more effective than documentation alone.
- Create a "Champion Network" - identify 2-3 power users per department for peer support.
- Share monthly usage reports with the customer's project sponsor for executive visibility.

## Common Onboarding Pitfalls
- **Bulk import failures**: Validate CSV formatting before upload (date formats, special characters, duplicate IDs).
- **SSO configuration errors**: Test with at least 3 different user roles before full rollout.
- **Slow API integrations**: For ERP/payroll integrations, allow 5-7 business days for credential provisioning.
""",

    "integration_guide.md": """# Integration Guide - Third-Party Systems & API Reference

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
""",

    "renewal_playbook.md": """# Renewal Playbook - Customer Success Team

## Overview
This playbook provides structured guidance for CSMs handling accounts approaching renewal. Follow these protocols to maximize retention and execute timely interventions.

## 90-Day Pre-Renewal Checklist

### Days 90-60: Health Assessment
- Review customer health score. Accounts below 50 require immediate CSM attention and risk mitigation plan.
- Analyze seat utilization: if active users < 60% of licensed, schedule a usage review call.
- Pull 3-month support ticket history. More than 5 open tickets is a red flag - escalate to support lead.

### Days 60-30: Engagement & Value Demonstration
- Schedule a QBR to present ROI metrics, usage trends, and feature adoption data.
- If dashboard usage is low, schedule customer training sessions to reinforce analytics value and demonstrate ROI. Low dashboard adoption is one of the strongest predictors of non-renewal.
- Share relevant case studies from the customer's industry.
- If competitors mentioned, prepare competitive comparison document.

### Days 30-15: Renewal Execution
- Send formal renewal proposal with pricing and recommended plan changes.
- If health score < 40 AND renewal within 30 days, trigger executive sponsor outreach within 48 hours.
- Address ALL outstanding support tickets before renewal negotiations.
- Offer incentives: multi-year discount (15% for 2-year, 20% for 3-year), training credits, dedicated support.

### Days 15-0: Final Push
- Daily check-ins with account owner.
- If no response to renewal proposal, escalate to regional sales director.
- Document all renewal conversations in CRM.

## Risk Indicators & Escalation Matrix

| Risk Signal | Severity | Action |
|---|---|---|
| Health score below 30 | Critical | Executive sponsor call within 48 hours |
| No login 14+ days | High | Immediate CSM outreach |
| Competitor evaluation mentioned | High | Schedule competitive demo |
| Champion/sponsor departure | High | Identify new internal advocate |
| Dashboard usage below 40% | Medium | Schedule personalized training |
| QBR declined/postponed twice | Medium | Escalate to CSM manager |
""",

    "customer_success_sop.md": """# Customer Success Standard Operating Procedures

## Overview
Standard operating procedures for the Customer Success team ensuring consistent, high-quality customer engagement and proactive account management.

## Account Health Monitoring

### Daily Checks
- Review Customer Health Dashboard for accounts dropping below 50 in last 24 hours.
- Check for new Critical/High priority support tickets - respond within 4 business hours.
- Monitor login activity: flag accounts where primary contact hasn't logged in for 7+ days.

### Weekly Reviews
- Run "At-Risk Accounts" report: health score < 50, renewal within 60 days, or 3+ open tickets.
- Review usage trends - 20%+ week-over-week decline warrants proactive check-in.
- Update CRM notes for all customer interactions.

### Monthly Activities
- Prepare and deliver QBR presentations for Enterprise accounts.
- Conduct NPS surveys for accounts that completed onboarding in previous month.

## Escalation Matrix

### Tier 1 - CSM Handled
- Routine check-ins and QBRs
- Feature adoption guidance and training scheduling
- Low/Medium priority support ticket follow-ups

### Tier 2 - CSM Manager Escalation
- Health score below 40 for 2+ consecutive weeks
- Customer declined/cancelled 2+ meetings in a row
- Any mention of competitor evaluation
- Renewal at risk with no mitigation plan

### Tier 3 - Executive Sponsor Escalation
- Health score < 30 AND renewal within 30 days - executive outreach within 48 hours
- Customer requests senior leadership engagement
- Contract value above $100K with active churn indicators
- Legal, compliance, or data security concerns raised

## Customer Segmentation & Touch Frequency

| Segment | Criteria | Touch Frequency | QBR Frequency |
|---|---|---|---|
| Enterprise | Enterprise plan, >200 seats | Weekly | Monthly |
| Growth | Growth plan, 50-200 seats | Bi-weekly | Quarterly |
| Starter | Starter plan, <50 seats | Monthly | Semi-annual |
| At-Risk | Health < 50 or 3+ tickets | 2x per week minimum | Monthly |

## Proactive Engagement Protocols

### Low Adoption Outreach
When dashboard usage < 40% or seat activation < 60%:
- Schedule 30-minute "Platform Value Session" with team lead
- Prepare personalized usage report showing underutilized features
- Offer complimentary training credits (up to 3 sessions/quarter for Growth/Enterprise)

### Champion Departure Protocol
- Immediately request introduction to successor
- Schedule "New Stakeholder Onboarding" within 2 weeks
- Update account risk assessment (champion departure increases churn by ~35%)

### Competitive Threat Response
- Acknowledge evaluation is normal - do NOT be defensive
- Request meeting to understand evaluation criteria
- Prepare tailored competitive comparison
- Offer product roadmap preview
- Engage Solutions Engineer for custom demo
""",

    "faq_pricing.md": """# Pricing & Plans - Frequently Asked Questions

## Plan Comparison

### Starter Plan - $12/user/month
**Best for**: Small teams (up to 100 users) getting started with HR automation.
- Core HR management (employee records, org chart, document storage)
- Basic onboarding workflows (up to 5 templates)
- Standard reporting (10 pre-built templates)
- Email support (48-hour response SLA)
- API access: 500 requests per 15-minute window
- Single SSO provider integration

### Growth Plan - $24/user/month
**Best for**: Growing organizations (50-500 users) needing deeper analytics.
- Everything in Starter, plus:
- Advanced analytics dashboard with custom KPI tracking
- Unlimited onboarding workflow templates
- Custom report builder with scheduled delivery
- Workflow automation engine (trigger-based actions, approval chains)
- Priority support (24-hour SLA, phone support during business hours)
- API access: 1,000 requests per 15-minute window
- Up to 3 SSO integrations
- Dedicated Customer Success Manager
- 2 complimentary training sessions per quarter

### Enterprise Plan - $42/user/month
**Best for**: Large organizations (200+ users) requiring compliance and customization.
- Everything in Growth, plus:
- Unlimited custom dashboards and BI integration
- Compliance reporting suite (SOC 2, HIPAA, GDPR, ISO 27001)
- Custom field mapping for ERP integrations
- Audit trail with granular filtering
- Premium support (4-hour SLA, 24/7 phone and chat)
- API access: 5,000 requests per 15-minute window, webhook support
- Unlimited SSO integrations
- Dedicated Solutions Engineer
- Quarterly Executive Business Reviews
- 5 complimentary training sessions per quarter

## Frequently Asked Questions

**Q: How does upgrading work?**
A: Upgrades take effect immediately with prorated billing. All data and configurations are preserved. New features available within 15 minutes.

**Q: Is there a trial for higher plans?**
A: Yes - 14-day full-access trial of any higher tier. Seamless return to current plan if not upgraded.

**Q: Annual billing discounts?**
A: Annual saves 15%. Multi-year: 2-year = 15% discount, 3-year = 20% discount.

**Q: Volume discounts?**
A: Custom pricing for 500+ users. Contact your CSM or sales@xlventures.com.

**Q: What happens if we exceed API rate limits?**
A: Requests get 429 HTTP response (not charged). Implement exponential backoff. Consider upgrading if consistently hitting limits.

**Q: Additional training sessions?**
A: $500 per session (90 min, up to 15 participants). Bulk package (10 sessions) at 20% discount.
"""
}


# ============================================================
# DATA GENERATION FUNCTIONS
# ============================================================

def create_directories():
    """Create all required data directories."""
    for d in [BASE_DIR, TRANSCRIPTS_DIR, KNOWLEDGE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directories created: {BASE_DIR}")


def generate_customers():
    """Generate customers.csv with archetype-driven profiles."""
    rows = []
    for p in CUSTOMER_PROFILES:
        renewal_date = TODAY + timedelta(days=p["RenewalDays"])
        rows.append({
            "CustomerID": p["CustomerID"],
            "Company": p["Company"],
            "Plan": p["Plan"],
            "Industry": p["Industry"],
            "RenewalDate": renewal_date.strftime("%Y-%m-%d"),
            "HealthScore": p["HealthScore"]
        })

    df = pd.DataFrame(rows)
    df.to_csv(BASE_DIR / "customers.csv", index=False)
    print(f"[OK] customers.csv - {len(df)} customers generated")
    return df


def generate_usage():
    """Generate usage.csv with metrics correlated to customer health."""
    rows = []
    for p in CUSTOMER_PROFILES:
        rows.append({
            "Company": p["Company"],
            "LicensedUsers": p["LicensedUsers"],
            "ActiveUsers": p["ActiveUsers"],
            "DashboardUsagePct": p["DashboardUsagePct"],
            "APICalls": p["APICalls"]
        })

    df = pd.DataFrame(rows)
    df.to_csv(BASE_DIR / "usage.csv", index=False)
    print(f"[OK] usage.csv - {len(df)} usage records generated")
    return df


def generate_crm():
    """Generate crm.json with relationship context and hidden signals."""
    records = []
    for p in CUSTOMER_PROFILES:
        last_meeting = (TODAY - timedelta(days=p["LastMeetingDaysAgo"])).strftime("%Y-%m-%d")
        last_login = (TODAY - timedelta(days=p["LastLoginDaysAgo"])).strftime("%Y-%m-%d")
        records.append({
            "company": p["Company"],
            "last_meeting_date": last_meeting,
            "last_login_date": last_login,
            "customer_owner": p["Owner"],
            "support_tickets_open": p["TicketsOpen"],
            "notes": p["Notes"]
        })

    with open(BASE_DIR / "crm.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"[OK] crm.json - {len(records)} CRM records generated")
    return records


def generate_support_tickets():
    """Generate support_tickets.csv with realistic HR SaaS issues."""
    tickets = []
    ticket_id = 1

    for p in CUSTOMER_PROFILES:
        archetype = p["Archetype"]
        templates = TICKET_TEMPLATES.get(archetype, [])

        # Select tickets based on archetype and open ticket count
        num_tickets = p["TicketsOpen"]
        if num_tickets == 0:
            continue

        selected = templates[:num_tickets] if len(templates) >= num_tickets else templates * 2
        selected = selected[:num_tickets]

        for i, (subject, priority) in enumerate(selected):
            # Spread creation dates over last 30 days
            days_ago = random.randint(2, 30)
            created = (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # Most tickets for crisis customers are Open
            if archetype == "crisis":
                status = random.choice(["Open", "Open", "Open", "Pending"])
            elif archetype == "new_onboarding":
                status = random.choice(["Open", "Pending"])
            else:
                status = random.choice(["Open", "Pending", "Resolved"])

            tickets.append({
                "TicketID": f"T{ticket_id:03d}",
                "Company": p["Company"],
                "Subject": subject,
                "Priority": priority,
                "Status": status,
                "CreatedDate": created
            })
            ticket_id += 1

    # Add some resolved tickets for healthier companies to show history
    resolved_extras = [
        ("Orion Enterprises", "Minor formatting issue in scheduled reports", "Low", "Resolved"),
        ("Vanguard Media", "Request: additional dashboard color themes", "Low", "Resolved"),
        ("Atlas Finserv", "Quarterly compliance export formatting update", "Low", "Resolved"),
        ("Meridian Logistics", "Feature request: bulk shift scheduling import", "Low", "Resolved"),
    ]
    for company, subject, priority, status in resolved_extras:
        days_ago = random.randint(15, 45)
        tickets.append({
            "TicketID": f"T{ticket_id:03d}",
            "Company": company,
            "Subject": subject,
            "Priority": priority,
            "Status": status,
            "CreatedDate": (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        })
        ticket_id += 1

    df = pd.DataFrame(tickets)
    df = df.sort_values("CreatedDate").reset_index(drop=True)
    df.to_csv(BASE_DIR / "support_tickets.csv", index=False)
    print(f"[OK] support_tickets.csv - {len(df)} tickets generated")
    return df


def generate_recommendation_history():
    """Generate empty recommendation history (populated by the platform)."""
    with open(BASE_DIR / "recommendation_history.json", "w", encoding="utf-8") as f:
        json.dump([], f)
    print("[OK] recommendation_history.json - initialized (empty)")


def generate_meeting_transcripts():
    """Generate realistic meeting transcripts for key customer archetypes."""
    for filename, template in TRANSCRIPT_TEMPLATES.items():
        meeting_date = (TODAY - timedelta(days=random.randint(1, 5))).strftime("%B %d, %Y")
        content = template.format(meeting_date=meeting_date)
        filepath = TRANSCRIPTS_DIR / f"{filename}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        word_count = len(content.split())
        print(f"[OK] meeting_transcripts/{filename}.txt - {word_count} words")


def generate_knowledge_base():
    """Generate enterprise knowledge base documents."""
    for filename, content in KNOWLEDGE_BASE_DOCS.items():
        filepath = KNOWLEDGE_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        word_count = len(content.split())
        print(f"[OK] knowledge_base/{filename} - {word_count} words")


# ============================================================
# DATA VALIDATION
# ============================================================

def validate_dataset():
    """Run validation checks on all generated data."""
    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)

    errors = []
    warnings = []
    passed = 0

    # 1. Check customers.csv exists and has correct data
    customers_path = BASE_DIR / "customers.csv"
    if customers_path.exists():
        df = pd.read_csv(customers_path)

        # Check C001 exists
        c001 = df[df["CustomerID"] == "C001"]
        if len(c001) == 1:
            passed += 1
            print("[PASS] C001 (ABC Manufacturing) exists")

            # Check health score
            if c001.iloc[0]["HealthScore"] == 42:
                passed += 1
                print("[PASS] C001 HealthScore = 42")
            else:
                errors.append(f"C001 HealthScore is {c001.iloc[0]['HealthScore']}, expected 42")

            # Check renewal date
            expected_renewal = (TODAY + timedelta(days=20)).strftime("%Y-%m-%d")
            if c001.iloc[0]["RenewalDate"] == expected_renewal:
                passed += 1
                print(f"[PASS] C001 RenewalDate = {expected_renewal} (20 days from today)")
            else:
                errors.append(f"C001 RenewalDate is {c001.iloc[0]['RenewalDate']}, expected {expected_renewal}")
        else:
            errors.append("C001 not found in customers.csv")

        # Check row count
        if len(df) == 10:
            passed += 1
            print(f"[PASS] customers.csv has {len(df)} customers")
        else:
            errors.append(f"customers.csv has {len(df)} rows, expected 10")
    else:
        errors.append("customers.csv not found")

    # 2. Check usage.csv
    usage_path = BASE_DIR / "usage.csv"
    if usage_path.exists():
        df = pd.read_csv(usage_path)
        abc = df[df["Company"] == "ABC Manufacturing"]
        if len(abc) == 1:
            row = abc.iloc[0]
            if row["LicensedUsers"] == 500 and row["ActiveUsers"] == 160 and row["DashboardUsagePct"] == 32:
                passed += 1
                print("[PASS] ABC Manufacturing usage: 500 licensed, 160 active, 32% dashboard")
            else:
                errors.append("ABC Manufacturing usage metrics don't match expected values")
        passed += 1
        print(f"[PASS] usage.csv exists ({len(df)} records)")
    else:
        errors.append("usage.csv not found")

    # 3. Check crm.json
    crm_path = BASE_DIR / "crm.json"
    if crm_path.exists():
        with open(crm_path, "r") as f:
            crm = json.load(f)
        abc_crm = [r for r in crm if r["company"] == "ABC Manufacturing"]
        if abc_crm and abc_crm[0]["support_tickets_open"] == 7:
            passed += 1
            print("[PASS] ABC Manufacturing CRM: 7 open tickets")
        else:
            errors.append("ABC Manufacturing CRM data incorrect")
        passed += 1
        print(f"[PASS] crm.json exists ({len(crm)} records)")
    else:
        errors.append("crm.json not found")

    # 4. Check support tickets
    tickets_path = BASE_DIR / "support_tickets.csv"
    if tickets_path.exists():
        df = pd.read_csv(tickets_path)
        passed += 1
        print(f"[PASS] support_tickets.csv exists ({len(df)} tickets)")
    else:
        errors.append("support_tickets.csv not found")

    # 5. Check meeting transcripts
    for transcript in ["abc_manufacturing.txt", "meridian_logistics.txt", "novatech_solutions.txt"]:
        path = TRANSCRIPTS_DIR / transcript
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().lower()
            # Validate ABC transcript content
            if transcript == "abc_manufacturing.txt":
                checks = {
                    "analytics/adoption": "analytics" in content or "adoption" in content or "dashboard" in content,
                    "renewal": "renewal" in content,
                    "SAP integration": "sap" in content,
                    "competitors": "competitor" in content or "vendor" in content or "bamboohr" in content or "workday" in content
                }
                for check_name, result in checks.items():
                    if result:
                        passed += 1
                        print(f"[PASS] ABC transcript mentions: {check_name}")
                    else:
                        errors.append(f"ABC transcript missing mention of: {check_name}")
            passed += 1
            print(f"[PASS] {transcript} exists")
        else:
            errors.append(f"{transcript} not found")

    # 6. Check knowledge base files
    for kb_file in KNOWLEDGE_BASE_DOCS.keys():
        path = KNOWLEDGE_DIR / kb_file
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Check training recommendation exists in key files
            if kb_file in ["renewal_playbook.md", "onboarding_guide.md"]:
                if "training" in content.lower() and "dashboard" in content.lower():
                    passed += 1
                    print(f"[PASS] {kb_file} - contains training recommendation for low dashboard usage")
                else:
                    warnings.append(f"{kb_file} may be missing training recommendation")
            passed += 1
            print(f"[PASS] knowledge_base/{kb_file} exists")
        else:
            errors.append(f"knowledge_base/{kb_file} not found")

    # 7. Cross-reference validation
    customers = pd.read_csv(BASE_DIR / "customers.csv")
    usage = pd.read_csv(BASE_DIR / "usage.csv")
    customer_companies = set(customers["Company"])
    usage_companies = set(usage["Company"])
    if customer_companies == usage_companies:
        passed += 1
        print("[PASS] Cross-reference: customers.csv <-> usage.csv companies match")
    else:
        errors.append(f"Company mismatch between customers.csv and usage.csv")

    # Summary
    print("\n" + "-" * 60)
    print(f"RESULTS: {passed} passed | {len(errors)} errors | {len(warnings)} warnings")

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"   - {e}")

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"   - {w}")

    if not errors:
        print("\nALL VALIDATIONS PASSED")

    print("-" * 60)
    return len(errors) == 0


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("=" * 60)
    print("ENTERPRISE SYNTHETIC DATA GENERATION PIPELINE")
    print(f"Target: {BASE_DIR}")
    print(f"Date: {TODAY}")
    print("=" * 60 + "\n")

    # Phase 1: Setup
    create_directories()
    print()

    # Phase 2: Generate structured data
    print("--- Structured Data ---")
    generate_customers()
    generate_usage()
    generate_crm()
    generate_support_tickets()
    generate_recommendation_history()
    print()

    # Phase 3: Generate unstructured data
    print("--- Meeting Transcripts ---")
    generate_meeting_transcripts()
    print()

    print("--- Knowledge Base ---")
    generate_knowledge_base()
    print()

    # Phase 4: Validate
    success = validate_dataset()
    print()

    if success:
        print("=" * 60)
        print("Enterprise synthetic dataset generation completed successfully")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Dataset generation completed with errors - review above")
        print("=" * 60)


if __name__ == "__main__":
    main()
