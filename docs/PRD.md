# Product Requirements Document (PRD)

## Quick Commerce Commission Tracker

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-07-27 |
| **Author** | Rahul |
| **Status** | Draft |
| **Repository** | https://github.com/rahul0113/quick-commerce-commission-tracker |

---

## 1. Problem Statement

Indian quick commerce platforms (Zomato, Swiggy, Blinkit, Instamart) charge sellers commissions of 15-25% per order. These commissions often include extra/unauthorized deductions that sellers cannot easily track or dispute. Currently, sellers must:

- Manually log into each platform's dashboard/app
- Export settlement reports (if available)
- Reconcile payments in spreadsheets
- Manually calculate expected vs actual commissions
- Miss overcharges due to lack of real-time tracking

**Result:** Sellers lose 2-7% of revenue annually due to untracked commission discrepancies.

---

## 2. Solution

An open-source, multi-platform commission tracking tool that:

1. **Automatically fetches** payment data from quick commerce platforms
2. **Calculates expected commissions** based on contract rates
3. **Detects anomalies** (overcharges, missing settlements, hidden fees)
4. **Provides a unified dashboard** across all platforms
5. **Generates reports** for dispute resolution

---

## 3. Target Users

| User Type | Description |
|-----------|-------------|
| **Primary** | Small/medium restaurant owners selling on multiple platforms |
| **Secondary** | Cloud kitchen operators managing 5+ brands |
| **Tertiary** | Accounting firms handling multi-platform reconciliation |

---

## 4. Platform Priority

| Priority | Platform | API Available | Integration Method |
|----------|----------|---------------|-------------------|
| P0 | Zomato | No | Playwright scraping |
| P0 | Swiggy | No | Playwright scraping |
| P0 | Blinkit | No | Zomato backend (shared scraper) |
| P0 | Instamart | No | Swiggy backend (shared scraper) |
| P1 | Amazon | Yes (SP-API) | REST API |
| P1 | Flipkart | Yes (Marketplace API) | REST API |
| P2 | Dunzo | Limited | API + scraping |
| P2 | BigBasket | No | Scraping |
| P2 | Meesho | Limited | API |

---

## 5. Features

### 5.1 Core Features (MVP)

#### F1: Multi-Platform Data Aggregation
- **Description:** Connect to multiple platforms and fetch payment/settlement data
- **Acceptance Criteria:**
  - User can add credentials for each platform
  - System fetches payment records automatically
  - Data is normalized across platforms
- **Platforms:** Zomato, Swiggy, Blinkit, Instamart

#### F2: Commission Calculation Engine
- **Description:** Calculate expected vs actual commissions per order
- **Acceptance Criteria:**
  - System knows the commission rate for each platform/category
  - Calculates expected commission: `total_price × rate / 100`
  - Calculates difference: `expected - actual`
  - Flags orders where difference > 1%
- **Default Rates:**
  - Zomato: 18%
  - Swiggy: 18%
  - Blinkit: 22%
  - Instamart: 18%

#### F3: Anomaly Detection
- **Description:** Identify orders with unexpected commission charges
- **Acceptance Criteria:**
  - Detects overcharges (actual > expected)
  - Detects undercharges (actual < expected)
  - Severity levels: low (<2%), medium (2-5%), high (>5%)
  - Alerts sorted by impact (absolute difference)

#### F4: Unified Dashboard
- **Description:** Single view of all platform payments and commissions
- **Acceptance Criteria:**
  - Overview cards: total overcharged, platforms connected, avg rate
  - Pie chart: commission by platform
  - Table: monthly summary by platform
  - Alerts list: top anomalies with severity

### 5.2 Enhanced Features (v1.1)

#### F5: Automated Scraping
- **Description:** Scheduled scraping of platform dashboards
- **Acceptance Criteria:**
  - Configurable scrape interval (default: 6 hours)
  - Retry logic with exponential backoff
  - Screenshot capture for debugging
  - Job status tracking

#### F6: Custom Commission Rates
- **Description:** Allow users to set their own commission rates
- **Acceptance Criteria:**
  - Per-platform, per-category rates
  - Effective date ranges
  - Override default rates

#### F7: Export & Reports
- **Description:** Export data for accounting/disputes
- **Acceptance Criteria:**
  - CSV export of payment records
  - PDF summary reports
  - Date range filtering
  - Platform-wise breakdown

### 5.3 Future Features (v2.0)

#### F8: API Integrations (Amazon, Flipkart)
- **Description:** Direct API access for platforms with public APIs
- **Acceptance Criteria:**
  - OAuth 2.0 authentication
  - Real-time sync via webhooks
  - Rate limiting compliance

#### F9: SMS/Email Notifications
- **Description:** Alert users of significant anomalies
- **Acceptance Criteria:**
  - Daily digest of overcharges
  - Real-time alerts for high-severity issues
  - Configurable thresholds

#### F10: Multi-User Support
- **Description:** Team access with role-based permissions
- **Acceptance Criteria:**
  - Admin/Viewer roles
  - Invitation system
  - Activity audit log

---

## 6. Technical Architecture

### 6.1 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13+, FastAPI |
| **Database** | PostgreSQL (asyncpg) |
| **Cache** | Redis |
| **Scraping** | Playwright (async) |
| **Frontend** | Next.js 14, React 18 |
| **Charts** | Recharts |
| **Styling** | Tailwind CSS |
| **Auth** | SuperAuth (JWT) |
| **Hosting** | Cloud (Vercel + Railway/Render) |

### 6.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                    Next.js + React                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Dashboard │ │  Alerts  │ │  Reports │ │ Settings │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (JWT)
┌─────────────────────────┴───────────────────────────────────┐
│                        Backend                              │
│                    FastAPI + Python                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Layer                           │  │
│  │  /payments  /summary  /alerts  /sync  /credentials   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │ Commission Engine │  │       Scraper Layer           │   │
│  │ - Rate lookup     │  │  ┌─────────┐  ┌─────────┐   │   │
│  │ - Calculation     │  │  │ Zomato  │  │ Swiggy  │   │   │
│  │ - Anomaly detect  │  │  │ Scraper │  │ Scraper │   │   │
│  │ - Aggregation     │  │  └─────────┘  └─────────┘   │   │
│  └──────────────────┘  └──────────────────────────────┘   │
└───────────┬────────────────────────────┬───────────────────┘
            │                            │
┌───────────┴──────────┐  ┌──────────────┴───────────────────┐
│     PostgreSQL        │  │            Redis                  │
│  - payment_records    │  │  - Session cache                  │
│  - users              │  │  - Rate limiting                  │
│  - credentials        │  │  - Scrape job queue               │
│  - commission_rates   │  │                                    │
└───────────────────────┘  └──────────────────────────────────┘
```

### 6.3 Database Schema

```sql
-- Core tables
users (id, email, name, password_hash, created_at)
platform_credentials (id, user_id, platform, credentials, is_active, last_sync_at)
payment_records (id, user_id, platform, order_id, order_date, settlement_date,
                 item_description, item_quantity, item_price, total_price,
                 expected_commission_rate, actual_commission_charged,
                 commission_difference, platform_fee, delivery_fee,
                 gst_on_fees, tds, other_deductions, gross_amount,
                 total_deductions, net_settlement, fetched_at, source, raw)
commission_rates (id, platform, category, base_rate, gst_rate, tds_rate,
                  effective_from, effective_to)
scrape_jobs (id, user_id, platform, status, records_found, records_new,
             error, started_at, completed_at)
```

### 6.4 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/payments` | List payments with filters | JWT |
| GET | `/api/summary` | Commission summary by platform | JWT |
| GET | `/api/alerts` | Commission anomalies | JWT |
| GET | `/api/overcharged` | Total overcharged amount | JWT |
| POST | `/api/sync/{platform}` | Trigger platform sync | JWT |
| POST | `/api/credentials` | Save platform credentials | JWT |
| GET | `/api/credentials` | List connected platforms | JWT |
| POST | `/api/rates` | Add custom commission rate | JWT |
| GET | `/health` | Health check | None |

---

## 7. Commission Rate Reference

| Platform | Base Rate | GST on Fees | TDS | Payment Cycle |
|----------|-----------|-------------|-----|---------------|
| Zomato | 15-25% | 18% | 1% | Weekly |
| Swiggy | 15-25% | 18% | 1% | Weekly |
| Blinkit | 20-25% | 18% | 1% | Weekly |
| Instamart | 15-25% | 18% | 1% | Weekly |
| Amazon | 5-45% | 18% | 1% | 7-14 days |
| Flipkart | 5-25% | 18% | 1% | 7-14 days |

**Note:** Rates vary by category, city, and seller tier.

---

## 8. Data Flow

### 8.1 Scraping Flow

```
User adds credentials
        │
        ▼
┌───────────────────┐
│  Save to DB       │
│  (encrypted)      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Scrape Job       │
│  Triggered        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Playwright       │
│  Browser Session  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Login to         │
│  Platform         │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Navigate to      │
│  Payments Page    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Extract Data     │
│  (DOM parsing)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Normalize &      │
│  Save to DB       │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Calculate        │
│  Commissions      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Detect           │
│  Anomalies        │
└───────────────────┘
```

### 8.2 Data Normalization

Each platform provides data in different formats. The system normalizes to:

```python
{
    "platform": "zomato",
    "order_id": "ORD-12345",
    "order_date": "2026-01-15T10:30:00Z",
    "total_price": 500.00,
    "expected_commission_rate": 18.0,
    "actual_commission_charged": 90.00,
    "commission_difference": 0.00,
    "gross_amount": 500.00,
    "total_deductions": 90.00,
    "net_settlement": 410.00
}
```

---

## 9. Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| Authentication | JWT tokens (SuperAuth) |
| Authorization | User-scoped data access |
| Credential Storage | Encrypted at rest (planned) |
| API Rate Limiting | 100 requests/15 min per IP |
| CORS | Restricted origins only |
| SQL Injection | Parameterized queries |
| XSS | React auto-escaping + CSP |

---

## 10. Performance Requirements

| Metric | Target |
|--------|--------|
| API Response Time | < 200ms (p95) |
| Dashboard Load | < 2s |
| Scrape Duration | < 30s per platform |
| Concurrent Scrapes | 2 max |
| Database Queries | < 50ms (p95) |

---

## 11. Deployment

### 11.1 Cloud Architecture

```
┌─────────────────────────────────────────┐
│              Vercel                      │
│         (Frontend Hosting)              │
│         Next.js + Static Assets         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           Railway / Render              │
│         (Backend Hosting)               │
│         FastAPI + Playwright            │
└─────────┬───────────────┬───────────────┘
          │               │
┌─────────┴──────┐  ┌─────┴──────────────┐
│   Supabase     │  │   Upstash Redis    │
│  (PostgreSQL)  │  │   (Cache/Queue)    │
└────────────────┘  └────────────────────┘
```

### 11.2 Environment Variables

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
JWT_SECRET=<256-bit-secret>

# Scraping
HEADLESS_BROWSER=true
SCRAPE_INTERVAL_HOURS=6
SCRAPE_MAX_CONCURRENT=2
```

---

## 12. Success Metrics

| Metric | Target (6 months) |
|--------|-------------------|
| GitHub Stars | 500+ |
| Monthly Active Users | 100+ |
| Platforms Supported | 4 (MVP) |
| Commission Accuracy | 99.5% |
| Anomaly Detection Rate | 95%+ |
| False Positive Rate | < 5% |

---

## 13. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Platform blocks scraping | High | Medium | Rotate user agents, rate limit, proxy support |
| Commission rates change | Medium | High | Configurable rates, community updates |
| Platform adds CAPTCHA | High | Medium | Manual fallback, CAPTCHA solving services |
| API deprecation | Medium | Low | Version pinning, quick adapter updates |
| Legal concerns | High | Low | Read-only scraping, no data resale, ToS review |

---

## 14. Open Source Strategy

- **License:** MIT
- **Contributing:** PRs welcome, clear CONTRIBUTING.md
- **Community:** GitHub Issues for bugs, Discussions for features
- **Documentation:** Inline code docs + wiki
- **Release Cadence:** Bi-weekly patches, monthly features

---

## 15. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: MVP** | Weeks 1-4 | Backend, scrapers, basic dashboard |
| **Phase 2: Polish** | Weeks 5-6 | Error handling, auth, deployment |
| **Phase 3: Launch** | Weeks 7-8 | Documentation, community setup |
| **Phase 4: Growth** | Months 3-6 | API integrations, more platforms |

---

## 16. Appendix

### A. API Research Summary

| Platform | Public API | Difficulty | Notes |
|----------|-----------|------------|-------|
| Zomato | No | High | Web dashboard scraping |
| Swiggy | No | High | Mobile app / web scraping |
| Blinkit | No | High | Zomato backend |
| Instamart | No | High | Swiggy backend |
| Amazon | Yes (SP-API) | Medium | Full payment data |
| Flipkart | Yes (Marketplace API) | Medium | Full payment data |
| Dunzo | Limited | High | Invite-only |
| BigBasket | No | High | Web scraping |

### B. Commission Calculation Formula

```
Expected Commission = Total Price × Expected Rate / 100
Difference = Expected Commission - Actual Commission Charged
Difference % = |Difference| / Total Price × 100

Severity:
  - Low: Difference % < 2%
  - Medium: 2% ≤ Difference % < 5%
  - High: Difference % ≥ 5%
```

### C. Competitive Landscape

| Tool | Type | Platforms | Open Source |
|------|------|-----------|-------------|
| **This Project** | Web App | Zomato, Swiggy, Blinkit, Instamart | Yes |
| Manual Spreadsheets | Manual | Any | N/A |
| Accounting Software | Desktop | Limited | No |
| Platform Dashboards | Web | Single | No |

---

*Document Version: 1.0*
*Last Updated: 2026-07-27*
