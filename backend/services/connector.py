from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from models.payment import PaymentRecord, Platform, PlatformCredential
from scrapers.zomato import ZomatoScraper
from scrapers.swiggy import SwiggyScraper

SCRAPERS = {
    "zomato": ZomatoScraper,
    "swiggy": SwiggyScraper,
    "blinkit": ZomatoScraper,  # Blinkit uses Zomato backend
    "instamart": SwiggyScraper,  # Instamart uses Swiggy backend
}

async def sync_from_api(
    db: AsyncSession,
    user_id,
    platform: Platform,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    # Get credentials
    result = await db.execute(
        select(PlatformCredential).where(
            PlatformCredential.user_id == user_id,
            PlatformCredential.platform == platform,
            PlatformCredential.is_active == True,
        )
    )
    cred = result.scalar_one_or_none()

    if not cred:
        return {"error": "No credentials found"}

    ScraperClass = SCRAPERS.get(platform.value)
    if not ScraperClass:
        return {"error": f"No scraper for {platform.value}"}

    scraper = ScraperClass()
    scrape_result = await scraper.scrape(cred.credentials)

    records_new = 0
    for record in scrape_result.get("records", []):
        existing = await db.execute(
            select(PaymentRecord).where(
                PaymentRecord.user_id == user_id,
                PaymentRecord.platform == platform,
                PaymentRecord.order_id == record["order_id"],
            )
        )
        if existing.scalar_one_or_none():
            continue

        payment = PaymentRecord(
            user_id=user_id,
            platform=platform,
            order_id=record["order_id"],
            order_date=record["order_date"],
            settlement_date=record.get("settlement_date"),
            item_description=record.get("item_description"),
            item_quantity=record.get("item_quantity", 1),
            item_price=record["item_price"],
            total_price=record["total_price"],
            expected_commission_rate=record["expected_commission_rate"],
            actual_commission_charged=record["actual_commission_charged"],
            commission_difference=record["commission_difference"],
            platform_fee=record.get("platform_fee", 0),
            delivery_fee=record.get("delivery_fee", 0),
            gst_on_fees=record.get("gst_on_fees", 0),
            tds=record.get("tds", 0),
            other_deductions=record.get("other_deductions", 0),
            gross_amount=record["gross_amount"],
            total_deductions=record["total_deductions"],
            net_settlement=record["net_settlement"],
            source="scrape",
        )
        db.add(payment)
        records_new += 1

    # Update last sync
    cred.last_sync_at = datetime.utcnow()
    await db.commit()

    return {
        "platform": platform.value,
        "records_found": len(scrape_result.get("records", [])),
        "records_new": records_new,
        "errors": scrape_result.get("errors", []),
    }
