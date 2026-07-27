from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional
from models.payment import PaymentRecord, Platform, PlatformCredential
from scrapers.zomato import ZomatoScraper
from scrapers.swiggy import SwiggyScraper

SCRAPERS = {
    "zomato": ZomatoScraper,
    "swiggy": SwiggyScraper,
    "blinkit": ZomatoScraper,
    "instamart": SwiggyScraper,
}

# FIX #6: Robust error handling — don't save partial data on scraper failure
async def sync_from_api(
    db: AsyncSession,
    user_id,
    platform: Platform,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    result = await db.execute(
        select(PlatformCredential).where(
            PlatformCredential.user_id == user_id,
            PlatformCredential.platform == platform,
            PlatformCredential.is_active == True,
        )
    )
    cred = result.scalar_one_or_none()

    if not cred:
        return {"error": "No credentials found", "platform": platform.value}

    ScraperClass = SCRAPERS.get(platform.value)
    if not ScraperClass:
        return {"error": f"No scraper for {platform.value}", "platform": platform.value}

    try:
        scraper = ScraperClass()
        scrape_result = await scraper.scrape(cred.credentials)
    except Exception as e:
        return {
            "error": f"Scraper crashed: {str(e)}",
            "platform": platform.value,
            "records_found": 0,
            "records_new": 0,
        }

    # Check if scraper reported errors
    if scrape_result.get("errors") and not scrape_result.get("records"):
        cred.last_sync_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "platform": platform.value,
            "records_found": 0,
            "records_new": 0,
            "errors": scrape_result["errors"],
        }

    records_new = 0
    records_skipped = 0
    errors = []

    for record in scrape_result.get("records", []):
        try:
            # Check for existing record
            existing = await db.execute(
                select(PaymentRecord).where(
                    PaymentRecord.user_id == user_id,
                    PaymentRecord.platform == platform,
                    PaymentRecord.order_id == record["order_id"],
                )
            )
            if existing.scalar_one_or_none():
                records_skipped += 1
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
        except Exception as e:
            errors.append(f"Failed to save record {record.get('order_id')}: {str(e)}")

    # Only commit if we have new records
    if records_new > 0:
        await db.commit()

    # Update last sync even if no new records (successful scrape)
    cred.last_sync_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "platform": platform.value,
        "records_found": len(scrape_result.get("records", [])),
        "records_new": records_new,
        "records_skipped": records_skipped,
        "errors": errors + scrape_result.get("errors", []),
    }
