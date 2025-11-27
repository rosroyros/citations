#!/usr/bin/env python3
"""
GPT-5.1 Citation Validation Test Script

This script tests OpenAI's GPT-5.1 model with "none" reasoning effort
on all 121 citations from the corrected test set to determine accuracy
toward the 95% validation accuracy goal.

Usage:
    python test_gpt51_validation.py
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

def load_test_set():
    """Load the 121 citation test set with ground truth labels."""
    test_set_path = "/Users/roy/Documents/Projects/citations/Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
    citations = []

    with open(test_set_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
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

    print(f"Loaded {len(citations)} citations from test set")
    return citations

def load_validation_prompt():
    """Load the v2 validation prompt."""
    prompt_path = "/Users/roy/Documents/Projects/citations/backend/prompts/validator_prompt_v2.txt"

    with open(prompt_path, 'r') as f:
        prompt = f.read()

    return prompt

def validate_citation_with_gpt51(citation_text, validation_prompt, client):
    """
    Validate a single citation using GPT-5.1 with 'none' reasoning.

    Args:
        citation_text: The citation to validate
        validation_prompt: The base validation prompt
        client: OpenAI client instance

    Returns:
        dict: Contains the citation, ground truth, model response, and validation result
    """
    # v2 prompt uses placeholder replacement format
    full_prompt = validation_prompt.replace("{citation}", citation_text)

    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=full_prompt,
            reasoning={"effort": "none"}
        )

        model_output = response.choices[0].message.content

        # Determine if model says citation is valid
        # Look for "✓ No APA 7 formatting errors detected" or similar patterns
        is_valid = "✓ No APA 7 formatting errors detected" in model_output

        return {
            'citation': citation_text,
            'model_response': model_output,
            'is_valid': is_valid,
            'raw_response': response
        }

    except Exception as e:
        print(f"Error validating citation: {e}")
        return {
            'citation': citation_text,
            'model_response': f"ERROR: {str(e)}",
            'is_valid': None,
            'raw_response': None
        }

def run_batch_validation():
    """Run validation on all 121 citations in batch."""
    print("🚀 Starting GPT-5.1 Citation Validation Test")
    print("=" * 60)
    print(f"Model: GPT-5.1")
    print(f"Reasoning Effort: none")
    print(f"Test Set: 121 citations with ground truth")
    print("=" * 60)

    # Load data
    citations = load_test_set()
    validation_prompt = load_validation_prompt()

    # Initialize OpenAI client (already loaded above)
    pass

    # Results tracking
    results = []
    correct_predictions = 0
    total_processed = 0

    print(f"\n📋 Processing {len(citations)} citations...\n")

    for i, citation_data in enumerate(citations, 1):
        print(f"Processing citation {i}/121: {citation_data['id']}")

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
            'model_response': validation_result['model_response'],
            'is_correct': validation_result['is_valid'] == citation_data['ground_truth']
        }

        results.append(combined_result)

        # Update counters
        if validation_result['is_valid'] is not None:  # If not an error
            total_processed += 1
            if combined_result['is_correct']:
                correct_predictions += 1

        # Show progress
        accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0
        print(f"  ✓ Correct: {combined_result['is_correct']}")
        print(f"  📊 Current Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_processed})")
        print()

    # Final results
    final_accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0

    print("=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total Citations: {len(citations)}")
    print(f"Successfully Processed: {total_processed}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Final Accuracy: {final_accuracy:.2f}%")
    print(f"Target Accuracy: 95.00%")
    print(f"Gap to Target: {95 - final_accuracy:.2f}%")

    # Error analysis
    false_negatives = 0  # Model says invalid, but it's actually valid
    false_positives = 0  # Model says valid, but it's actually invalid

    for result in results:
        if result['model_prediction'] is not None:
            if not result['model_prediction'] and result['ground_truth']:
                false_negatives += 1
            elif result['model_prediction'] and not result['ground_truth']:
                false_positives += 1

    print(f"\n🔍 Error Breakdown:")
    print(f"False Negatives (too strict): {false_negatives}")
    print(f"False Positives (too lenient): {false_positives}")

    # Save detailed results
    output_file = "gpt51_validation_results_none_effort.json"
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'model': 'gpt-5.1',
                'reasoning_effort': 'none',
                'total_citations': len(citations),
                'processed': total_processed,
                'correct': correct_predictions,
                'accuracy': final_accuracy,
                'target_accuracy': 95.0,
                'gap': 95 - final_accuracy,
                'false_negatives': false_negatives,
                'false_positives': false_positives
            },
            'results': results
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    return results, final_accuracy

def main():
    """Main execution function."""
    try:
        results, accuracy = run_batch_validation()

        print(f"\n🎯 GPT-5.1 with 'none' reasoning achieved {accuracy:.2f}% accuracy")
        print(f"Goal: 95% accuracy | Current gap: {95 - accuracy:.2f}%")

        if accuracy >= 95:
            print("🎉 TARGET ACHIEVED! GPT-5.1 meets the 95% accuracy goal!")
        else:
            print(f"📈 Additional optimization needed to reach 95% goal.")

    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        raise

if __name__ == "__main__":
    main()