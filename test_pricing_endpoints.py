"""
Quick test script to verify pricing endpoints work correctly.

Tests the simplified $40/post pricing model (no preset packages).
"""
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.pricing import (
    PricingConfig,
    calculate_price,
    calculate_price_from_quantities,
)


def test_pricing_config():
    """Test pricing configuration"""
    print("\n=== Testing Pricing Configuration ===")
    config = PricingConfig()
    print(f"✓ Price per post: ${config.PRICE_PER_POST}")
    print(f"✓ Research price per post: ${config.RESEARCH_PRICE_PER_POST} (DEPRECATED - Bug #43)")
    print(f"✓ Min posts: {config.MIN_POSTS}")
    print(f"✓ Max posts: {config.MAX_POSTS}")
    print(f"✓ Unlimited revisions: {config.UNLIMITED_REVISIONS}")
    assert config.PRICE_PER_POST == 40.0
    assert config.RESEARCH_PRICE_PER_POST == 0.0  # DEPRECATED (Bug #43): was 15.0
    assert config.UNLIMITED_REVISIONS == True
    print("✓ All pricing config tests passed!")


def test_price_calculations():
    """Test price calculation functions"""
    print("\n=== Testing Price Calculations ===")

    # Test 1: 10 posts, no research
    price1 = calculate_price(10, research_per_post=False)
    assert price1 == 400.0  # 10 * 40
    print(f"✓ 10 posts, no research: ${price1}")

    # Test 2: 30 posts, no research
    price2 = calculate_price(30, research_per_post=False)
    assert price2 == 1200.0  # 30 * 40
    print(f"✓ 30 posts, no research: ${price2}")

    # Test 3: 30 posts, with research (DEPRECATED - Bug #43)
    price3 = calculate_price(30, research_per_post=True)
    assert price3 == 1200.0  # 30 * 40 (research addon deprecated, was 1650)
    print(f"✓ 30 posts, with research: ${price3} (research addon DEPRECATED)")

    # Test 4: 50 posts, with research (DEPRECATED - Bug #43)
    price4 = calculate_price(50, research_per_post=True)
    assert price4 == 2000.0  # 50 * 40 (research addon deprecated, was 2750)
    print(f"✓ 50 posts, with research: ${price4} (research addon DEPRECATED)")

    # Test 5: 100 posts, no research
    price5 = calculate_price(100, research_per_post=False)
    assert price5 == 4000.0  # 100 * 40
    print(f"✓ 100 posts, no research: ${price5}")

    # Test 6: 100 posts, with research (DEPRECATED - Bug #43)
    price6 = calculate_price(100, research_per_post=True)
    assert price6 == 4000.0  # 100 * 40 (research addon deprecated, was 5500)
    print(f"✓ 100 posts, with research: ${price6} (research addon DEPRECATED)")

    print("✓ All price calculation tests passed!")


def test_template_quantities_calculations():
    """Test calculate_price_from_quantities function"""
    print("\n=== Testing Template Quantities Calculations ===")

    # Test 1: Calculate from template quantities (10 posts, no research)
    quantities1 = {1: 3, 2: 5, 9: 2}  # 10 total posts
    price1 = calculate_price_from_quantities(quantities1, research_per_post=False)
    assert price1 == 400.0  # 10 * 40
    print(f"✓ Custom quantities (10 posts), no research: ${price1}")

    # Test 2: Custom quantities with research (10 posts) - DEPRECATED (Bug #43)
    price2 = calculate_price_from_quantities(quantities1, research_per_post=True)
    assert price2 == 400.0  # 10 * 40 (research addon deprecated, was 550)
    print(f"✓ Custom quantities (10 posts), with research: ${price2} (research addon DEPRECATED)")

    # Test 3: Larger custom order (30 posts)
    quantities2 = {1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 9: 5}  # 30 total
    price3 = calculate_price_from_quantities(quantities2, research_per_post=False)
    assert price3 == 1200.0  # 30 * 40
    print(f"✓ Custom quantities (30 posts), no research: ${price3}")

    # Test 4: Empty quantities
    price4 = calculate_price_from_quantities({}, research_per_post=False)
    assert price4 == 0.0
    print(f"✓ Empty quantities: ${price4}")

    print("✓ All template quantities calculation tests passed!")


def test_common_scenarios():
    """Test common pricing scenarios"""
    print("\n=== Testing Common Pricing Scenarios ===")

    # Scenario 1: Small trial (10 posts)
    price1 = calculate_price(10, research_per_post=False)
    print(f"✓ Small trial (10 posts): ${price1}")
    assert price1 == 400.0

    # Scenario 2: Monthly content (30 posts)
    price2 = calculate_price(30, research_per_post=False)
    print(f"✓ Monthly content (30 posts): ${price2}")
    assert price2 == 1200.0

    # Scenario 3: Monthly content with research (DEPRECATED - Bug #43)
    price3 = calculate_price(30, research_per_post=True)
    print(f"✓ Monthly content with research (30 posts): ${price3}")
    assert price3 == 1200.0  # Research addon deprecated, was 1650

    # Scenario 4: Quarterly bank (100 posts)
    price4 = calculate_price(100, research_per_post=False)
    print(f"✓ Quarterly bank (100 posts): ${price4}")
    assert price4 == 4000.0

    # Scenario 5: Single post
    price5 = calculate_price(1, research_per_post=False)
    print(f"✓ Single post: ${price5}")
    assert price5 == 40.0

    print("✓ All common scenario tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("PRICING ENDPOINT VERIFICATION")
    print("=" * 60)

    try:
        test_pricing_config()
        test_price_calculations()
        test_template_quantities_calculations()
        test_common_scenarios()

        print("\n" + "=" * 60)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 60)
        print("\nPricing model: $40/post (research add-on DEPRECATED - Bug #43)")
        print("Research tools: $300-$600 per tool (see src/config/pricing.py)")
        print("\nAvailable endpoints:")
        print("  - GET /api/pricing/config")
        print("  - GET /api/pricing/calculate?num_posts=30&research=false")
        print("  - POST /api/pricing/calculate")
        print("  - POST /api/pricing/calculate-from-quantities")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
