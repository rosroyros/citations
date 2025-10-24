#!/usr/bin/env python3
"""
Detailed error analysis of optimized validator
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
import dspy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_dataset(filepath):
    """Load dataset from JSONL"""
    examples = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def generate_predictions_with_details(model, test_examples):
    """Generate predictions with full details"""
    results = []

    for i, example in enumerate(test_examples):
        try:
            pred = model(citation=example['citation'])

            pred_valid = str(pred.is_valid).lower().strip() == 'true'
            gold_valid = example['is_valid']

            result = {
                'index': i,
                'citation': example['citation'],
                'ground_truth': gold_valid,
                'predicted': pred_valid,
                'explanation': pred.explanation if hasattr(pred, 'explanation') else '',
                'correct': pred_valid == gold_valid,
                'error_type': None,
                'metadata': example.get('metadata', {})
            }

            # Classify error type
            if not result['correct']:
                if gold_valid and not pred_valid:
                    result['error_type'] = 'false_negative'  # Valid citation marked invalid
                else:
                    result['error_type'] = 'false_positive'  # Invalid citation marked valid

            results.append(result)

        except Exception as e:
            logger.error(f"Error on example {i}: {e}")
            results.append({
                'index': i,
                'citation': example['citation'],
                'ground_truth': example['is_valid'],
                'predicted': None,
                'explanation': f'Error: {str(e)}',
                'correct': False,
                'error_type': 'prediction_error',
                'metadata': example.get('metadata', {})
            })

    return results


def analyze_errors(results):
    """Perform comprehensive error analysis"""

    analysis = {
        'total': len(results),
        'correct': sum(1 for r in results if r['correct']),
        'incorrect': sum(1 for r in results if not r['correct']),
        'accuracy': sum(1 for r in results if r['correct']) / len(results),
        'error_types': defaultdict(int),
        'false_positives': [],
        'false_negatives': [],
        'citation_length_errors': defaultdict(list),
        'error_patterns': []
    }

    # Error type breakdown
    for r in results:
        if r['error_type']:
            analysis['error_types'][r['error_type']] += 1

            if r['error_type'] == 'false_positive':
                analysis['false_positives'].append(r)
            elif r['error_type'] == 'false_negative':
                analysis['false_negatives'].append(r)

    # Citation length analysis
    for r in results:
        if not r['correct']:
            length_bucket = (len(r['citation']) // 100) * 100
            analysis['citation_length_errors'][length_bucket].append(r)

    # Pattern detection in false positives (invalid marked as valid)
    fp_patterns = defaultdict(int)
    for fp in analysis['false_positives']:
        citation = fp['citation'].lower()
        # Check for common APA error patterns
        if 'pp.' not in citation and 'p.' not in citation:
            fp_patterns['missing_page_notation'] += 1
        if citation.count('(') != citation.count(')'):
            fp_patterns['unbalanced_parentheses'] += 1
        if '&' not in citation and ' and ' in citation:
            fp_patterns['and_instead_of_ampersand'] += 1
        if citation.count(',') < 2:
            fp_patterns['insufficient_commas'] += 1
        if not any(c.isupper() for c in citation):
            fp_patterns['no_capitals'] += 1

    analysis['fp_patterns'] = dict(fp_patterns)

    # Pattern detection in false negatives (valid marked as invalid)
    fn_patterns = defaultdict(int)
    for fn in analysis['false_negatives']:
        citation = fn['citation'].lower()
        # What valid citations are being rejected?
        if 'doi' in citation or 'http' in citation:
            fn_patterns['has_doi_or_url'] += 1
        if citation.count('(') == citation.count(')') and citation.count('(') >= 2:
            fn_patterns['proper_parentheses'] += 1
        if '_' in fn['citation']:  # Markdown italics
            fn_patterns['has_markdown_italics'] += 1
        if citation.count(',') >= 3:
            fn_patterns['many_commas'] += 1

    analysis['fn_patterns'] = dict(fn_patterns)

    return analysis


def print_analysis_report(analysis):
    """Print comprehensive analysis report"""

    print("\n" + "="*80)
    print("ERROR ANALYSIS REPORT")
    print("="*80)

    print(f"\n📊 OVERALL METRICS")
    print(f"  Total predictions: {analysis['total']}")
    print(f"  Correct: {analysis['correct']} ({analysis['accuracy']:.1%})")
    print(f"  Incorrect: {analysis['incorrect']} ({analysis['incorrect']/analysis['total']:.1%})")

    print(f"\n❌ ERROR BREAKDOWN")
    for error_type, count in sorted(analysis['error_types'].items(), key=lambda x: -x[1]):
        pct = count / analysis['total'] * 100
        print(f"  {error_type}: {count} ({pct:.1f}%)")

    print(f"\n🔴 FALSE POSITIVES (Invalid marked as Valid): {len(analysis['false_positives'])}")
    print(f"  These are the most dangerous - invalid citations passing through")
    if analysis['fp_patterns']:
        print(f"  Common patterns in missed invalid citations:")
        for pattern, count in sorted(analysis['fp_patterns'].items(), key=lambda x: -x[1])[:5]:
            print(f"    - {pattern}: {count}")

    if analysis['false_positives']:
        print(f"\n  Sample false positives (showing first 3):")
        for i, fp in enumerate(analysis['false_positives'][:3], 1):
            print(f"\n  [{i}] Citation: {fp['citation'][:150]}...")
            print(f"      Model said: VALID (incorrect - should be INVALID)")
            print(f"      Explanation: {fp['explanation'][:200]}...")

    print(f"\n🟡 FALSE NEGATIVES (Valid marked as Invalid): {len(analysis['false_negatives'])}")
    print(f"  These reject correct citations - annoying but less dangerous")
    if analysis['fn_patterns']:
        print(f"  Common patterns in rejected valid citations:")
        for pattern, count in sorted(analysis['fn_patterns'].items(), key=lambda x: -x[1])[:5]:
            print(f"    - {pattern}: {count}")

    if analysis['false_negatives']:
        print(f"\n  Sample false negatives (showing first 3):")
        for i, fn in enumerate(analysis['false_negatives'][:3], 1):
            print(f"\n  [{i}] Citation: {fn['citation'][:150]}...")
            print(f"      Model said: INVALID (incorrect - should be VALID)")
            print(f"      Explanation: {fn['explanation'][:200]}...")

    print(f"\n📏 ERRORS BY CITATION LENGTH")
    for length_bucket, errors in sorted(analysis['citation_length_errors'].items()):
        if errors:
            print(f"  {length_bucket}-{length_bucket+99} chars: {len(errors)} errors")

    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)

    # Calculate precision and recall for invalid class
    tp = len([r for r in analysis['false_positives']]) + analysis['correct'] - len(analysis['false_negatives'])
    fp = len(analysis['false_positives'])
    fn = len(analysis['false_negatives'])

    # Actually let's recalculate properly
    all_results = []
    from pathlib import Path
    base_dir = Path("Checker_Prompt_Optimization")
    dataset_path = base_dir / "final_merged_dataset.jsonl"
    all_examples = []
    with open(dataset_path, 'r') as f:
        for line in f:
            if line.strip():
                all_examples.append(json.loads(line))
    split_idx = int(len(all_examples) * 0.8)
    test_examples = all_examples[split_idx:]

    true_invalid = sum(1 for e in test_examples if not e['is_valid'])
    true_valid = sum(1 for e in test_examples if e['is_valid'])

    print(f"\n🎯 RECOMMENDATIONS")

    if len(analysis['false_positives']) > len(analysis['false_negatives']):
        print(f"  ⚠️  CRITICAL: More false positives than false negatives!")
        print(f"      The model is letting invalid citations through.")
        print(f"      Consider: Stricter validation rules, more training on invalid examples")
    else:
        print(f"  ✓ Good: More false negatives than false positives")
        print(f"    The model errs on the side of caution (better for a validator)")

    if analysis['fp_patterns']:
        top_fp_pattern = max(analysis['fp_patterns'].items(), key=lambda x: x[1])
        print(f"\n  🔍 Top missed invalid pattern: {top_fp_pattern[0]} ({top_fp_pattern[1]} cases)")
        print(f"      Action: Add more training examples with this error type")

    if analysis['fn_patterns']:
        top_fn_pattern = max(analysis['fn_patterns'].items(), key=lambda x: x[1])
        print(f"\n  📝 Top rejected valid pattern: {top_fn_pattern[0]} ({top_fn_pattern[1]} cases)")
        print(f"      Action: Review prompt to avoid over-flagging this pattern")

    print(f"\n  📈 Performance Summary:")
    print(f"     - Accuracy: {analysis['accuracy']:.1%}")
    print(f"     - True Invalid in test: {true_invalid}")
    print(f"     - True Valid in test: {true_valid}")
    print(f"     - Dataset balance: {true_invalid/len(test_examples):.1%} invalid")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    import os

    base_dir = Path(__file__).parent
    output_dir = base_dir / "optimized_output"
    model_path = output_dir / "optimized_validator.json"
    dataset_path = base_dir / "final_merged_dataset.jsonl"

    if not model_path.exists():
        logger.error(f"Optimized model not found: {model_path}")
        sys.exit(1)

    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    # Configure DSPy
    lm = dspy.LM(model='openai/gpt-4o-mini', max_tokens=500, temperature=0.0)
    dspy.configure(lm=lm)

    # Load model
    logger.info("Loading optimized model...")
    import sys
    sys.path.insert(0, str(base_dir))
    from run_gepa_optimization import APAValidatorModule
    model = APAValidatorModule()
    model.load(str(model_path))

    # Load test set
    logger.info("Loading test set...")
    all_examples = load_dataset(dataset_path)
    split_idx = int(len(all_examples) * 0.8)
    test_examples = all_examples[split_idx:]
    logger.info(f"Test set: {len(test_examples)} examples")

    # Generate predictions
    logger.info("Generating predictions...")
    results = generate_predictions_with_details(model, test_examples)

    # Analyze
    logger.info("Analyzing errors...")
    analysis = analyze_errors(results)

    # Print report
    print_analysis_report(analysis)

    # Save detailed results
    output_file = output_dir / "error_analysis.json"
    with open(output_file, 'w') as f:
        # Convert to serializable format
        serializable_analysis = {
            'total': analysis['total'],
            'correct': analysis['correct'],
            'incorrect': analysis['incorrect'],
            'accuracy': analysis['accuracy'],
            'error_types': dict(analysis['error_types']),
            'fp_patterns': analysis['fp_patterns'],
            'fn_patterns': analysis['fn_patterns'],
            'num_false_positives': len(analysis['false_positives']),
            'num_false_negatives': len(analysis['false_negatives']),
            'false_positive_examples': [
                {
                    'citation': fp['citation'],
                    'explanation': fp['explanation']
                }
                for fp in analysis['false_positives'][:10]
            ],
            'false_negative_examples': [
                {
                    'citation': fn['citation'],
                    'explanation': fn['explanation']
                }
                for fn in analysis['false_negatives'][:10]
            ]
        }
        json.dump(serializable_analysis, f, indent=2)

    logger.info(f"Detailed analysis saved to {output_file}")
