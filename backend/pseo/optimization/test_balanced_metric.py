"""Test the balanced metric to verify it scores correctly."""
import dspy
from dspy_validator import citation_validator_metric

def test_balanced_metric():
    """Test all scenarios of the balanced metric."""

    print("="*70)
    print("TESTING BALANCED METRIC")
    print("="*70)

    # Test Case 1: Both valid - should score 1.0
    print("\n1. Both valid (perfect agreement):")
    example1 = dspy.Example(
        citation="Smith, J. (2020). Title. Journal, 1(2), 3-4.",
        is_valid=True,
        errors=[]
    )
    pred1 = dspy.Prediction(is_valid=True, errors=[])
    score1 = citation_validator_metric(example1, pred1)
    print(f"   Score: {score1:.3f} (expected: 1.000)")
    print(f"   ✓ PASS" if score1 == 1.0 else f"   ✗ FAIL")

    # Test Case 2: Both invalid, perfect error match - should score 1.0
    print("\n2. Both invalid, perfect error matching:")
    example2 = dspy.Example(
        citation="Smith J (2020) Title. Journal, 1(2), 3-4.",
        is_valid=False,
        errors=[
            {"component": "authors", "problem": "Missing period", "correction": "Smith, J."},
            {"component": "title", "problem": "Missing italics", "correction": "Italicize"}
        ]
    )
    pred2 = dspy.Prediction(
        is_valid=False,
        errors=[
            {"component": "authors", "problem": "Missing period", "correction": "Smith, J."},
            {"component": "title", "problem": "Missing italics", "correction": "Italicize"}
        ]
    )
    score2 = citation_validator_metric(example2, pred2)
    print(f"   Score: {score2:.3f} (expected: 1.000)")
    print(f"   Citation correct: 1.0, Error F1: 1.0 → Final: 0.5*1 + 0.5*1 = 1.0")
    print(f"   ✓ PASS" if score2 == 1.0 else f"   ✗ FAIL")

    # Test Case 3: Both invalid, partial error match - should score between 0.5 and 1.0
    print("\n3. Both invalid, partial error matching:")
    example3 = dspy.Example(
        citation="Smith J (2020) Title. Journal, 1(2), 3-4.",
        is_valid=False,
        errors=[
            {"component": "authors", "problem": "Missing period", "correction": "Smith, J."},
            {"component": "title", "problem": "Missing italics", "correction": "Italicize"}
        ]
    )
    pred3 = dspy.Prediction(
        is_valid=False,
        errors=[
            {"component": "authors", "problem": "Missing period", "correction": "Smith, J."}
        ]
    )
    score3 = citation_validator_metric(example3, pred3)
    print(f"   Score: {score3:.3f}")
    print(f"   Citation correct: 1.0, Error F1: ~0.67 (1 TP, 0 FP, 1 FN)")
    print(f"   Final: 0.5*1 + 0.5*0.67 = ~0.83")
    print(f"   ✓ PASS" if 0.5 < score3 < 1.0 else f"   ✗ FAIL")

    # Test Case 4: False positive (valid flagged as invalid) - should score 0.0
    print("\n4. False positive (valid → invalid):")
    example4 = dspy.Example(
        citation="Smith, J. (2020). Title. Journal, 1(2), 3-4.",
        is_valid=True,
        errors=[]
    )
    pred4 = dspy.Prediction(
        is_valid=False,
        errors=[{"component": "authors", "problem": "Fake error", "correction": "None"}]
    )
    score4 = citation_validator_metric(example4, pred4)
    print(f"   Score: {score4:.3f} (expected: 0.000)")
    print(f"   Citation correct: 0.0, Error score: 0.0 → Final: 0.5*0 + 0.5*0 = 0.0")
    print(f"   ✓ PASS" if score4 == 0.0 else f"   ✗ FAIL")

    # Test Case 5: False negative (invalid flagged as valid) - should score 0.0
    print("\n5. False negative (invalid → valid):")
    example5 = dspy.Example(
        citation="Smith J (2020) Title. Journal, 1(2), 3-4.",
        is_valid=False,
        errors=[{"component": "authors", "problem": "Missing period", "correction": "Smith, J."}]
    )
    pred5 = dspy.Prediction(is_valid=True, errors=[])
    score5 = citation_validator_metric(example5, pred5)
    print(f"   Score: {score5:.3f} (expected: 0.000)")
    print(f"   Citation correct: 0.0, Error score: 0.0 → Final: 0.5*0 + 0.5*0 = 0.0")
    print(f"   ✓ PASS" if score5 == 0.0 else f"   ✗ FAIL")

    # Test Case 6: Both invalid, no error match - should score 0.5
    print("\n6. Both invalid, but completely wrong error components:")
    example6 = dspy.Example(
        citation="Smith J (2020) Title. Journal, 1(2), 3-4.",
        is_valid=False,
        errors=[
            {"component": "authors", "problem": "Missing period", "correction": "Smith, J."}
        ]
    )
    pred6 = dspy.Prediction(
        is_valid=False,
        errors=[
            {"component": "doi", "problem": "Missing DOI", "correction": "Add DOI"}
        ]
    )
    score6 = citation_validator_metric(example6, pred6)
    print(f"   Score: {score6:.3f} (expected: 0.500)")
    print(f"   Citation correct: 1.0, Error F1: 0.0 (0 TP, 1 FP, 1 FN)")
    print(f"   Final: 0.5*1 + 0.5*0 = 0.5")
    print(f"   ✓ PASS" if score6 == 0.5 else f"   ✗ FAIL")

    print("\n" + "="*70)
    print("KEY INSIGHT: The new metric prevents gaming!")
    print("="*70)
    print("- Just getting valid/invalid right: 0.5 score minimum")
    print("- Must also match error components to reach 1.0")
    print("- Can't optimize for one without the other")
    print("="*70)

if __name__ == "__main__":
    test_balanced_metric()
