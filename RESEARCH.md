# Quick Commerce Commission Tracker — API & Integration Research

## Executive Summary

This research explores API integrations available across Indian quick commerce platforms for tracking payments and calculating commissions charged to sellers/partners. The goal is to build an open-source tool that aggregates payment data from multiple platforms and identifies extra/unauthorized commissions.

---

## Platform-by-Platform API Availability

### 1. Zomato (includes Blinkit)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Zomato for Business (business.zomato.com) |
| **Public API** | ❌ No public seller/restaurant API |
| **Partner Dashboard** | Web-based only — no programmatic access |
| **Payment Data** | Available via dashboard (weekly settlements) |
| **Commission Structure** | 15-25% per order (varies by city, category) |
| **Data Access Method** | Screen scraping / browser automation only |
| **Webhook Support** | Not documented publicly |

**Key Findings:**
- Zomato does NOT expose a public API for sellers or delivery partners
- Blinkit (acquired by Zomato) also has no public API
- Both operate through web dashboards only
- Payment reconciliation must be done manually or via scraping

---

### 2. Swiggy (includes Instamart)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Swiggy Partner App (mobile) |
| **Public API** | ❌ No public seller API |
| **Partner Dashboard** | Mobile app + limited web access |
| **Payment Data** | Available in partner app |
| **Commission Structure** | 15-25% per order |
| **Data Access Method** | Mobile app scraping / API reverse-engineering |
| **Webhook Support** | Not documented publicly |

**Key Findings:**
- Swiggy operates primarily through mobile apps for partners
- No public API documentation exists
- Instamart (quick commerce) uses the same partner infrastructure
- Some developers have reverse-engineered internal APIs (unofficial, fragile)

---

### 3. Blinkit (Zomato subsidiary)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Integrated with Zomato for Business |
| **Public API** | ❌ No public API |
| **Payment Data** | Via Zomato seller dashboard |
| **Commission Structure** | 20-25% per order |
| **Data Access Method** | Same as Zomato |

---

### 4. Zepto

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Zepto Seller Portal (seller.zepto.in) |
| **Public API** | ❌ No public API |
| **Partner Dashboard** | Web-based portal |
| **Payment Data** | Available in seller portal |
| **Commission Structure** | 15-22% per order |
| **Data Access Method** | Web scraping / browser automation |
| **Webhook Support** | Not documented |

---

### 5. Dunzo

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Dunzo for Business |
| **Public API** | ⚠️ Limited — Dunzo Merchant API (invite-only) |
| **Partner Dashboard** | Web + Mobile |
| **Payment Data** | Available in partner dashboard |
| **Commission Structure** | 15-20% per order + delivery charges |
| **Data Access Method** | API (if approved) / scraping |
| **Webhook Support** | Yes (for order updates, if approved) |

**Key Findings:**
- Dunzo has the most accessible API among quick commerce platforms
- Merchant API is available but requires business verification
- Documentation is limited and requires NDA

---

### 6. BigBasket (Tata Group)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | BigBasket Seller Hub |
| **Public API** | ❌ No public seller API |
| **Partner Dashboard** | Web-based portal |
| **Payment Data** | Available in seller portal |
| **Commission Structure** | 10-20% per order |
| **Data Access Method** | Web scraping |

---

### 7. Jomatos

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Jomatos Seller App |
| **Public API** | ❌ No public API |
| **Partner Dashboard** | Mobile app |
| **Payment Data** | Available in app |
| **Commission Structure** | Varies (typically 15-25%) |
| **Data Access Method** | Mobile app scraping |

---

### 8. Amazon Fresh / Amazon Marketplace

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Amazon Seller Central (sellercentral.in) |
| **Public API** | ✅ Yes — Amazon SP-API (Selling Partner API) |
| **Documentation** | https://developer-docs.amazon.com/sp-api/ |
| **Payment Data** | ✅ Full API access — Settlements, Financial Events |
| **Commission Structure** | 5-45% referral fee (category-dependent) |
| **Data Access Method** | REST API with OAuth 2.0 |
| **Rate Limits** | Throttled per endpoint |

**Key Findings:**
- **BEST OPTION** — Amazon has the most comprehensive public API
- SP-API provides: Orders, Settlements, Financial Events, Reports
- Can programmatically fetch all payment and commission data
- Requires Amazon Developer account + SP-API access approval

---

### 9. Flipkart (includes Flipkart Quick)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Flipkart Seller Hub (seller.flipkart.com) |
| **Public API** | ✅ Yes — Flipkart Marketplace API |
| **Documentation** | https://seller.flipkart.com/api-docs/ |
| **Payment Data** | ✅ Full API access — Payments, Settlements |
| **Commission Structure** | 5-25% referral fee |
| **Data Access Method** | REST API with OAuth 2.0 |
| **Rate Limits** | Varies by endpoint |

**Key Findings:**
- **STRONG OPTION** — Flipkart has good API documentation
- API provides: Orders, Payments, Settlements, Inventory
- Commission data available through payment endpoints
- Requires Flipkart seller account + API access

---

### 10. Meesho

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Meesho Seller Panel |
| **Public API** | ⚠️ Limited — Meesho Marketplace API |
| **Documentation** | Limited documentation available |
| **Payment Data** | Partial API access |
| **Commission Structure** | 0% commission (revenue via logistics) |
| **Data Access Method** | REST API (limited) |

---

### 11. PharmEasy / 1mg (Tata)

| Aspect | Details |
|--------|---------|
| **Partner Portal** | Seller portals (separate) |
| **Public API** | ❌ No public API |
| **Payment Data** | Via seller dashboard only |
| **Commission Structure** | 10-20% per order |

---

## Summary: API Availability Matrix

| Platform | Public API | Payment Data | Commission Tracking | Difficulty |
|----------|-----------|--------------|---------------------|------------|
| **Amazon** | ✅ Full | ✅ Full | ✅ Full | Medium |
| **Flipkart** | ✅ Full | ✅ Full | ✅ Full | Medium |
| **Dunzo** | ⚠️ Limited | ⚠️ Partial | ⚠️ Partial | High |
| **Meesho** | ⚠️ Limited | ⚠️ Partial | ⚠️ Partial | High |
| **Zomato** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **Blinkit** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **Swiggy** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **Instamart** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **Zepto** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **BigBasket** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |
| **Jomatos** | ❌ None | ❌ Dashboard | ❌ Manual | Very High |

---

## Recommended Architecture for Commission Tracker

### Tier 1: API-Based (Reliable)
```
┌─────────────────────────────────────────────────┐
│              Commission Tracker Core             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Amazon  │  │Flipkart │  │ Meesho  │        │
│  │ SP-API  │  │MarketAPI│  │  API    │        │
│  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │              │
│       └────────────┼────────────┘              │
│                    ▼                           │
│         ┌──────────────────┐                   │
│         │ Unified Payment  │                   │
│         │    Data Model    │                   │
│         └──────────────────┘                   │
│                    │                           │
│                    ▼                           │
│         ┌──────────────────┐                   │
│         │ Commission       │                   │
│         │ Calculator       │                   │
│         └──────────────────┘                   │
│                    │                           │
│                    ▼                           │
│         ┌──────────────────┐                   │
│         │ Dashboard /      │                   │
│         │ Reports          │                   │
│         └──────────────────┘                   │
└─────────────────────────────────────────────────┘
```

### Tier 2: Scraping-Based (Workaround)
For platforms without APIs (Zomato, Swiggy, Blinkit, Zepto):

```
┌─────────────────────────────────────────────────┐
│           Browser Automation Layer              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Playwright│ │ Puppeteer│ │Selenium │        │
│  │  (Python) │ │ (Node.js)│ │(Multi)  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │              │
│       └────────────┼────────────┘              │
│                    ▼                           │
│         ┌──────────────────┐                   │
│         │  Data Extractor  │                   │
│         │  (PDF/HTML parse)│                   │
│         └──────────────────┘                   │
│                    │                           │
│                    ▼                           │
│         ┌──────────────────┐                   │
│         │ Unified Payment  │                   │
│         │    Data Model    │                   │
│         └──────────────────┘                   │
└─────────────────────────────────────────────────┘
```

### Tier 3: Hybrid (Best Approach)
Combine API-based (Amazon, Flipkart) with scraping-based (others):

```
┌─────────────────────────────────────────────────┐
│            Hybrid Commission Tracker            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │           Connector Layer               │   │
│  ├─────────┬─────────┬─────────┬───────────┤   │
│  │ Amazon  │Flipkart │ Zomato  │  Swiggy   │   │
│  │  API    │  API    │ Scrape  │  Scrape   │   │
│  └────┬────┘────┬────┘────┬────┘─────┬─────┘   │
│       │         │         │          │         │
│       └─────────┼─────────┼──────────┘         │
│                 ▼         ▼                    │
│         ┌──────────────────────┐               │
│         │  Unified Data Layer  │               │
│         │  (PostgreSQL/SQLite) │               │
│         └──────────────────────┘               │
│                       │                        │
│                       ▼                        │
│         ┌──────────────────────┐               │
│         │  Commission Engine   │               │
│         │  - Expected rate     │               │
│         │  - Actual charged    │               │
│         │  - Difference        │               │
│         │  - Alerts            │               │
│         └──────────────────────┘               │
│                       │                        │
│                       ▼                        │
│         ┌──────────────────────┐               │
│         │  Dashboard (Web)     │               │
│         │  - Real-time tracking│               │
│         │  - Reports           │               │
│         │  - Export (CSV/PDF)  │               │
│         └──────────────────────┘               │
└─────────────────────────────────────────────────┘
```

---

## Unified Payment Data Model

```typescript
interface PaymentRecord {
  id: string;
  platform: 'amazon' | 'flipkart' | 'zomato' | 'swiggy' | 'blinkit' 
          | 'zepto' | 'dunzo' | 'bigbasket' | 'jomatos' | 'meesho';
  orderId: string;
  orderDate: Date;
  settlementDate: Date;
  
  // Order Details
  itemDescription: string;
  itemQuantity: number;
  itemPrice: number;
  totalPrice: number;
  
  // Commission Details
  expectedCommissionRate: number;  // As per contract
  actualCommissionCharged: number; // What was actually deducted
  commissionDifference: number;    // Expected - Actual
  
  // Fees Breakdown
  platformFee: number;
  deliveryFee: number;
  gstOnFees: number;
  tds: number;
  otherDeductions: number;
  
  // Settlement
  grossAmount: number;
  totalDeductions: number;
  netSettlement: number;
  
  // Metadata
  fetchedAt: Date;
  source: 'api' | 'scrape' | 'manual';
  raw?: any; // Original API response or scraped data
}
```

---

## Commission Structure Reference

| Platform | Base Commission | GST on Commission | TDS | Payment Cycle |
|----------|----------------|-------------------|-----|---------------|
| Amazon | 5-45% | 18% | 1% | 7-14 days |
| Flipkart | 5-25% | 18% | 1% | 7-14 days |
| Zomato | 15-25% | 18% | 1% | Weekly |
| Swiggy | 15-25% | 18% | 1% | Weekly |
| Blinkit | 20-25% | 18% | 1% | Weekly |
| Zepto | 15-22% | 18% | 1% | Weekly |
| Dunzo | 15-20% | 18% | 1% | Weekly |
| BigBasket | 10-20% | 18% | 1% | Weekly |
| Jomatos | 15-25% | 18% | 1% | Weekly |
| Meesho | 0% | N/A | 1% | 7-10 days |

**Note:** Commission rates vary by category, city, and seller tier. Rates above are indicative.

---

## Existing Open-Source Solutions

### Relevant Projects

| Project | Description | Language | Applicability |
|---------|-------------|----------|---------------|
| **Spree** | Multi-vendor marketplace platform | Ruby | Commission calculation patterns |
| **MedusaJS** | Headless commerce with plugins | TypeScript | Plugin architecture reference |
| **Vendure** | Headless commerce platform | TypeScript | Payment module patterns |
| **Marketplace Integration API** | Turkish marketplace integrator | JavaScript | Multi-platform connector pattern |

### No Direct Solution Exists
There is **no existing open-source tool** specifically designed for tracking quick commerce commissions across Indian platforms. This is a gap in the market.

---

## Recommended Tech Stack

### Backend
```
Runtime:      Node.js / Python (FastAPI)
Database:     PostgreSQL (primary) + Redis (cache)
API Layer:    REST + GraphQL
Scraping:     Playwright (Python) / Puppeteer (Node.js)
PDF Parsing:  pdf-parse / PyPDF2
Excel Parse:  xlsx / openpyxl
```

### Frontend
```
Framework:    Next.js / React
UI Library:   shadcn/ui / Mantine
Charts:       Recharts / Chart.js
Export:       jsPDF / react-pdf
```

### Infrastructure
```
Hosting:      Vercel / Railway / Render
Database:     Supabase / Neon
Auth:         NextAuth.js / Supabase Auth
Queue:        BullMQ (for scraping jobs)
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up project structure
- [ ] Design database schema
- [ ] Build authentication system
- [ ] Create unified payment data model

### Phase 2: API Integrations (Weeks 3-4)
- [ ] Amazon SP-API integration
- [ ] Flipkart Marketplace API integration
- [ ] Payment data normalization layer

### Phase 3: Scraping Layer (Weeks 5-6)
- [ ] Zomato seller dashboard scraper
- [ ] Swiggy partner app data extractor
- [ ] Blinkit/Zepto/BigBasket scrapers
- [ ] PDF statement parser (fallback)

### Phase 4: Commission Engine (Week 7)
- [ ] Commission calculation logic
- [ ] Expected vs actual comparison
- [ ] Anomaly detection
- [ ] Alert system

### Phase 5: Dashboard (Weeks 8-9)
- [ ] Real-time payment tracking view
- [ ] Commission reports by platform
- [ ] Export functionality (CSV, PDF)
- [ ] Historical trends

### Phase 6: Polish (Week 10)
- [ ] Error handling & retry logic
- [ ] Rate limiting for scrapers
- [ ] Documentation
- [ ] Open-source release prep

---

## Legal & Ethical Considerations

1. **API Usage**: Only use officially documented APIs (Amazon, Flipkart)
2. **Scraping**: Check robots.txt; avoid aggressive scraping
3. **Data Storage**: Encrypt sensitive financial data
4. **Rate Limits**: Respect platform rate limits
5. **Terms of Service**: Review each platform's ToS before integration
6. **User Consent**: If building for others, require explicit consent

---

## Next Steps

1. **Decide scope**: Start with API-based platforms (Amazon, Flipkart) or go all-in with scraping?
2. **Choose tech stack**: Node.js vs Python?
3. **Target platforms**: Which platforms are priority for your use case?
4. **Deployment**: Self-hosted or cloud service?

---

*Research conducted: 2026-07-27*
*Status: Complete*
