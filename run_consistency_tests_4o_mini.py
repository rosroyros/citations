#!/usr/bin/env python3
"""
Run consistency tests on GPT-4o-mini only (for parallel execution).
Tests model 3 times with temperature=1 to measure consistency and ensemble performance.
"""
import json
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load OpenAI API key from .env file
load_dotenv('backend/.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# Load optimized prompt
with open('backend/prompts/validator_prompt_optimized.txt', 'r') as f:
    base_prompt = f.read()

# Load test set
test_file = 'Checker_Prompt_Optimization/test_set_121_corrected.jsonl'
test_set = []
with open(test_file, 'r') as f:
    for line in f:
        test_set.append(json.loads(line))

print(f"Loaded {len(test_set)} citations from {test_file}")
print()

def parse_model_response(response_text):
    """Parse model response to extract verdict."""
    response_lower = response_text.lower()
    if "✓ no apa 7 formatting errors detected" in response_lower:
        return True  # Valid
    elif "❌" in response_text:
        return False  # Invalid
    else:
        return None  # Unknown

def run_consistency_test(model_name, run_number):
    """Run one consistency test iteration."""
    output_file = f'Checker_Prompt_Optimization/consistency_test_{model_name}_run_{run_number}.jsonl'

    print(f"{'='*80}")
    print(f"Running {model_name} - Run {run_number}")
    print(f"Output: {output_file}")
    print(f"{'='*80}")
    print()

    results = []
    correct_count = 0

    for i, item in enumerate(test_set, 1):
        citation = item['citation']
        ground_truth = item['ground_truth']

        print(f"[{i}/{len(test_set)}] {citation[:60]}...")

        prompt = base_prompt + "\n\n" + citation

        try:
            # GPT-4o-mini uses standard temperature parameter (no reasoning_effort)
            response = client.chat.completions.create(
                model=model_name,
                temperature=1,
                messages=[{"role": "user", "content": prompt}]
            )

            full_response = response.choices[0].message.content
            predicted = parse_model_response(full_response)
            correct = (predicted == ground_truth)

            if correct:
                correct_count += 1

            result = {
                'citation': citation,
                'ground_truth': ground_truth,
                'predicted': predicted,
                'raw_response': full_response,
                'correct': correct
            }

            results.append(result)

            # Save after each (incremental save)
            with open(output_file, 'w') as f:
                for r in results:
                    f.write(json.dumps(r) + '\n')

            status = "✓" if correct else "✗"
            print(f"  GT: {'VALID' if ground_truth else 'INVALID'} | "
                  f"Pred: {'VALID' if predicted else 'INVALID' if predicted is False else 'UNKNOWN'} "
                  f"{status}")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            result = {
                'citation': citation,
                'ground_truth': ground_truth,
                'error': str(e)
            }
            results.append(result)

            # Save even with error
            with open(output_file, 'w') as f:
                for r in results:
                    f.write(json.dumps(r) + '\n')

    accuracy = (correct_count / len(test_set)) * 100 if test_set else 0
    print()
    print(f"Run {run_number} Complete: {correct_count}/{len(test_set)} correct ({accuracy:.2f}%)")
    print()

    return output_file, accuracy

# Run tests for GPT-4o-mini only
model_id = 'gpt-4o-mini'
model_label = 'GPT-4o-mini_optimized'

print(f"\n{'#'*80}")
print(f"# Testing: {model_label}")
print(f"{'#'*80}\n")

model_runs = []
for run in range(1, 4):
    output_file, accuracy = run_consistency_test(model_id, run)
    model_runs.append({
        'run': run,
        'output_file': output_file,
        'accuracy': accuracy
    })

# Calculate average accuracy
avg_accuracy = sum(r['accuracy'] for r in model_runs) / len(model_runs)
print(f"\n{model_label} Average Accuracy: {avg_accuracy:.2f}%")
print(f"Run 1: {model_runs[0]['accuracy']:.2f}%")
print(f"Run 2: {model_runs[1]['accuracy']:.2f}%")
print(f"Run 3: {model_runs[2]['accuracy']:.2f}%")
print()

# Save summary
summary = {
    'test_date': datetime.now().isoformat(),
    'test_set': test_file,
    'num_citations': len(test_set),
    'model': model_label,
    'runs': model_runs,
    'avg_accuracy': avg_accuracy
}

summary_file = 'Checker_Prompt_Optimization/consistency_test_4o_mini_summary.json'
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n✅ GPT-4o-mini tests complete! Summary saved to: {summary_file}")
