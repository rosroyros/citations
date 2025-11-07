"""
Competitive Benchmark Test Runner

Tests 5 models on validation set:
1. Optimized DSPy checker (local)
2. Claude Sonnet 4.5 (Anthropic API)
3. GPT-4o (OpenAI API)
4. GPT-5 (OpenAI API)
5. GPT-5-mini (OpenAI API)

Requirements:
- pip install anthropic openai dspy-ai
- Set API keys as environment variables:
  - ANTHROPIC_API_KEY
  - OPENAI_API_KEY
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import dspy

# Add parent directories to path for imports
sys.path.append('../backend/pseo/optimization')
sys.path.append('../backend/pseo')

try:
    from dspy_validator import CitationValidator, load_dataset
    from dspy_config import setup_dspy
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the competitive_benchmark directory and DSPy is installed")
    sys.exit(1)


class ModelTester:
    """Base class for testing different models."""

    def __init__(self, name: str):
        self.name = name
        self.results = []

    def test_citation(self, citation: str, ground_truth: bool) -> Dict[str, Any]:
        """Test a single citation. Override in subclasses."""
        raise NotImplementedError

    def test_dataset(self, dataset: List[Dict]) -> List[Dict]:
        """Test entire dataset."""
        print(f"\n🧪 Testing {self.name}...")
        results = []

        for i, example in enumerate(dataset, 1):
            citation = example['citation']
            ground_truth = example['is_valid']

            print(f"  [{i}/{len(dataset)}] Testing: {citation[:60]}...")

            try:
                result = self.test_citation(citation, ground_truth)
                result['citation_id'] = example.get('citation_id', f"cit_{i}")
                result['citation'] = citation
                result['ground_truth'] = ground_truth
                results.append(result)

                # Show brief status
                status = "✓" if result['predicted_valid'] == ground_truth else "✗"
                print(f"    {status} Predicted: {result['predicted_valid']}, Truth: {ground_truth}")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                error_result = {
                    'citation_id': example.get('citation_id', f"cit_{i}"),
                    'citation': citation,
                    'ground_truth': ground_truth,
                    'predicted_valid': None,
                    'explanation': f"Error: {str(e)}",
                    'error': True
                }
                results.append(error_result)

        self.results = results
        return results

    def save_results(self, filename: str):
        """Save results to JSONL file."""
        with open(filename, 'w') as f:
            for result in self.results:
                f.write(json.dumps(result) + '\n')
        print(f"✅ Results saved to {filename}")


class DSPyOptimizedTester(ModelTester):
    """Test the optimized DSPy model."""

    def __init__(self):
        super().__init__("DSPy Optimized")
        # Load the optimized model
        self.validator = CitationValidator()
        model_path = '../backend/pseo/optimization/models/optimized_validator.json'

        if Path(model_path).exists():
            try:
                self.validator.load(model_path)
                print(f"✅ Loaded optimized DSPy model from {model_path}")
            except Exception as e:
                print(f"⚠️  Could not load optimized model: {e}")
                print("    Using unoptimized DSPy model instead")
        else:
            print(f"⚠️  Optimized model not found at {model_path}")
            print("    Using unoptimized DSPy model")

    def test_citation(self, citation: str, ground_truth: bool) -> Dict[str, Any]:
        """Test citation with DSPy model."""
        prediction = self.validator(citation=citation)

        return {
            'predicted_valid': prediction.is_valid,
            'explanation': f"Source type: {prediction.source_type}, Errors: {len(prediction.errors)}",
            'source_type': prediction.source_type,
            'errors': prediction.errors
        }


class ClaudeTester(ModelTester):
    """Test Claude Sonnet 4.5 via Anthropic API."""

    def __init__(self):
        super().__init__("Claude Sonnet 4.5")
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            print("✅ Initialized Anthropic client")
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")

    def test_citation(self, citation: str, ground_truth: bool) -> Dict[str, Any]:
        """Test citation with Claude."""
        prompt = f"""Please verify if this citation matches the APA 7th edition standard. Respond with: is_valid (true/false), explanation (brief)

Citation: {citation}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Parse response
            is_valid = None
            explanation = content

            # Look for true/false in response
            if 'true' in content.lower():
                is_valid = True
            elif 'false' in content.lower():
                is_valid = False

            return {
                'predicted_valid': is_valid,
                'explanation': explanation,
                'raw_response': content
            }

        except Exception as e:
            return {
                'predicted_valid': None,
                'explanation': f"API Error: {str(e)}",
                'error': True
            }


class GPTTester(ModelTester):
    """Test GPT models via OpenAI API."""

    def __init__(self, model_name: str):
        super().__init__(f"GPT {model_name}")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model_name = model_name
            print(f"✅ Initialized OpenAI client for {model_name}")
        except ImportError:
            raise ImportError("Install openai: pip install openai")

    def test_citation(self, citation: str, ground_truth: bool) -> Dict[str, Any]:
        """Test citation with GPT."""
        prompt = f"""Please verify if this citation matches the APA 7th edition standard. Respond with: is_valid (true/false), explanation (brief)

Citation: {citation}"""

        try:
            model_id = {
                "4o": "gpt-4o",
                "5": "gpt-5-preview",  # Adjust if different model name
                "5-mini": "gpt-5-mini-preview"  # GPT-5-mini model
            }.get(self.model_name, f"gpt-{self.model_name}")

            response = self.client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            is_valid = None
            explanation = content

            # Look for true/false in response
            if 'true' in content.lower():
                is_valid = True
            elif 'false' in content.lower():
                is_valid = False

            return {
                'predicted_valid': is_valid,
                'explanation': explanation,
                'raw_response': content
            }

        except Exception as e:
            return {
                'predicted_valid': None,
                'explanation': f"API Error: {str(e)}",
                'error': True
            }


def main():
    print("="*80)
    print("COMPETITIVE BENCHMARK TEST RUNNER")
    print("="*80)

    # Load validation set
    validation_file = Path("validation_set.jsonl")
    if not validation_file.exists():
        print(f"❌ Validation set not found: {validation_file}")
        print("Run extract_validation_set.py first")
        return

    print(f"\n📁 Loading validation set from {validation_file}")
    dataset = []
    with open(validation_file, 'r') as f:
        for line in f:
            dataset.append(json.loads(line.strip()))

    print(f"✅ Loaded {len(dataset)} citations")

    # Count valid/invalid
    valid_count = sum(1 for ex in dataset if ex['is_valid'])
    invalid_count = len(dataset) - valid_count
    print(f"   Valid: {valid_count}, Invalid: {invalid_count}")

    # Initialize testers
    testers = []

    # 1. DSPy Optimized
    try:
        testers.append(DSPyOptimizedTester())
    except Exception as e:
        print(f"⚠️  Could not initialize DSPy tester: {e}")

    # 2. Claude Sonnet 4.5
    try:
        testers.append(ClaudeTester())
    except Exception as e:
        print(f"⚠️  Could not initialize Claude tester: {e}")

    # 3. GPT-4o
    try:
        testers.append(GPTTester("4o"))
    except Exception as e:
        print(f"⚠️  Could not initialize GPT-4o tester: {e}")

    # 4. GPT-5 (if available)
    try:
        testers.append(GPTTester("5"))
    except Exception as e:
        print(f"⚠️  Could not initialize GPT-5 tester: {e}")

    # 5. GPT-5-mini (if available)
    try:
        testers.append(GPTTester("5-mini"))
    except Exception as e:
        print(f"⚠️  Could not initialize GPT-5-mini tester: {e}")

    if not testers:
        print("❌ No testers could be initialized. Check API keys and dependencies.")
        return

    print(f"\n🚀 Running benchmarks with {len(testers)} models...")

    # Run tests
    all_results = {}
    start_time = time.time()

    for tester in testers:
        try:
            results = tester.test_dataset(dataset)
            all_results[tester.name] = results

            # Save individual results
            filename = f"{tester.name.lower().replace(' ', '_')}_results.jsonl"
            tester.save_results(filename)

            # Show quick summary
            correct = sum(1 for r in results if r.get('predicted_valid') == r.get('ground_truth'))
            accuracy = correct / len(results) if results else 0
            print(f"   Accuracy: {accuracy:.1%} ({correct}/{len(results)})")

        except Exception as e:
            print(f"❌ Error testing {tester.name}: {e}")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total testing time: {elapsed:.1f} seconds")

    # Save summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'dataset_size': len(dataset),
        'valid_citations': valid_count,
        'invalid_citations': invalid_count,
        'models_tested': list(all_results.keys()),
        'total_time_seconds': elapsed
    }

    with open('benchmark_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print("✅ Benchmark complete!")
    print(f"📊 Summary saved to benchmark_summary.json")
    print(f"📁 Individual results saved to *_results.jsonl files")


if __name__ == "__main__":
    main()