from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict
from datetime import datetime
from models.payment import PaymentRecord, Platform

DEFAULT_RATES = {
    "zomato": 18,
    "swiggy": 18,
    "blinkit": 22,
    "instamart": 18,
}

class CommissionService:
    async def get_expected_rate(
        self, db: AsyncSession, platform: Platform, category: str = "*"
    ) -> float:
        # Check custom rates first
        from models.payment import CommissionRate
        result = await db.execute(
            select(CommissionRate)
            .where(
                CommissionRate.platform == platform,
                CommissionRate.category.in_([category, "*"]),
                CommissionRate.effective_from <= datetime.utcnow(),
            )
            .order_by(CommissionRate.effective_from.desc())
            .limit(1)
        )
        custom_rate = result.scalar_one_or_none()
        if custom_rate:
            return custom_rate.base_rate

        return DEFAULT_RATES.get(platform.value, 15)

    def calculate_commission(
        self, total_price: float, expected_rate: float, actual_charged: float
    ) -> dict:
        expected_amount = (expected_rate / 100) * total_price
        difference = expected_amount - actual_charged
        return {
            "expected_amount": expected_amount,
            "difference": difference,
            "is_overcharged": difference < 0,
        }

    async def analyze_records(
        self, records: List[PaymentRecord]
    ) -> List[dict]:
        alerts = []
        for record in records:
            expected_rate = DEFAULT_RATES.get(record.platform, 15)
            result = self.calculate_commission(
                record.total_price, expected_rate, record.actual_commission_charged
            )

            diff_percent = abs(result["difference"]) / record.total_price * 100
            severity = "low"
            if diff_percent > 5:
                severity = "high"
            elif diff_percent > 2:
                severity = "medium"

            if abs(result["difference"]) > 1:
                alerts.append({
                    "platform": record.platform,
                    "order_id": record.order_id,
                    "expected": result["expected_amount"],
                    "actual": record.actual_commission_charged,
                    "difference": result["difference"],
                    "severity": severity,
                    "message": (
                        f"Overcharged by ₹{abs(result['difference']):.2f} ({diff_percent:.1f}% of order)"
                        if result["is_overcharged"]
                        else f"Undercharged by ₹{result['difference']:.2f} ({diff_percent:.1f}% of order)"
                    ),
                })

        return sorted(alerts, key=lambda x: abs(x["difference"]), reverse=True)

    async def get_summary(
        self,
        db: AsyncSession,
        user_id,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[Platform] = None,
    ) -> List[dict]:
        query = """
            SELECT
                platform,
                DATE_TRUNC('month', order_date) AS period,
                COUNT(*) AS total_orders,
                SUM(total_price) AS total_sales,
                SUM(actual_commission_charged) AS total_commission_charged,
                SUM(expected_commission_rate * total_price / 100) AS total_commission_expected,
                SUM(commission_difference) AS total_overcharged,
                AVG(actual_commission_charged / NULLIF(total_price, 0) * 100) AS avg_commission_rate,
                SUM(net_settlement) AS net_settled
            FROM payment_records
            WHERE user_id = :user_id
            AND order_date >= :start_date
            AND order_date <= :end_date
        """
        params = {"user_id": user_id, "start_date": start_date, "end_date": end_date}

        if platform:
            query += " AND platform = :platform"
            params["platform"] = platform.value

        query += " GROUP BY platform, DATE_TRUNC('month', order_date) ORDER BY period DESC"

        result = await db.execute(query, params)
        rows = result.fetchall()

        return [
            {
                "platform": row[0],
                "period": str(row[1]),
                "total_orders": row[2],
                "total_sales": float(row[3] or 0),
                "total_commission_charged": float(row[4] or 0),
                "total_commission_expected": float(row[5] or 0),
                "total_overcharged": float(row[6] or 0),
                "avg_commission_rate": float(row[7] or 0),
                "net_settled": float(row[8] or 0),
            }
            for row in rows
        ]

    async def get_total_overcharged(
        self, db: AsyncSession, user_id, start_date: datetime, end_date: datetime
    ) -> dict:
        query = """
            SELECT
                platform,
                SUM(commission_difference) AS overcharged
            FROM payment_records
            WHERE user_id = :user_id
            AND order_date >= :start_date
            AND order_date <= :end_date
            GROUP BY platform
        """
        result = await db.execute(query, {"user_id": user_id, "start_date": start_date, "end_date": end_date})
        rows = result.fetchall()

        by_platform = {}
        total = 0
        for row in rows:
            amount = abs(float(row[1] or 0))
            by_platform[row[0]] = amount
            total += amount

        return {"total_overcharged": total, "by_platform": by_platform}

    async def add_custom_rate(
        self,
        db: AsyncSession,
        platform: Platform,
        category: str,
        rate: float,
        effective_from: Optional[datetime] = None,
    ):
        from models.payment import CommissionRate
        new_rate = CommissionRate(
            platform=platform,
            category=category,
            base_rate=rate,
            effective_from=effective_from or datetime.utcnow(),
        )
        db.add(new_rate)
        await db.commit()
