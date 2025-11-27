#!/usr/bin/env python3
"""
GPT-5.1 Citation Validation Test Script - 5 Sample Test

This script tests OpenAI's GPT-5.1 model with "none" reasoning effort
on 5 sample citations to verify the approach works before running on all 121.

Usage:
    python test_gpt51_validation_5samples.py
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

def load_sample_citations():
    """Load 5 sample citations from the test set."""
    samples = [
        {
            'id': 2,
            'citation': "Malory, T. (2017). _Le morte d'Arthur_ (P. J. C. Field, Ed.). D. S. Brewer.",
            'ground_truth': True
        },
        {
            'id': 5,
            'citation': "O'Connor, J., & Smith, L. (2017). _Nancy Clancy, late-breaking news!_ (R. Preiss Glasser, Illus.). HarperCollins Publishers.",
            'ground_truth': True
        },
        {
            'id': 11,
            'citation': "joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post \"The transition to seventh edition APA Style\"]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690",
            'ground_truth': True
        },
        {
            'id': 1,
            'citation': "_King James Bible_ (2017) King James Bible Online. https://www.kingjamesbibleonline.org/ (Original work published: 1769)",
            'ground_truth': False
        },
        {
            'id': 3,
            'citation': "Leitch, M. G., & Rushton, C. J. (Eds.). 2019. _A New Companion to Malory_. D. S. Brewer.",
            'ground_truth': False
        }
    ]

    print(f"Loaded {len(samples)} sample citations for testing")
    return samples

def load_validation_prompt():
    """Load the original v1 validation prompt."""
    prompt_path = "/Users/roy/Documents/Projects/citations/backend/prompts/validator_prompt.txt"

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
    # The original prompt expects citations to be appended at the end
    full_prompt = validation_prompt + "\n" + citation_text

    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=full_prompt,
            reasoning={"effort": "none"}
        )

        # Debug: print response structure
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}")

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
        import traceback
        traceback.print_exc()
        return {
            'citation': citation_text,
            'model_response': f"ERROR: {str(e)}",
            'is_valid': None,
            'raw_response': None
        }

def run_sample_validation():
    """Run validation on 5 sample citations."""
    print("🚀 GPT-5.1 Citation Validation - 5 Sample Test")
    print("=" * 60)
    print(f"Model: GPT-5.1")
    print(f"Reasoning Effort: none")
    print(f"Sample Size: 5 citations with ground truth")
    print("=" * 60)

    # Load data
    citations = load_sample_citations()
    validation_prompt = load_validation_prompt()

    # Initialize OpenAI client (already loaded above)
    pass

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
            'model_response': validation_result['model_response'],
            'is_correct': validation_result['is_valid'] == citation_data['ground_truth']
        }

        results.append(combined_result)

        # Update counters
        if validation_result['is_valid'] is not None:  # If not an error
            total_processed += 1
            if combined_result['is_correct']:
                correct_predictions += 1

        # Show result
        print(f"Model Prediction: {'VALID' if validation_result['is_valid'] else 'INVALID' if validation_result['is_valid'] is False else 'ERROR'}")
        print(f"Correct: {'✓' if combined_result['is_correct'] else '✗'}")
        if not validation_result['is_valid'] and len(validation_result['model_response']) > 200:
            print(f"Model Response: {validation_result['model_response'][:200]}...")
        elif validation_result['is_valid'] is None:
            print(f"Error: {validation_result['model_response']}")
        else:
            print(f"Model Response: {validation_result['model_response']}")
        print()

        # Show progress
        accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0
        print(f"📊 Current Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_processed})")
        print("-" * 40)

    # Final results
    final_accuracy = (correct_predictions / total_processed * 100) if total_processed > 0 else 0

    print("\n" + "=" * 60)
    print("📊 SAMPLE TEST RESULTS")
    print("=" * 60)
    print(f"Total Citations: {len(citations)}")
    print(f"Successfully Processed: {total_processed}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Final Accuracy: {final_accuracy:.2f}%")

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
    output_file = "gpt51_validation_results_5samples_none_effort.json"
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'model': 'gpt-5.1',
                'reasoning_effort': 'none',
                'total_citations': len(citations),
                'processed': total_processed,
                'correct': correct_predictions,
                'accuracy': final_accuracy,
                'false_negatives': false_negatives,
                'false_positives': false_positives,
                'test_type': '5_sample_validation'
            },
            'results': results
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    return results, final_accuracy

def main():
    """Main execution function."""
    try:
        results, accuracy = run_sample_validation()

        print(f"\n🎯 GPT-5.1 with 'none' reasoning achieved {accuracy:.2f}% accuracy on 5 samples")

        if accuracy >= 95:
            print("🎉 EXCELLENT! 5-sample test suggests approach may achieve 95% target!")
            print("🚀 Ready to run on full 121 citation test set.")
        elif accuracy >= 80:
            print("📈 GOOD result! Worth testing on full 121 citation set.")
            print("🚀 Proceed to full validation test.")
        else:
            print("⚠️  Low accuracy on sample. Consider debugging before full test.")
            print("🔧 Review prompts and approach before scaling up.")

    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        raise

if __name__ == "__main__":
    main()