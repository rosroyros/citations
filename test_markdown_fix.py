#!/usr/bin/env python3
"""
Test for the markdown conversion fix.
This should initially fail, then pass after we implement the fix.
"""

import re

def current_underscore_conversion(text):
    """Current implementation from openai_provider.py line 249"""
    return re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

def fixed_underscore_conversion(text):
    """Fixed implementation that handles edge cases better"""
    # Convert valid italic patterns (avoiding empty matches and double underscores)
    # Pattern: single underscore, then non-underscore content, then single underscore
    # Don't match: __text__ (double underscores), __ (empty), _ (single)
    return re.sub(r'(?<!_)_([^_]+)_([^_])', r'<em>\1</em>\2', text)

def fixed_bold_conversion(text):
    """New implementation to convert **bold** to <strong>bold</strong>"""
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

def fixed_combined_conversion(text):
    """Apply both fixes in the right order"""
    # Convert bold first, then italics
    text = fixed_bold_conversion(text)
    text = fixed_underscore_conversion(text)
    return text

def test_expected_fixes():
    """Test cases that should work after the fix"""

    # These should pass after fixing bold conversion
    bold_test_cases = [
        ("Smith, J. (2020). **Journal of Testing**, 15(2), 123-145.",
         "Smith, J. (2020). <strong>Journal of Testing</strong>, 15(2), 123-145."),

        ("Mixed **bold** and _italic_ text.",
         "Mixed <strong>bold</strong> and <em>italic</em> text."),
    ]

    # These should pass after fixing underscore edge cases
    underscore_test_cases = [
        ("Smith, J. (2020). _Journal of Testing_, 15(2), 123-145.",
         "Smith, J. (2020). <em>Journal of Testing</em>, 15(2), 123-145."),

        ("No italics: single_underscore should not change.",
         "No italics: single_underscore should not change."),
    ]

    print("=== TESTING BOLD CONVERSION ===")
    all_pass = True
    for i, (input_text, expected) in enumerate(bold_test_cases, 1):
        result = fixed_combined_conversion(input_text)
        passed = result == expected
        all_pass = all_pass and passed

        print(f"{i}. Input:    {input_text}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        print(f"   Pass:     {passed}")
        print()

    print("=== TESTING UNDERSCORE CONVERSION ===")
    for i, (input_text, expected) in enumerate(underscore_test_cases, 1):
        result = fixed_combined_conversion(input_text)
        passed = result == expected
        all_pass = all_pass and passed

        print(f"{i}. Input:    {input_text}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        print(f"   Pass:     {passed}")
        print()

    print(f"=== OVERALL RESULT: {'PASS' if all_pass else 'FAIL'} ===")
    return all_pass

if __name__ == "__main__":
    test_expected_fixes()