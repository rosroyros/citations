"""
Extract and display the optimized prompt from DSPy model.
"""
import json
from pathlib import Path
import dspy
from dspy_config import setup_dspy


def extract_prompt(model_path):
    """Extract the optimized prompt from saved DSPy model."""

    # Load the saved model
    with open(model_path, 'r') as f:
        model_data = json.load(f)

    print("="*80)
    print("OPTIMIZED DSPy MODEL ANALYSIS")
    print("="*80)

    # Check structure
    print("\nModel Structure:")
    print(json.dumps({k: type(v).__name__ for k, v in model_data.items()}, indent=2))

    # Look for prompts/demos
    if 'validate' in model_data:
        print("\n" + "-"*80)
        print("VALIDATION MODULE")
        print("-"*80)
        validate_data = model_data['validate']

        # Check for demos (few-shot examples)
        if 'demos' in validate_data:
            demos = validate_data['demos']
            print(f"\nFew-shot Examples (Demos): {len(demos)} examples")

            for i, demo in enumerate(demos[:3], 1):  # Show first 3
                print(f"\n--- Demo {i} ---")
                print(json.dumps(demo, indent=2))

        # Check for extended signature
        if 'extended_signature' in validate_data:
            print("\n" + "-"*80)
            print("EXTENDED SIGNATURE (Optimized Instructions)")
            print("-"*80)
            print(validate_data['extended_signature'])

        # Check for other prompt-related fields
        for key in validate_data:
            if 'prompt' in key.lower() or 'instruction' in key.lower():
                print(f"\n{key}:")
                print(validate_data[key])

    # Save full model dump for inspection
    output_file = Path("backend/pseo/optimization/models/optimized_prompt_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(model_data, f, indent=2)

    print(f"\n✓ Full model saved to: {output_file}")

    # Try to reconstruct the effective prompt
    print("\n" + "="*80)
    print("RECONSTRUCTED EFFECTIVE PROMPT")
    print("="*80)

    if 'validate' in model_data and 'demos' in model_data['validate']:
        print("\nThe optimized validator uses few-shot learning with these patterns:\n")

        demos = model_data['validate']['demos']

        # Analyze demo patterns
        from collections import Counter

        valid_count = sum(1 for d in demos if d.get('is_valid'))
        invalid_count = len(demos) - valid_count

        print(f"Demo distribution:")
        print(f"  Valid examples: {valid_count}")
        print(f"  Invalid examples: {invalid_count}")

        # Error patterns in demos
        error_components = []
        for demo in demos:
            if not demo.get('is_valid') and demo.get('errors'):
                for error in demo['errors']:
                    error_components.append(error.get('component', 'unknown'))

        if error_components:
            print(f"\nError components in demos:")
            for comp, count in Counter(error_components).most_common():
                print(f"  {comp}: {count}")


if __name__ == "__main__":
    setup_dspy()

    model_path = "backend/pseo/optimization/models/optimized_validator.json"

    if Path(model_path).exists():
        extract_prompt(model_path)
    else:
        print(f"❌ Model not found at {model_path}")
        print("Run optimization first: python3 backend/pseo/optimization/run_gepa_optimization.py")
