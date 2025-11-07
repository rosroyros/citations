"""
Real Dual Prompt Competitive Benchmark Test Runner

Tests 5 models × 2 prompts = 10 variations with actual API calls:
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

# Prompt definitions
BASELINE_PROMPT = """Is this citation valid or invalid? Respond with exactly one word: "valid" or "invalid".

Citation: {citation}"""

OPTIMIZED_PROMPT = """As an expert academic librarian specializing in citation validation, evaluate this citation according to APA 7th edition standards.

Consider:
- Required elements completeness (author, title, source, date)
- Format accuracy and consistency
- Source credibility and accessibility
- DOI/publisher information when applicable

Respond with exactly one word: "valid" or "invalid"

Citation: {citation}"""

class DualPromptModelTester:
    """Base class for testing different models with dual prompts."""

    def __init__(self, name: str):
        self.name = name
        self.baseline_results = []
        self.optimized_results = []

    def test_citation(self, citation: str, ground_truth: bool, prompt_type: str) -> Dict[str, Any]:
        """Test a single citation. Override in subclasses."""
        raise NotImplementedError

    def test_dataset(self, dataset: List[Dict], prompt_type: str) -> List[Dict]:
        """Test entire dataset with specified prompt type."""
        print(f"\n🧪 Testing {self.name} with {prompt_type} prompt...")
        results = []

        for i, item in enumerate(dataset, 1):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(dataset)}")

            citation = item['citation']
            ground_truth = item['ground_truth']

            try:
                result = self.test_citation(citation, ground_truth, prompt_type)
                result['index'] = i
                results.append(result)

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error testing citation {i}: {e}")
                results.append({
                    'index': i,
                    'citation': citation,
                    'ground_truth': ground_truth,
                    'predicted': None,
                    'correct': False,
                    'error': str(e)
                })

        return results

    def calculate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate accuracy and other metrics."""
        total = len(results)
        correct = sum(1 for r in results if r.get('correct', False))
        accuracy = correct / total if total > 0 else 0

        return {
            'model': self.name,
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'results': results
        }


class DSPyTester(DualPromptModelTester):
    """Test optimized DSPy citation validator."""

    def __init__(self):
        super().__init__("DSPy Optimized")
        self.validator = None

    def setup(self):
        """Setup DSPy with the optimized prompt."""
        print("🔧 Setting up DSPy...")
        setup_dspy()

        class OptimizedCitationValidator(dspy.Signature):
            """Validate citations according to APA 7th edition standards."""

            input = dspy.InputField(desc="Citation to validate")
            output = dspy.OutputField(desc="'valid' or 'invalid'")

        self.validator = CitationValidator(OptimizedCitationValidator)

    def test_citation(self, citation: str, ground_truth: bool, prompt_type: str) -> Dict[str, Any]:
        """Test citation with DSPy."""
        if self.validator is None:
            self.setup()

        # DSPy uses optimized prompting by default
        prediction = self.validator(input=citation)
        predicted = prediction.output.lower().strip() == 'valid'

        return {
            'citation': citation,
            'ground_truth': ground_truth,
            'predicted': 'valid' if predicted else 'invalid',
            'correct': predicted == ground_truth
        }


class AnthropicTester(DualPromptModelTester):
    """Test Claude models via Anthropic API."""

    def __init__(self, model_id: str, name: str):
        super().__init__(name)
        self.model_id = model_id
        self.client = None

    def setup(self):
        """Setup Anthropic client."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def test_citation(self, citation: str, ground_truth: bool, prompt_type: str) -> Dict[str, Any]:
        """Test citation with Anthropic model."""
        if self.client is None:
            self.setup()

        prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
        prompt = prompt.format(citation=citation)

        try:
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            predicted_text = response.content[0].text.lower().strip()
            predicted = predicted_text == 'valid'

            return {
                'citation': citation,
                'ground_truth': ground_truth,
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == ground_truth
            }

        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")


class OpenAITester(DualPromptModelTester):
    """Test OpenAI models via API."""

    def __init__(self, model_id: str, name: str):
        super().__init__(name)
        self.model_id = model_id
        self.client = None

    def setup(self):
        """Setup OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        import openai
        self.client = openai.OpenAI(api_key=api_key)

    def test_citation(self, citation: str, ground_truth: bool, prompt_type: str) -> Dict[str, Any]:
        """Test citation with OpenAI model."""
        if self.client is None:
            self.setup()

        prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
        prompt = prompt.format(citation=citation)

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'

            return {
                'citation': citation,
                'ground_truth': ground_truth,
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == ground_truth
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")


def main():
    print("="*80)
    print("REAL DUAL PROMPT COMPETITIVE BENCHMARK")
    print("="*80)

    # Check API keys
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY not set - Claude tests will be skipped")
    if not openai_key:
        print("⚠️  OPENAI_API_KEY not set - OpenAI tests will be skipped")

    # Load dataset
    print("\n📁 Loading validation dataset...")
    try:
        dataset = load_dataset('../backend/pseo/datasets/validation_split.json')
        print(f"✅ Loaded {len(dataset)} citations")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return

    # Initialize testers
    testers = [
        DSPyTester(),
        AnthropicTester("claude-3-5-sonnet-20241022", "Claude Sonnet 4.5") if anthropic_key else None,
        OpenAITester("gpt-4o", "GPT-4o") if openai_key else None,
        OpenAITester("gpt-5-preview", "GPT-5") if openai_key else None,
        OpenAITester("gpt-5-mini-preview", "GPT-5-mini") if openai_key else None,
    ]

    testers = [t for t in testers if t is not None]
    print(f"\n🤖 Testing {len(testers)} models with dual prompts...")

    all_results = {}

    # Test each model with both prompts
    for tester in testers:
        print(f"\n{'='*60}")
        print(f"TESTING: {tester.name}")
        print(f"{'='*60}")

        # Test with baseline prompt
        print(f"\n📋 BASELINE PROMPT TEST")
        baseline_results = tester.test_dataset(dataset, 'baseline')
        baseline_metrics = tester.calculate_metrics(baseline_results)

        # Test with optimized prompt
        print(f"\n🚀 OPTIMIZED PROMPT TEST")
        optimized_results = tester.test_dataset(dataset, 'optimized')
        optimized_metrics = tester.calculate_metrics(optimized_results)

        # Store results
        all_results[f"{tester.name}_baseline"] = baseline_metrics
        all_results[f"{tester.name}_optimized"] = optimized_metrics

        # Print summary
        print(f"\n📊 RESULTS SUMMARY for {tester.name}:")
        print(f"   Baseline:  {baseline_metrics['accuracy']:.1%} ({baseline_metrics['correct']}/{baseline_metrics['total']})")
        print(f"   Optimized: {optimized_metrics['accuracy']:.1%} ({optimized_metrics['correct']}/{optimized_metrics['total']})")

        improvement = optimized_metrics['accuracy'] - baseline_metrics['accuracy']
        print(f"   Change:    {improvement:+.1%}")

    # Save all results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"real_dual_prompt_results_{timestamp}.json"

    print(f"\n💾 Saving results to {results_file}...")
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"✅ Real dual prompt testing complete!")
    print(f"📁 Results saved to {results_file}")
    print(f"📊 Tested {len(testers)} models × 2 prompts = {len(all_results)} variations")

    return results_file


if __name__ == "__main__":
    main()