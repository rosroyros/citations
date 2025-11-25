#!/usr/bin/env python3
"""
Test script to reproduce the markdown formatting issue.
This helps us understand exactly what's happening with underscore and bold conversion.
"""

import re

def current_underscore_conversion(text):
    """Current implementation from openai_provider.py line 249"""
    return re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

def current_bold_conversion(text):
    """Current implementation from app.py (needs investigation)"""
    # This is likely missing or not working properly
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

def test_current_patterns():
    """Test current markdown conversion patterns"""

    # Test cases that should show italics
    test_cases_italics = [
        "Smith, J. (2020). _Journal of Testing_, 15(2), 123-145.",
        "This should be _italic text_ in the citation.",
        "Multiple _italic_ and _more italic_ phrases.",
        "Edge case: _multiple words here_ should be italic.",
        "No italics: single_underscore should not change.",
    ]

    # Test cases that should show bold
    test_cases_bold = [
        "Smith, J. (2020). **Journal of Testing**, 15(2), 123-145.",
        "This should be **bold text** in the citation.",
        "Multiple **bold** and **more bold** phrases.",
        "Mixed **bold** and _italic_ text.",
    ]

    print("=== TESTING CURRENT UNDERSCORE CONVERSION ===")
    for i, test in enumerate(test_cases_italics, 1):
        result = current_underscore_conversion(test)
        print(f"{i}. Input:  {test}")
        print(f"   Output: {result}")
        print(f"   Success: {'_' not in result}")
        print()

    print("=== TESTING CURRENT BOLD CONVERSION ===")
    for i, test in enumerate(test_cases_bold, 1):
        result = current_bold_conversion(test)
        print(f"{i}. Input:  {test}")
        print(f"   Output: {result}")
        print(f"   Success: {'**' not in result}")
        print()

def test_edge_cases():
    """Test edge cases that might break the current regex"""
    edge_cases = [
        "Multiple underscores: __this__ and _this_",
        "Nested: _outer **inner** outer_",
        "Escaped: \\_not italic_",
        "Empty: __ and _single_",
        "Numbers: _123_ and _abc123_",
    ]

    print("=== TESTING EDGE CASES ===")
    for i, test in enumerate(edge_cases, 1):
        underscore_result = current_underscore_conversion(test)
        bold_result = current_bold_conversion(test)
        print(f"{i}. Input:  {test}")
        print(f"   Underscores: {underscore_result}")
        print(f"   Bold:        {bold_result}")
        print()

if __name__ == "__main__":
    test_current_patterns()
    test_edge_cases()