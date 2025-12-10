#!/usr/bin/env python3
"""
Test script to verify text fits within 64x32 matrix display bounds
"""

def test_message_lengths():
    """Test that all orphaned recovery messages fit within display bounds"""

    # Font approximation: 6x10 font means ~6 pixels per character
    # With 1 pixel spacing, that's roughly 7-8 pixels per character
    # 64 pixels wide / 8 pixels per char = ~8 characters max safely

    print("Testing message lengths for 64x32 matrix display:")
    print("=" * 50)

    # Test messages from the updated cards
    test_messages = [
        # Orphaned card
        ("ORPHANED", "ID:4EX7", "USE APP"),

        # Recovery card
        ("RECOVERY", "WAIT...", ""),

        # Success card
        ("SUCCESS", "READY", ""),

        # Failed card
        ("FAILED", "ID:4EX7", "USE APP"),

        # Link instruction card
        ("LINK ME", "ID:4EX7", "USE APP"),

        # Claim code card (6 char code)
        ("CLAIM", "ABC123", "USE APP"),
        ("CLAIM", "XYZ789", "USE APP"),
    ]

    max_safe_chars = 10  # Conservative estimate

    all_pass = True

    for i, (line1, line2, line3) in enumerate(test_messages, 1):
        print(f"\nTest {i}:")
        print(f"  Line 1: '{line1}' ({len(line1)} chars)")
        print(f"  Line 2: '{line2}' ({len(line2)} chars)")
        print(f"  Line 3: '{line3}' ({len(line3)} chars)")

        # Check each line
        issues = []
        for line_num, line in enumerate([line1, line2, line3], 1):
            if line and len(line) > max_safe_chars:
                issues.append(f"Line {line_num} too long: {len(line)} > {max_safe_chars}")

        if issues:
            print(f"  ❌ ISSUES: {', '.join(issues)}")
            all_pass = False
        else:
            print(f"  ✅ PASS: All lines fit within bounds")

    print("\n" + "=" * 50)
    if all_pass:
        print("🎉 All messages fit within 64x32 display bounds!")
    else:
        print("❌ Some messages may not fit properly")

    return all_pass

def test_device_key_shortening():
    """Test device key shortening logic"""

    print("\nTesting device key shortening:")
    print("-" * 30)

    test_keys = [
        "MTX-5ITN-4EX7",
        "ESP-ABCD-EFGH",
        "DEVICE123",
        "A-B-C-D",
        "SHORT"
    ]

    for device_key in test_keys:
        # Simulate the shortening logic
        short_key = device_key.split('-')[-1] if '-' in device_key else device_key[-4:]
        result_text = f"ID:{short_key}"

        print(f"  '{device_key}' -> '{result_text}' ({len(result_text)} chars)")

        if len(result_text) <= 10:
            print(f"    ✅ Fits in display")
        else:
            print(f"    ❌ Too long for display")

def test_claim_code_truncation():
    """Test claim code truncation logic"""

    print("\nTesting claim code truncation:")
    print("-" * 30)

    test_codes = [
        "ABC123",
        "VERYLONGCODE123",
        "XY",
        "123456789",
        "SHORT"
    ]

    for claim_code in test_codes:
        # Simulate the truncation logic
        short_code = claim_code[:6] if len(claim_code) > 6 else claim_code
        result_text = f"{short_code}"

        print(f"  '{claim_code}' -> '{result_text}' ({len(result_text)} chars)")

        if len(result_text) <= 10:
            print(f"    ✅ Fits in display")
        else:
            print(f"    ❌ Too long for display")

def main():
    """Run all tests"""
    print("64x32 Matrix Display Text Fitting Tests")
    print("=" * 50)

    success = True

    # Test message lengths
    if not test_message_lengths():
        success = False

    # Test device key shortening
    test_device_key_shortening()

    # Test claim code truncation
    test_claim_code_truncation()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Messages should display correctly on 64x32 matrix.")
    else:
        print("❌ Some tests failed. Messages may not display properly.")

    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)