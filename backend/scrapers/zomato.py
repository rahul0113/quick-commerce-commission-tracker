import re
from scrapers.base import BaseScraper
from datetime import datetime

class ZomatoScraper(BaseScraper):
    LOGIN_URL = "https://business.zomato.com"
    PAYMENTS_URL = "https://business.zomato.com/payments"

    def __init__(self, headless: bool = True):
        super().__init__("zomato", headless)

    async def scrape(self, credentials: dict) -> dict:
        records = []
        errors = []
        screenshots = []

        try:
            await self.init()
            if not self.page:
                raise Exception("Page not initialized")

            await self.page.goto(self.LOGIN_URL, wait_until="networkidle")
            screenshots.append(await self.screenshot("login-page"))

            logged_in = await self.page.query_selector(".dashboard-content, .orders-section")

            if not logged_in and credentials.get("email"):
                await self.page.fill('input[type="email"], input[name="email"]', credentials["email"])
                await self.page.fill('input[type="password"], input[name="password"]', credentials["password"])
                await self.page.click('button[type="submit"]')
                await self.page.wait_for_load_state("networkidle")
                screenshots.append(await self.screenshot("after-login"))

                otp_input = await self.page.query_selector('input[name="otp"], input[placeholder*="OTP"]')
                if otp_input and credentials.get("otp"):
                    await otp_input.fill(credentials["otp"])
                    await self.page.click('button[type="submit"]')
                    await self.page.wait_for_load_state("networkidle")

            await self.page.goto(self.PAYMENTS_URL, wait_until="networkidle")
            try:
                await self.page.wait_for_selector(".payment-list, .settlement-list, table", timeout=10000)
            except Exception:
                screenshots.append(await self.screenshot("no-payment-data"))
                return {"records": [], "errors": ["Could not find payment data"], "screenshots": screenshots}

            screenshots.append(await self.screenshot("payments-page"))

            rows = await self.page.eval_on_selector_all(
                ".payment-row, .settlement-row, table tbody tr",
                """rows => rows.map(row => {
                    const cells = row.querySelectorAll('td, .cell');
                    return Array.from(cells).map(cell => cell.textContent.trim());
                })""",
            )

            for row in rows:
                try:
                    record = self._parse_row(row)
                    if record:
                        records.append(record)
                except Exception as e:
                    errors.append(f"Failed to parse row: {str(e)}")

        except Exception as e:
            errors.append(f"Scrape failed: {str(e)}")
            if self.page:
                screenshots.append(await self.screenshot("error"))
        finally:
            await self.close()

        return {"records": records, "errors": errors, "screenshots": screenshots}

    # FIX #8: Use re.sub() for proper regex replacement
    def _parse_row(self, cells: list) -> dict:
        if len(cells) < 5:
            return None

        date_str, order_id, item, amount, commission, net_payable = cells[:6]

        if not order_id or order_id == "Order ID":
            return None

        total_price = float(amount.replace("₹", "").replace(",", "") or "0")
        actual_commission = float(commission.replace("₹", "").replace(",", "") or "0")
        net = float(net_payable.replace("₹", "").replace(",", "") or "0")

        expected_rate = 18
        expected_commission = (expected_rate / 100) * total_price

        return {
            "order_id": re.sub(r"[^\w-]", "", order_id),
            "order_date": datetime.now(),
            "item_description": item,
            "item_quantity": 1,
            "item_price": total_price,
            "total_price": total_price,
            "expected_commission_rate": expected_rate,
            "actual_commission_charged": actual_commission,
            "commission_difference": expected_commission - actual_commission,
            "platform_fee": 0,
            "delivery_fee": 0,
            "gst_on_fees": 0,
            "tds": 0,
            "other_deductions": 0,
            "gross_amount": total_price,
            "total_deductions": actual_commission,
            "net_settlement": net or (total_price - actual_commission),
        }
