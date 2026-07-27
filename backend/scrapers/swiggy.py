from scrapers.base import BaseScraper
from datetime import datetime
import re

class SwiggyScraper(BaseScraper):
    """
    Swiggy/Instamart Partner Dashboard Scraper

    Flow:
    1. Navigate to partner.swiggy.com
    2. Login with phone + OTP
    3. Navigate to Payments section
    4. Extract payment/settlement data
    """

    LOGIN_URL = "https://partner.swiggy.com"
    PAYMENTS_URL = "https://partner.swiggy.com/payments"

    def __init__(self, headless: bool = True):
        super().__init__("swiggy", headless)

    async def scrape(self, credentials: dict) -> dict:
        records = []
        errors = []
        screenshots = []

        try:
            await self.init()
            if not self.page:
                raise Exception("Page not initialized")

            # Navigate to partner portal
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle")
            screenshots.append(await self.screenshot("login-page"))

            # Login with phone
            phone_input = await self.page.query_selector('input[type="phone"], input[name="phone"]')
            if phone_input and credentials.get("phone"):
                await phone_input.fill(credentials["phone"])
                await self.page.click('button[type="submit"]')

                # Wait for OTP input
                try:
                    await self.page.wait_for_selector('input[name="otp"], input[placeholder*="OTP"]', timeout=30000)
                except:
                    screenshots.append(await self.screenshot("otp-timeout"))
                    return {"records": [], "errors": ["OTP input not found"], "screenshots": screenshots}

                if credentials.get("otp"):
                    await self.page.fill('input[name="otp"], input[placeholder*="OTP"]', credentials["otp"])
                    await self.page.click('button[type="submit"]')
                    await self.page.wait_for_load_state("networkidle")

            # Navigate to payments
            await self.page.goto(self.PAYMENTS_URL, wait_until="networkidle")
            screenshots.append(await self.screenshot("payments-page"))

            # Extract payment data
            payment_data = await self.page.eval_on_selector_all(
                ".payment-card, .settlement-card, .transaction-row, [data-testid*='payment']",
                "elements => elements.map(el => el.textContent.trim())",
            ).catch(lambda _: [])

            if not payment_data:
                errors.append("No payment data found. Swiggy may require PDF statement parsing.")
                screenshots.append(await self.screenshot("no-data"))
            else:
                for data in payment_data:
                    try:
                        record = self._parse_payment_text(data)
                        if record:
                            records.append(record)
                    except Exception as e:
                        errors.append(f"Failed to parse payment: {str(e)}")

        except Exception as e:
            errors.append(f"Scrape failed: {str(e)}")
            if self.page:
                screenshots.append(await self.screenshot("error"))
        finally:
            await self.close()

        return {"records": records, "errors": errors, "screenshots": screenshots}

    def _parse_payment_text(self, text: str) -> dict:
        # Extract order ID
        order_match = re.search(r"Order\s*(?:ID|#)?\s*:?\s*(\w+)", text, re.IGNORECASE)
        # Extract amounts
        amounts = re.findall(r"₹\s*([\d,]+\.?\d*)", text)

        if not order_match or len(amounts) < 2:
            return None

        order_id = order_match.group(1)
        total_price = float(amounts[0].replace(",", ""))
        commission = float(amounts[1].replace(",", ""))

        expected_rate = 18
        expected_commission = (expected_rate / 100) * total_price

        return {
            "order_id": order_id,
            "order_date": datetime.now(),
            "item_description": text[:100],
            "item_quantity": 1,
            "item_price": total_price,
            "total_price": total_price,
            "expected_commission_rate": expected_rate,
            "actual_commission_charged": commission,
            "commission_difference": expected_commission - commission,
            "platform_fee": 0,
            "delivery_fee": 0,
            "gst_on_fees": 0,
            "tds": 0,
            "other_deductions": 0,
            "gross_amount": total_price,
            "total_deductions": commission,
            "net_settlement": total_price - commission,
        }
