# Quick Commerce Commission Tracker

Track and calculate commissions across Indian quick commerce platforms (Zomato, Swiggy, Blinkit, Instamart).

## Features

- Real-time commission tracking
- Anomaly detection (overcharged/undercharged)
- Multi-platform aggregation
- Visual dashboards with Recharts
- Automated data scraping

## Tech Stack

- **Backend**: Python, FastAPI, PostgreSQL, Redis, Playwright
- **Frontend**: Next.js, React, Recharts, Tailwind CSS
- **Auth**: SuperAuth

## Priority Platforms

1. Zomato
2. Swiggy
3. Blinkit
4. Instamart

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn app:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /api/payments` - List payments with filters
- `GET /api/summary` - Commission summary by platform
- `GET /api/alerts` - Commission anomalies
- `GET /api/overcharged` - Total overcharged amount
- `POST /api/sync/{platform}` - Sync data from platform
- `POST /api/credentials` - Save platform credentials

## License

MIT
