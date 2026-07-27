"""
Commission Tracker Backend - Test Suite
Tests all core logic without requiring PostgreSQL.
"""
import sys
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

# ===== Test 1: Commission Calculation Logic =====

def test_commission_calculation():
    """Test core commission calculation"""
    from services.commission import CommissionService

    svc = CommissionService()

    # Test: correct commission
    result = svc.calculate_commission(1000, 18, 180)
    assert result["expected_amount"] == 180.0, f"Expected 180, got {result['expected_amount']}"
    assert result["difference"] == 0.0, f"Expected diff 0, got {result['difference']}"
    assert result["is_overcharged"] == False

    # Test: overcharged
    result = svc.calculate_commission(1000, 18, 200)
    assert result["expected_amount"] == 180.0
    assert result["difference"] == -20.0, f"Expected -20, got {result['difference']}"
    assert result["is_overcharged"] == True

    # Test: undercharged
    result = svc.calculate_commission(1000, 18, 150)
    assert result["expected_amount"] == 180.0
    assert result["difference"] == 30.0, f"Expected 30, got {result['difference']}"
    assert result["is_overcharged"] == False

    # Test: zero price (division by zero guard)
    result = svc.calculate_commission(0, 18, 0)
    assert result["expected_amount"] == 0.0

    print("PASS: Commission calculation logic")

# ===== Test 2: Default Rates =====

def test_default_rates():
    """Test default commission rates"""
    from services.commission import DEFAULT_RATES

    assert DEFAULT_RATES["zomato"] == 18
    assert DEFAULT_RATES["swiggy"] == 18
    assert DEFAULT_RATES["blinkit"] == 22
    assert DEFAULT_RATES["instamart"] == 18

    print("PASS: Default rates")

# ===== Test 3: Scraper Import =====

def test_scraper_imports():
    """Test all scrapers can be imported"""
    from scrapers.base import BaseScraper
    from scrapers.zomato import ZomatoScraper
    from scrapers.swiggy import SwiggyScraper

    z = ZomatoScraper(headless=True)
    assert z.platform == "zomato"
    assert z.headless == True

    s = SwiggyScraper(headless=True)
    assert s.platform == "swiggy"

    print("PASS: Scraper imports")

# ===== Test 4: Zomato Row Parsing =====

def test_zomato_parse_row():
    """Test Zomato scraper row parsing"""
    from scrapers.zomato import ZomatoScraper

    scraper = ZomatoScraper(headless=True)

    # Valid row
    row = ["2026-01-15", "ORD-12345", "Pizza", "₹500.00", "₹90.00", "₹410.00"]
    record = scraper._parse_row(row)
    assert record is not None
    assert record["order_id"] == "ORD-12345"
    assert record["total_price"] == 500.0
    assert record["actual_commission_charged"] == 90.0
    assert record["expected_commission_rate"] == 18
    assert record["commission_difference"] == 0.0  # 18% of 500 = 90

    # Header row (should be skipped)
    header = ["Date", "Order ID", "Item", "Amount", "Commission", "Net"]
    assert scraper._parse_row(header) is None

    # Too few cells
    short = ["2026-01-15", "ORD-12345"]
    assert scraper._parse_row(short) is None

    print("PASS: Zomato row parsing")

# ===== Test 5: Swiggy Payment Parsing =====

def test_swiggy_parse_payment():
    """Test Swiggy scraper text parsing"""
    from scrapers.swiggy import SwiggyScraper

    scraper = SwiggyScraper(headless=True)

    # Valid payment text
    text = "Order #SW12345: ₹1000.00 commission ₹180.00 net ₹820.00"
    record = scraper._parse_payment_text(text)
    assert record is not None
    assert record["order_id"] == "SW12345"
    assert record["total_price"] == 1000.0
    assert record["actual_commission_charged"] == 180.0

    # No amounts
    text2 = "No payment info here"
    assert scraper._parse_payment_text(text2) is None

    print("PASS: Swiggy payment parsing")

# ===== Test 6: Connector Scraper Mapping =====

def test_connector_mapping():
    """Test scraper mapping"""
    from services.connector import SCRAPERS
    from scrapers.zomato import ZomatoScraper
    from scrapers.swiggy import SwiggyScraper

    assert SCRAPERS["zomato"] == ZomatoScraper
    assert SCRAPERS["swiggy"] == SwiggyScraper
    assert SCRAPERS["blinkit"] == ZomatoScraper
    assert SCRAPERS["instamart"] == SwiggyScraper

    print("PASS: Connector scraper mapping")

# ===== Test 7: Settings Validation =====

def test_settings():
    """Test settings loads correctly"""
    import os
    os.environ["JWT_SECRET"] = "test-secret-for-validation"

    # Re-import to pick up env
    import importlib
    import config.settings
    importlib.reload(config.settings)

    s = config.settings.settings
    assert s.JWT_SECRET == "test-secret-for-validation"
    assert s.JWT_ALGORITHM == "HS256"
    assert s.PORT == 8000

    print("PASS: Settings validation")

# ===== Test 8: Model Schema =====

def test_models():
    """Test model definitions"""
    from models.payment import Platform, DataSource, User, PaymentRecord, PlatformCredential, CommissionRate, ScrapeJob

    # Test enum values
    assert Platform.zomato.value == "zomato"
    assert Platform.swiggy.value == "swiggy"
    assert Platform.blinkit.value == "blinkit"
    assert Platform.instamart.value == "instamart"

    assert DataSource.api.value == "api"
    assert DataSource.scrape.value == "scrape"
    assert DataSource.manual.value == "manual"
    assert DataSource.pdf.value == "pdf"

    # Test table names
    assert User.__tablename__ == "users"
    assert PaymentRecord.__tablename__ == "payment_records"
    assert PlatformCredential.__tablename__ == "platform_credentials"
    assert CommissionRate.__tablename__ == "commission_rates"
    assert ScrapeJob.__tablename__ == "scrape_jobs"

    print("PASS: Model schema")

# ===== Test 9: Route Definitions =====

def test_routes():
    """Test API routes are properly defined"""
    from api.routes import router

    route_paths = [r.path for r in router.routes]

    assert "/payments" in route_paths
    assert "/summary" in route_paths
    assert "/alerts" in route_paths
    assert "/overcharged" in route_paths
    assert "/credentials" in route_paths
    assert "/rates" in route_paths

    print("PASS: Route definitions")

# ===== Test 10: Analyze Records =====

def test_analyze_records():
    """Test anomaly detection"""
    from services.commission import CommissionService
    from unittest.mock import MagicMock

    svc = CommissionService()

    # Create mock records
    record1 = MagicMock()
    record1.platform = "zomato"
    record1.order_id = "ORD-001"
    record1.total_price = 1000
    record1.expected_commission_rate = 18
    record1.actual_commission_charged = 180  # Correct

    record2 = MagicMock()
    record2.platform = "swiggy"
    record2.order_id = "ORD-002"
    record2.total_price = 1000
    record2.expected_commission_rate = 18
    record2.actual_commission_charged = 250  # Overcharged!

    record3 = MagicMock()
    record3.platform = "blinkit"
    record3.order_id = "ORD-003"
    record3.total_price = 0  # Zero price — should be skipped
    record3.expected_commission_rate = 22
    record3.actual_commission_charged = 0

    alerts = asyncio.get_event_loop().run_until_complete(
        svc.analyze_records([record1, record2, record3])
    )

    # record1: 180 vs expected 180 → no alert (diff = 0)
    # record2: 250 vs expected 180 → alert (diff = -70)
    # record3: skipped (zero price)

    assert len(alerts) == 1, f"Expected 1 alert, got {len(alerts)}"
    assert alerts[0]["order_id"] == "ORD-002"
    assert alerts[0]["severity"] == "high"
    assert alerts[0]["difference"] == -70.0

    print("PASS: Analyze records (anomaly detection)")

# ===== Test 11: Auth Middleware =====

def test_auth_middleware():
    """Test auth helper exists and has correct signature"""
    from api.routes import get_current_user
    import inspect

    sig = inspect.signature(get_current_user)
    params = list(sig.parameters.keys())
    assert "authorization" in params
    assert "db" in params

    print("PASS: Auth middleware")

# ===== Test 12: Frontend API Helper =====

def test_frontend_api_helper():
    """Test frontend has auth token handling"""
    with open("frontend/src/app/page.tsx", "r") as f:
        content = f.read()

    assert "getAuthToken" in content
    assert "Authorization" in content
    assert "Bearer" in content
    assert "401" in content

    print("PASS: Frontend auth integration")


# ===== Run All Tests =====

if __name__ == "__main__":
    print("=" * 50)
    print("Commission Tracker Backend - Test Suite")
    print("=" * 50)
    print()

    tests = [
        test_commission_calculation,
        test_default_rates,
        test_scraper_imports,
        test_zomato_parse_row,
        test_swiggy_parse_payment,
        test_connector_mapping,
        test_settings,
        test_models,
        test_routes,
        test_analyze_records,
        test_auth_middleware,
        test_frontend_api_helper,
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
