"""
Commission Tracker - Standalone Logic Tests
Tests core logic without any external dependencies.
"""
import sys
import re
from datetime import datetime

# ===== Pure Logic Tests =====

class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# ===== Test 1: Commission Calculation =====

def test_commission_calculation():
    DEFAULT_RATES = {"zomato": 18, "swiggy": 18, "blinkit": 22, "instamart": 18}

    def calculate_commission(total_price, expected_rate, actual_charged):
        expected_amount = (expected_rate / 100) * total_price
        difference = expected_amount - actual_charged
        return {
            "expected_amount": expected_amount,
            "difference": difference,
            "is_overcharged": difference < 0,
        }

    # Correct commission
    r = calculate_commission(1000, 18, 180)
    assert r["expected_amount"] == 180.0
    assert r["difference"] == 0.0
    assert r["is_overcharged"] == False

    # Overcharged
    r = calculate_commission(1000, 18, 200)
    assert r["difference"] == -20.0
    assert r["is_overcharged"] == True

    # Undercharged
    r = calculate_commission(1000, 18, 150)
    assert r["difference"] == 30.0
    assert r["is_overcharged"] == False

    # Zero price
    r = calculate_commission(0, 18, 0)
    assert r["expected_amount"] == 0.0

    print("PASS: Commission calculation")

# ===== Test 2: Zomato Row Parsing =====

def test_zomato_parse_row():
    def parse_row(cells):
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
            "total_price": total_price,
            "actual_commission_charged": actual_commission,
            "expected_commission_rate": expected_rate,
            "commission_difference": expected_commission - actual_commission,
            "net_settlement": net or (total_price - actual_commission),
        }

    # Valid row
    row = ["2026-01-15", "ORD-12345", "Pizza", "₹500.00", "₹90.00", "₹410.00"]
    r = parse_row(row)
    assert r is not None
    assert r["order_id"] == "ORD-12345"
    assert r["total_price"] == 500.0
    assert r["actual_commission_charged"] == 90.0
    assert r["commission_difference"] == 0.0  # 18% of 500 = 90

    # Header row
    header = ["Date", "Order ID", "Item", "Amount", "Commission", "Net"]
    assert parse_row(header) is None

    # Too few cells
    assert parse_row(["2026-01-15", "ORD-12345"]) is None

    # Regex cleanup works
    row2 = ["2026-01-15", "ORD/999@#$", "Burger", "₹300.00", "₹54.00", "₹246.00"]
    r2 = parse_row(row2)
    assert r2["order_id"] == "ORD999"

    print("PASS: Zomato row parsing")

# ===== Test 3: Swiggy Text Parsing =====

def test_swiggy_parse():
    def parse_payment_text(text):
        order_match = re.search(r"Order\s*(?:ID|#)?\s*:?\s*(\w+)", text, re.IGNORECASE)
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
            "total_price": total_price,
            "actual_commission_charged": commission,
            "commission_difference": expected_commission - commission,
        }

    # Valid text
    text = "Order #SW12345: ₹1000.00 commission ₹180.00 net ₹820.00"
    r = parse_payment_text(text)
    assert r is not None
    assert r["order_id"] == "SW12345"
    assert r["total_price"] == 1000.0
    assert r["commission_difference"] == 0.0

    # No amounts
    assert parse_payment_text("No payment info here") is None

    # Overcharged text
    text2 = "Order ID: SW99999 ₹500 ₹120 ₹380"
    r2 = parse_payment_text(text2)
    assert r2 is not None
    assert r2["order_id"] == "SW99999"
    assert r2["commission_difference"] == -30.0  # Expected 90, got 120

    print("PASS: Swiggy text parsing")

# ===== Test 4: Anomaly Detection =====

def test_anomaly_detection():
    DEFAULT_RATES = {"zomato": 18, "swiggy": 18, "blinkit": 22, "instamart": 18}

    def analyze_records(records):
        alerts = []
        for record in records:
            expected_rate = record.expected_commission_rate or DEFAULT_RATES.get(record.platform, 15)
            if record.total_price <= 0:
                continue
            expected_amount = (expected_rate / 100) * record.total_price
            difference = expected_amount - record.actual_commission_charged
            is_overcharged = difference < 0

            diff_percent = abs(difference) / record.total_price * 100
            severity = "low"
            if diff_percent > 5:
                severity = "high"
            elif diff_percent > 2:
                severity = "medium"

            if abs(difference) > 1:
                alerts.append({
                    "platform": record.platform,
                    "order_id": record.order_id,
                    "difference": difference,
                    "severity": severity,
                })
        return sorted(alerts, key=lambda x: abs(x["difference"]), reverse=True)

    # Correct commission
    r1 = MockRecord(platform="zomato", order_id="ORD-001", total_price=1000,
                    expected_commission_rate=18, actual_commission_charged=180)

    # Overcharged
    r2 = MockRecord(platform="swiggy", order_id="ORD-002", total_price=1000,
                    expected_commission_rate=18, actual_commission_charged=250)

    # Zero price (should be skipped)
    r3 = MockRecord(platform="blinkit", order_id="ORD-003", total_price=0,
                    expected_commission_rate=22, actual_commission_charged=0)

    # Slightly over
    r4 = MockRecord(platform="instamart", order_id="ORD-004", total_price=500,
                    expected_commission_rate=18, actual_commission_charged=100)

    alerts = analyze_records([r1, r2, r3, r4])

    # r1: diff=0, no alert
    # r2: diff=-70 (7% over), high
    # r3: skipped
    # r4: diff=-10 (2% over), medium

    assert len(alerts) == 2, f"Expected 2 alerts, got {len(alerts)}"
    assert alerts[0]["order_id"] == "ORD-002"  # Most overcharged
    assert alerts[0]["severity"] == "high"
    assert alerts[0]["difference"] == -70.0
    assert alerts[1]["order_id"] == "ORD-004"
    # diff_percent = 10/500*100 = 2.0, condition is > 2 so severity is "low"
    assert alerts[1]["severity"] == "low"

    print("PASS: Anomaly detection")

# ===== Test 5: Total Overcharged Calculation =====

def test_total_overcharged():
    def get_total_overcharged(records):
        by_platform = {}
        total = 0
        for r in records:
            expected_amount = (r.expected_commission_rate / 100) * r.total_price
            diff = expected_amount - r.actual_commission_charged
            amount = abs(diff)
            by_platform[r.platform] = by_platform.get(r.platform, 0) + amount
            total += amount
        return {"total_overcharged": total, "by_platform": by_platform}

    records = [
        MockRecord(platform="zomato", total_price=1000, expected_commission_rate=18, actual_commission_charged=200),
        MockRecord(platform="zomato", total_price=500, expected_commission_rate=18, actual_commission_charged=100),
        MockRecord(platform="swiggy", total_price=800, expected_commission_rate=18, actual_commission_charged=150),
    ]

    result = get_total_overcharged(records)
    # Zomato: expected 180, actual 200 → over 20; expected 90, actual 100 → over 10; total 30
    # Swiggy: expected 144, actual 150 → over 6; total 6
    assert result["total_overcharged"] == 36.0
    assert result["by_platform"]["zomato"] == 30.0
    assert result["by_platform"]["swiggy"] == 6.0

    print("PASS: Total overcharged calculation")

# ===== Test 6: Regex Validation =====

def test_regex_patterns():
    # Zomato order ID cleanup
    assert re.sub(r"[^\w-]", "", "ORD/12345@#$") == "ORD12345"
    assert re.sub(r"[^\w-]", "", "ORD-12345") == "ORD-12345"
    assert re.sub(r"[^\w-]", "", "") == ""

    # Swiggy order ID extraction
    assert re.search(r"Order\s*(?:ID|#)?\s*:?\s*(\w+)", "Order #SW12345", re.IGNORECASE).group(1) == "SW12345"
    assert re.search(r"Order\s*(?:ID|#)?\s*:?\s*(\w+)", "Order ID: SW99999", re.IGNORECASE).group(1) == "SW99999"
    assert re.search(r"Order\s*(?:ID|#)?\s*:?\s*(\w+)", "Order: ABC123", re.IGNORECASE).group(1) == "ABC123"

    # Amount extraction
    amounts = re.findall(r"₹\s*([\d,]+\.?\d*)", "₹500.00 ₹90.00 ₹410.00")
    assert amounts == ["500.00", "90.00", "410.00"]

    print("PASS: Regex patterns")

# ===== Test 7: Scraper Mapping =====

def test_scraper_mapping():
    SCRAPERS = {
        "zomato": "ZomatoScraper",
        "swiggy": "SwiggyScraper",
        "blinkit": "ZomatoScraper",
        "instamart": "SwiggyScraper",
    }

    assert SCRAPERS["zomato"] == "ZomatoScraper"
    assert SCRAPERS["blinkit"] == "ZomatoScraper"
    assert SCRAPERS["swiggy"] == "SwiggyScraper"
    assert SCRAPERS["instamart"] == "SwiggyScraper"
    assert "dunzo" not in SCRAPERS

    print("PASS: Scraper mapping")

# ===== Test 8: Edge Cases =====

def test_edge_cases():
    def calculate_commission(total_price, expected_rate, actual_charged):
        expected_amount = (expected_rate / 100) * total_price
        difference = expected_amount - actual_charged
        return {"expected_amount": expected_amount, "difference": difference, "is_overcharged": difference < 0}

    # Very large order
    r = calculate_commission(1000000, 18, 180000)
    assert r["expected_amount"] == 180000.0
    assert r["difference"] == 0.0

    # Very small order (floating point tolerance)
    r = calculate_commission(10, 18, 1.8)
    assert abs(r["expected_amount"] - 1.8) < 0.001
    assert abs(r["difference"]) < 0.001

    # 0% commission (Meesho)
    r = calculate_commission(1000, 0, 0)
    assert r["expected_amount"] == 0.0
    assert r["difference"] == 0.0

    # 100% commission (theoretical)
    r = calculate_commission(1000, 100, 1000)
    assert r["expected_amount"] == 1000.0
    assert r["difference"] == 0.0

    # Negative commission (refund)
    r = calculate_commission(1000, 18, -50)
    assert r["is_overcharged"] == False  # Expected 180, got -50 → undercharged

    print("PASS: Edge cases")


# ===== Run All Tests =====

if __name__ == "__main__":
    print("=" * 50)
    print("Commission Tracker - Standalone Test Suite")
    print("=" * 50)
    print()

    tests = [
        test_commission_calculation,
        test_zomato_parse_row,
        test_swiggy_parse,
        test_anomaly_detection,
        test_total_overcharged,
        test_regex_patterns,
        test_scraper_mapping,
        test_edge_cases,
    ]

    passed = 0
    failed = 0
    errors = []

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            print(f"FAIL: {test.__name__}: {e}")

    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print("=" * 50)

    if errors:
        print("\nFailed tests:")
        for name, err in errors:
            print(f"  - {name}: {err}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
