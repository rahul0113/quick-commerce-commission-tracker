# API Documentation

## Quick Commerce Commission Tracker — REST API

| Field | Value |
|-------|-------|
| **Base URL** | `http://localhost:8000` |
| **Version** | 1.0.0 |
| **Format** | JSON |
| **Auth** | JWT Bearer Token |
| **OpenAPI Spec** | `http://localhost:8000/docs` (Swagger UI) |

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Error Handling](#2-error-handling)
3. [Rate Limiting](#3-rate-limiting)
4. [Endpoints](#4-endpoints)
   - [Health Check](#41-health-check)
   - [List Payments](#42-list-payments)
   - [Commission Summary](#43-commission-summary)
   - [Commission Alerts](#44-commission-alerts)
   - [Overcharged Amount](#45-overcharged-amount)
   - [Sync Platform](#46-sync-platform)
   - [Save Credentials](#47-save-credentials)
   - [List Credentials](#48-list-credentials)
   - [Add Custom Rate](#49-add-custom-rate)
5. [Data Models](#5-data-models)
6. [Webhooks](#6-webhooks)
7. [Examples](#7-examples)

---

## 1. Authentication

All endpoints (except `/health`) require JWT authentication.

### Obtaining a Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Using the Token

Include the token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token Payload

```json
{
  "sub": "uuid-of-user",
  "email": "user@example.com",
  "exp": 1690000000,
  "iat": 1689913600
}
```

### Token Expiration

- Default: 24 hours
- Configurable via `JWT_EXPIRATION_HOURS` env var
- On expiration, API returns `401 Unauthorized`

---

## 2. Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid parameters |
| `401` | Unauthorized | Missing/invalid/expired token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `422` | Validation Error | Request body validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Server Error | Internal error |

### Error Response Examples

**Missing Auth:**
```json
{
  "detail": "Missing or invalid authorization header"
}
```

**Expired Token:**
```json
{
  "detail": "Token expired"
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["query", "start_date"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 3. Rate Limiting

| Limit | Window | Scope |
|-------|--------|-------|
| 100 requests | 15 minutes | Per IP address |

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1690000900
```

When exceeded:
```json
{
  "detail": "Too many requests"
}
```

---

## 4. Endpoints

### 4.1 Health Check

Check if the API is running.

```
GET /health
```

**Auth:** None

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

### 4.2 List Payments

Get paginated payment records with optional filters.

```
GET /api/payments
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | No | — | Filter by platform (`zomato`, `swiggy`, `blinkit`, `instamart`) |
| `start_date` | datetime | No | — | Filter payments after this date (ISO 8601) |
| `end_date` | datetime | No | — | Filter payments before this date (ISO 8601) |
| `page` | integer | No | `1` | Page number (min: 1) |
| `limit` | integer | No | `50` | Results per page (min: 1, max: 100) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "platform": "zomato",
      "order_id": "ORD-12345",
      "order_date": "2026-07-15T10:30:00Z",
      "settlement_date": "2026-07-22T00:00:00Z",
      "item_description": "Margherita Pizza, Coke",
      "item_quantity": 2,
      "item_price": 250.00,
      "total_price": 500.00,
      "expected_commission_rate": 18.0,
      "actual_commission_charged": 95.00,
      "commission_difference": -5.00,
      "platform_fee": 0.00,
      "delivery_fee": 30.00,
      "gst_on_fees": 16.20,
      "tds": 5.00,
      "other_deductions": 0.00,
      "gross_amount": 500.00,
      "total_deductions": 146.20,
      "net_settlement": 353.80,
      "fetched_at": "2026-07-15T11:00:00Z",
      "source": "scrape"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 234,
    "pages": 5
  }
}
```

**Example Requests:**

```bash
# All payments
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/payments"

# Zomato payments in July 2026
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/payments?platform=zomato&start_date=2026-07-01T00:00:00Z&end_date=2026-07-31T23:59:59Z"

# Page 2, 25 per page
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/payments?page=2&limit=25"
```

---

### 4.3 Commission Summary

Get monthly commission summary grouped by platform.

```
GET /api/summary
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | datetime | **Yes** | — | Start of date range (ISO 8601) |
| `end_date` | datetime | **Yes** | — | End of date range (ISO 8601) |
| `platform` | string | No | — | Filter by single platform |

**Response (200):**
```json
[
  {
    "platform": "zomato",
    "period": "2026-07-01 00:00:00+00",
    "total_orders": 156,
    "total_sales": 78000.00,
    "total_commission_charged": 14820.00,
    "total_commission_expected": 14040.00,
    "total_overcharged": 780.00,
    "avg_commission_rate": 19.0,
    "net_settled": 63180.00
  },
  {
    "platform": "swiggy",
    "period": "2026-07-01 00:00:00+00",
    "total_orders": 89,
    "total_sales": 44500.00,
    "total_commission_charged": 8010.00,
    "total_commission_expected": 8010.00,
    "total_overcharged": 0.00,
    "avg_commission_rate": 18.0,
    "net_settled": 36490.00
  }
]
```

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/summary?start_date=2026-07-01T00:00:00Z&end_date=2026-07-31T23:59:59Z"
```

---

### 4.4 Commission Alerts

Get detected anomalies (overcharges/undercharges).

```
GET /api/alerts
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | No | — | Filter by platform |
| `start_date` | datetime | No | — | Filter after this date |
| `end_date` | datetime | No | — | Filter before this date |

**Response (200):**
```json
[
  {
    "platform": "zomato",
    "order_id": "ORD-67890",
    "expected": 180.00,
    "actual": 250.00,
    "difference": -70.00,
    "severity": "high",
    "message": "Overcharged by ₹70.00 (7.0% of order)"
  },
  {
    "platform": "swiggy",
    "order_id": "ORD-11111",
    "expected": 90.00,
    "actual": 100.00,
    "difference": -10.00,
    "severity": "medium",
    "message": "Overcharged by ₹10.00 (2.0% of order)"
  }
]
```

**Severity Levels:**

| Level | Criteria | Color |
|-------|----------|-------|
| `low` | Difference < 2% of order | Blue |
| `medium` | 2% ≤ Difference < 5% | Yellow |
| `high` | Difference ≥ 5% | Red |

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/alerts?platform=zomato&start_date=2026-07-01T00:00:00Z"
```

---

### 4.5 Overcharged Amount

Get total overcharged amount across all platforms.

```
GET /api/overcharged
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | datetime | **Yes** | — | Start of date range (ISO 8601) |
| `end_date` | datetime | **Yes** | — | End of date range (ISO 8601) |

**Response (200):**
```json
{
  "total_overcharged": 1250.00,
  "by_platform": {
    "zomato": 780.00,
    "swiggy": 320.00,
    "blinkit": 150.00
  }
}
```

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/overcharged?start_date=2026-07-01T00:00:00Z&end_date=2026-07-31T23:59:59Z"
```

---

### 4.6 Sync Platform

Trigger a manual sync for a specific platform.

```
POST /api/sync/{platform}
```

**Auth:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | Platform to sync (`zomato`, `swiggy`, `blinkit`, `instamart`) |

**Request Body (optional):**

```json
{
  "start_date": "2026-07-01T00:00:00Z",
  "end_date": "2026-07-31T23:59:59Z"
}
```

**Response (200):**
```json
{
  "platform": "zomato",
  "records_found": 45,
  "records_new": 12,
  "records_skipped": 33,
  "errors": []
}
```

**Error Response (400):**
```json
{
  "error": "No credentials found",
  "platform": "zomato"
}
```

**Example Request:**

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2026-07-01T00:00:00Z"}' \
  "http://localhost:8000/api/sync/zomato"
```

---

### 4.7 Save Credentials

Save or update platform login credentials.

```
POST /api/credentials
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platform` | string | **Yes** | Platform identifier |

**Request Body:**

```json
{
  "email": "restaurant@email.com",
  "password": "secure-password",
  "otp": "123456"
}
```

**Credential Fields by Platform:**

| Platform | Required Fields | Optional Fields |
|----------|----------------|-----------------|
| `zomato` | `email`, `password` | `otp` |
| `swiggy` | `phone` | `otp` |
| `blinkit` | `email`, `password` | `otp` |
| `instamart` | `phone` | `otp` |

**Response (200):**
```json
{
  "success": true
}
```

**Example Request:**

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "restaurant@email.com", "password": "secret123"}' \
  "http://localhost:8000/api/credentials?platform=zomato"
```

---

### 4.8 List Credentials

List all connected platforms and their status.

```
GET /api/credentials
```

**Auth:** Required

**Response (200):**
```json
[
  {
    "platform": "zomato",
    "is_active": true,
    "last_sync_at": "2026-07-27T10:30:00Z",
    "created_at": "2026-07-01T08:00:00Z"
  },
  {
    "platform": "swiggy",
    "is_active": true,
    "last_sync_at": "2026-07-27T09:15:00Z",
    "created_at": "2026-07-05T12:00:00Z"
  },
  {
    "platform": "blinkit",
    "is_active": false,
    "last_sync_at": null,
    "created_at": "2026-07-10T14:30:00Z"
  }
]
```

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/credentials"
```

---

### 4.9 Add Custom Rate

Add a custom commission rate for a platform/category.

```
POST /api/rates
```

**Auth:** Required

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | **Yes** | — | Platform identifier |
| `category` | string | **Yes** | — | Product category (`*` for all) |
| `rate` | float | **Yes** | — | Commission rate (0-100) |
| `effective_from` | datetime | No | Now | When this rate takes effect |

**Response (200):**
```json
{
  "success": true
}
```

**Example Request:**

```bash
# Set 20% commission for Zomato pizza category
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/rates?platform=zomato&category=pizza&rate=20"

# Set 15% commission for all Swiggy categories
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/rates?platform=swiggy&category=*&rate=15"
```

---

## 5. Data Models

### 5.1 Payment Record

```typescript
interface PaymentRecord {
  id: string;                    // UUID
  platform: "zomato" | "swiggy" | "blinkit" | "instamart";
  order_id: string;              // Platform-specific order ID
  order_date: string;            // ISO 8601 datetime
  settlement_date: string | null;// When payment was settled
  item_description: string | null;
  item_quantity: number;
  item_price: number;            // Price per unit
  total_price: number;           // Total order value

  // Commission
  expected_commission_rate: number;   // Expected % (e.g., 18.0)
  actual_commission_charged: number;  // What was actually charged
  commission_difference: number;      // Expected - Actual

  // Fee Breakdown
  platform_fee: number;
  delivery_fee: number;
  gst_on_fees: number;
  tds: number;
  other_deductions: number;

  // Settlement
  gross_amount: number;
  total_deductions: number;
  net_settlement: number;

  // Metadata
  fetched_at: string;
  source: "api" | "scrape" | "manual" | "pdf";
}
```

### 5.2 Platform

```typescript
type Platform = "zomato" | "swiggy" | "blinkit" | "instamart";
```

### 5.3 Alert Severity

```typescript
type Severity = "low" | "medium" | "high";

// low:    < 2% of order value
// medium: 2% - 5% of order value
// high:   > 5% of order value
```

### 5.4 Pagination

```typescript
interface Pagination {
  page: number;    // Current page
  limit: number;   // Results per page
  total: number;   // Total results
  pages: number;   // Total pages
}
```

---

## 6. Webhooks

**Status:** Planned (v1.1)

Planned webhook events:

| Event | Trigger |
|-------|---------|
| `sync.completed` | Platform sync finished |
| `alert.detected` | New anomaly detected |
| `sync.failed` | Platform sync failed |

---

## 7. Examples

### Full Workflow Example

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}' \
  http://localhost:8000/api/auth/login | jq -r '.access_token')

# 2. Add Zomato credentials
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "restaurant@email.com", "password": "secret"}' \
  "http://localhost:8000/api/credentials?platform=zomato"

# 3. Trigger sync
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/sync/zomato"

# 4. Check overcharged amount
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/overcharged?start_date=2026-07-01T00:00:00Z&end_date=2026-07-31T23:59:59Z"

# 5. View alerts
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/alerts?platform=zomato"
```

### JavaScript/Fetch Example

```javascript
const API = "http://localhost:8000";
const TOKEN = "your-jwt-token";

async function getPayments(platform, startDate, endDate) {
  const params = new URLSearchParams({
    platform,
    start_date: startDate,
    end_date: endDate,
  });

  const res = await fetch(`${API}/api/payments?${params}`, {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
    },
  });

  if (res.status === 401) {
    // Redirect to login
    window.location.href = "/login";
    return;
  }

  return res.json();
}

// Usage
const data = await getPayments(
  "zomato",
  "2026-07-01T00:00:00Z",
  "2026-07-31T23:59:59Z"
);

console.log(`Found ${data.pagination.total} payments`);
console.log(`Total overcharged: ₹${data.data.reduce((sum, p) => sum + Math.abs(p.commission_difference), 0)}`);
```

### Python/Requests Example

```python
import requests

API = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Get summary
response = requests.get(
    f"{API}/api/summary",
    headers=headers,
    params={
        "start_date": "2026-07-01T00:00:00Z",
        "end_date": "2026-07-31T23:59:59Z",
    },
)

summary = response.json()
for platform in summary:
    print(f"{platform['platform']}: ₹{platform['total_overcharged']:.2f} overcharged")
```

---

## Appendix: Default Commission Rates

| Platform | Default Rate | Range |
|----------|-------------|-------|
| Zomato | 18% | 15-25% |
| Swiggy | 18% | 15-25% |
| Blinkit | 22% | 20-25% |
| Instamart | 18% | 15-25% |

**Note:** Rates can be overridden per platform/category via `POST /api/rates`.

---

*API Version: 1.0.0*
*Last Updated: 2026-07-27*
