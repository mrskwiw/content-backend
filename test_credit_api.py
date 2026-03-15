#!/usr/bin/env python
"""Test credit system API endpoints."""
import sys
import requests
import json

BASE_URL = "http://localhost:8000"

def test_packages():
    """Test GET /api/credits/packages"""
    print("=" * 60)
    print("Testing: GET /api/credits/packages")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/api/credits/packages", timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            packages = response.json()
            print(f"\n[OK] Found {len(packages)} credit packages:\n")

            # Group by type
            standard = [p for p in packages if p["package_type"] == "package"]
            additional = [p for p in packages if p["package_type"] == "additional"]

            print("Standard Packages ($2/credit):")
            for pkg in standard:
                rate = pkg["price_usd"] / pkg["credits"]
                print(f"  • {pkg['name']}: {pkg['credits']} credits = ${pkg['price_usd']:.2f} (${rate:.2f}/credit)")

            print("\nAdditional Credits ($2.50/credit):")
            for pkg in additional:
                rate = pkg["price_usd"] / pkg["credits"]
                print(f"  • {pkg['name']}: {pkg['credits']} credits = ${pkg['price_usd']:.2f} (${rate:.2f}/credit)")

            return True
        else:
            print(f"[FAIL] Error: {response.status_code}")
            print(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("[FAIL] Backend not running!")
        print("Start it with: python -m uvicorn backend.main:app --reload")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_research_tools():
    """Test GET /api/research/tools"""
    print("\n" + "=" * 60)
    print("Testing: GET /api/research/tools (credit costs)")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/api/research/tools", timeout=5)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            tools = response.json()
            print(f"\n[OK] Found {len(tools)} research tools:\n")

            for tool in tools:
                credits = tool.get("credits", 0)
                print(f"  • {tool['label']}: {credits} credits")

            return True
        else:
            print(f"[FAIL] Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


if __name__ == "__main__":
    print("\nCredit System API Tests\n")

    results = []
    results.append(("Credit Packages", test_packages()))
    results.append(("Research Tools", test_research_tools()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n[OK] All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
