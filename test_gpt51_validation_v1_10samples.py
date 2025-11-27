#!/usr/bin/env python3
"""
GPT-5.1 Citation Validation Test Script - V1 Prompt, 10 Samples

This script tests OpenAI's GPT-5.1 model with "none" reasoning effort
on 10 sample citations using the original v1 prompt to compare performance.

Usage:
    python test_gpt51_validation_v1_10samples.py
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import openai

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key from .env file
ENV_PATH = os.getenv('ENV_FILE_PATH', './backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found in .env file", flush=True)
    print(f"   Checked: {ENV_PATH}", flush=True)
    exit(1)

client = openai.OpenAI(api_key=OPENAI_API_KEY)
print(f"✓ OpenAI API key loaded", flush=True)

def load_10_sample_citations():
    """Load 10 sample citations from test set."""
    # Select a mix of valid/invalid for comprehensive test
    sample_indices = [2, 5, 11, 1, 4, 8, 14, 18, 29]  # 6 valid, 4 invalid

    test_set_path = "/Users/roy/Documents/Projects/citations/Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
    citations = []

    with open(test_set_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip() and line_num in sample_indices:
                try:
                    data = json.loads(line)
                    citations.append({
                        'id': line_num,
                        'citation': data['citation'],
                        'ground_truth': data['ground_truth']
                    })
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue

    print(f"Loaded {len(citations)} sample citations for testing")
    return citations

def load_v1_validation_prompt():
    """Load the original v1 validation prompt."""
    prompt_path = "/Users/roy/Documents/Projects/citations/backend/prompts/validator_prompt.txt"

    with open(prompt_path, 'r') as f:
        prompt = f.read()

    return prompt

def validate_citation_with_gpt51(citation_text, validation_prompt, client):
    """
    Validate a single citation using GPT-5.1 with 'none' reasoning.

    Returns:
        dict: Contains the citation, ground truth, model response, and validation result
    """
    # The v1 prompt expects citations to be appended at the end
    full_prompt = validation_prompt + "\n" + citation_text

    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=full_prompt,
            reasoning={"effort": "none"}
        )

        # Try different response formats based on Response type
        if hasattr(response, 'output_text'):
            model_output = response.output_text
        elif hasattr(response, 'choices'):
            model_output = response.choices[0].message.content
        elif hasattr(response, 'content'):
            model_output = response.content
        elif hasattr(response, 'text'):
            model_output = response.text
        elif hasattr(response, 'output'):
            model_output = response.output
        else:
            # Fallback: convert to string and extract content
            model_output = str(response)
            print(f"Using raw response as output: {model_output[:200]}...")

        # IMPROVED PARSING: Extract validation decision from structured GPT-5.1 response
        is_valid = None

        # GPT-5.1 provides detailed analysis - look for explicit decision patterns
        if "✓ No APA 7 formatting errors detected" in model_output:
            is_valid = True
        # Look for explicit INVALID patterns in the detailed analysis
        elif any(pattern in model_output for pattern in [
            "❌ [Component]: [What's wrong]",
            "Should be: [Correct format]",
            "INVALID",
            "contains formatting errors that violate APA 7 guidelines",
            "does not meet APA 7 formatting standards"
        ]):
            is_valid = False
        # Default: assume valid if no clear invalid patterns found
        else:
            is_valid = True

        return {
            'citation': citation_text,
            'model_response': model_output,
            'is_valid': is_valid,
            'raw_response': response
        }

    except Exception as e:
        print(f"Error validating citation: {e}")
        import traceback
        traceback.print_exc()
        return {
            'citation': citation_text,
            'model_response': f"ERROR: {str(e)}",
            'is_valid': None,
            'raw_response': None
        }

def run_v1_sample_validation():
    """Run validation on 10 sample citations using v1 prompt."""
    print("🚀 GPT-5.1 Citation Validation - V1 Prompt, 10 Samples")
    print("=" * 60)
    print(f"Model: GPT-5.1")
    print(f"Reasoning Effort: none")
    print(f"Sample Size: 10 citations with ground truth")
    print("=" * 60)

    # Load data
    citations = load_10_sample_citations()
    validation_prompt = load_v1_validation_prompt()

    # Results tracking
    results = []
    correct_predictions = 0
    total_processed = 0

    print(f"\n📋 Processing {len(citations)} sample citations...\n")

    for i, citation_data in enumerate(citations, 1):
        print(f"Processing citation {i}/{len(citations)}")
        print(f"Citation: {citation_data['citation']}")
        print(f"Ground Truth: {'VALID' if citation_data['ground_truth'] else 'INVALID'}")

        # Validate with GPT-5.1
        validation_result = validate_citation_with_gpt51(
            citation_data['citation'],
            validation_prompt,
            client
        )

        # Combine with ground truth
        combined_result = {
            'id': citation_data['id'],
            'citation': citation_data['citation'],
            'ground_truth': citation_data['ground_truth'],
            'model_prediction': validation_result['is_valid'],
            'model_response': validation_result['model_response'][:500] + ("..." if len(validation_result['model_response']) > 500 else ""),
            'is_correct': validation_result['is_valid'] == citation_data['ground_truth']
        }

        results.append(combined_result)

        # Update counters
        if validation_result['is_valid'] is not None:  # If not an error
            total_processed += 1
            if combined_result['is_correct']:
                correct_predictions += 1

        # Show result
        status = "✓ CORRECT" if combined_result['is_correct'] else "❌ INCORRECT"
        prediction = "VALID" if validation_result['is_valid'] else "INVALID"

        print(f"Model Prediction: {prediction}")
        print(f"Result: {status}")

        if len(validation_result['model_response']) > 200:
            print(f"Model Response: {validation_result['model_response'][:200]}...")
        else:
            print(f"Model Response: {validation_result['model_response']}")

        print()

        # Show progress
        accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0
        print(f"📊 Current Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_processed})")
        print("-" * 40)

    # Final results
    false_negatives = 0  # Model says invalid, but it's actually valid
    false_positives = 0  # Model says valid, but it's actually invalid

    for result in results:
        if result['model_prediction'] is not None:
            if not result['model_prediction'] and result['ground_truth']:
                false_negatives += 1
            elif result['model_prediction'] and not result['ground_truth']:
                false_positives += 1

    final_accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0

    print("\n" + "=" * 60)
    print("📊 V1 PROMPT TEST RESULTS")
    print("=" * 60)
    print(f"Total Citations: {len(citations)}")
    print(f"Successfully Processed: {total_processed}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Final Accuracy: {final_accuracy:.2f}%")

    print(f"\n🔍 Error Breakdown:")
    print(f"False Negatives (too strict): {false_negatives}")
    print(f"False Positives (too lenient): {false_positives}")

    # Save detailed results
    output_file = "gpt51_validation_results_v1_10samples_none_effort.json"
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'model': 'gpt-5.1',
                'reasoning_effort': 'none',
                'prompt_type': 'v1',
                'total_citations': len(citations),
                'processed': total_processed,
                'correct': correct_predictions,
                'accuracy': final_accuracy,
                'false_negatives': false_negatives,
                'false_positives': false_positives,
                'test_type': 'v1_10_sample_validation'
            },
            'results': results
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Success assessment
    print(f"\n🎯 GPT-5.1 with 'none' reasoning achieved {final_accuracy:.2f}% accuracy on {len(citations)} samples using V1 prompt")

    if final_accuracy >= 80:
        print("🎉 EXCELLENT! V1 prompt shows significant improvement potential")
    elif final_accuracy >= 60:
        print("📈 GOOD! V1 prompt performs better than expected")
    elif final_accuracy >= 40:
        print("📊 MODERATE: V1 prompt shows some improvement")
    else:
        print("⚠️  LOW ACCURACY: V1 prompt needs significant refinement")

    print(f"\n🤔 Comparison with V2 prompt test:")
    print(f"   V2 Prompt Accuracy: 80.0% (4/5 correct)")
    print(f"   V1 Prompt Accuracy: {final_accuracy:.1f}% ({correct_predictions}/{total_processed})")
    print(f"   Difference: {final_accuracy - 80.0:+.1f} percentage points")

    return results, final_accuracy

def main():
    """Main execution function."""
    try:
        results, accuracy = run_v1_sample_validation()

        print(f"\n🎯 GPT-5.1 with 'none' reasoning achieved {accuracy:.1f}% accuracy on 10 samples")
        print("⚠️  Consider running full 121-citation test to confirm these results")
        print("🔧 Consider fixing parsing or prompt issues before scaling up")

    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        raise

if __name__ == "__main__":
    main()