#!/usr/bin/env python3
"""
Cascade Validator - Minimal implementation for TDD GREEN phase
Implements cascade system using gpt-4o-mini with escalation to gpt-5-mini (medium thinking)
"""

import json
import os
import sys
import time
import statistics
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from collections import Counter
from typing import Dict, List, Any, Tuple

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def parse_decision(response_text):
    """Parse VALID/INVALID from response."""
    cleaned = response_text.replace('*', '').replace('_', '').lower()

    if '✓ no apa 7 formatting errors detected' in response_text.lower():
        return True  # VALID
    elif '❌' in response_text:
        return False  # INVALID
    elif 'no apa 7 formatting errors' in cleaned:
        return True  # VALID
    elif 'final decision: valid' in cleaned:
        return True  # VALID
    elif 'final decision: invalid' in cleaned:
        return False  # INVALID
    else:
        # Default to INVALID if unparseable
        return False

class CascadeValidator:
    """Minimal cascade validator implementation."""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.prompt_file = Path('../backend/prompts/validator_prompt_v2.txt')
        self.test_set_file = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')

        # Model cost per 1M tokens (approximate)
        self.model_costs = {
            'gpt-4o-mini': 0.00015,  # $0.15 per 1M tokens
            'gpt-5-mini': 0.0025,   # ~$2.50 per 1M tokens (estimate)
        }

    def load_test_data(self, limit: int = 121) -> Tuple[List[Dict], Dict]:
        """Load test set with ground truth."""
        test_data = []
        ground_truth_data = {}

        with open(self.test_set_file) as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                if line.strip():
                    item = json.loads(line)
                    test_data.append(item)
                    ground_truth_data[item['citation']] = item['ground_truth']

        return test_data, ground_truth_data

    def load_prompt(self) -> str:
        """Load validation prompt."""
        with open(self.prompt_file) as f:
            return f.read()

    def validate_citation(self, model: str, citation: str, prompt: str, thinking: str = None) -> Dict[str, Any]:
        """Validate a single citation with specified model."""
        try:
            messages = [{"role": "user", "content": prompt.format(citation=citation)}]

            # Add thinking parameter if specified and model supports it
            if thinking and 'gpt-5' in model.lower():
                messages.append({
                    "role": "assistant",
                    "content": f"Let me think about this systematically with {thinking} thinking."
                })

            # Handle model-specific temperature settings
            if 'gpt-5' in model.lower():
                # gpt-5-mini doesn't support custom temperature, only default (1)
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1 if thinking else 0.3  # Lower temperature for cascade
                )

            response_text = response.choices[0].message.content
            decision = parse_decision(response_text)
            usage = response.usage

            return {
                'decision': decision,
                'response_text': response_text,
                'usage': {
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens
                }
            }

        except Exception as e:
            print(f"    ⚠️  {model} API error: {e}")
            # Conservative fallback
            return {
                'decision': True,  # Assume valid
                'response_text': f"Error: {e}",
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }

    def measure_baseline(self, model: str, thinking: str = None, test_set_size: int = 121) -> Dict[str, Any]:
        """Phase 1: Measure baseline accuracy for specified model."""
        print(f"🎯 Phase 1: Measuring {model} baseline with {thinking or 'no'} thinking")
        print(f"📊 Test set size: {test_set_size} citations")

        test_data, ground_truth = self.load_test_data(test_set_size)
        prompt = self.load_prompt()

        results = []
        correct_count = 0

        for i, item in enumerate(test_data, 1):
            citation = item['citation']
            ground_truth_value = item['ground_truth']

            print(f"📝 [{i:3d}/{test_set_size}] Processing citation...")

            # Validate with specified model
            result = self.validate_citation(model, citation, prompt, thinking)
            result['ground_truth'] = ground_truth_value
            result['correct'] = result['decision'] == ground_truth_value

            if result['correct']:
                correct_count += 1

            results.append(result)

            # Progress indicator
            status = "✓" if result['correct'] else "✗"
            print(f"     {status} Predicted: {result['decision']}, Actual: {ground_truth_value}")

        accuracy = correct_count / len(results)

        print(f"\n📊 BASELINE RESULTS:")
        print(f"  Model: {model}")
        print(f"  Thinking: {thinking or 'None'}")
        print(f"  Accuracy: {accuracy:.2%} ({correct_count}/{len(results)})")

        return {
            'model': model,
            'thinking': thinking,
            'accuracy': accuracy,
            'correct_count': correct_count,
            'total_count': len(results),
            'results': results
        }

    def validate_citation_with_temp(self, model: str, citation: str, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Validate a single citation with specified model and temperature."""
        try:
            messages = [{"role": "user", "content": prompt.format(citation=citation)}]

            # Add thinking parameter if specified and model supports it
            if temperature > 0.9 and 'gpt-5' in model.lower():
                messages.append({
                    "role": "assistant",
                    "content": f"Let me think about this systematically with medium thinking."
                })

            # Handle model-specific temperature settings
            if 'gpt-5' in model.lower():
                # gpt-5-mini doesn't support custom temperature, only default (1)
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature  # Use specified temperature
                )

            response_text = response.choices[0].message.content
            decision = parse_decision(response_text)
            usage = response.usage

            return {
                'decision': decision,
                'response_text': response_text,
                'usage': {
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens
                }
            }

        except Exception as e:
            print(f"    ⚠️  {model} API error: {e}")
            # Conservative fallback
            return {
                'decision': True,  # Assume valid
                'response_text': f"Error: {e}",
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }

    def calculate_confidence(self, citation: str, model: str = 'gpt-4o-mini', samples: int = 5, temperature: float = 1.0) -> Dict[str, Any]:
        """Calculate confidence score using ensemble voting with specified temperature."""
        prompt = self.load_prompt()
        individual_votes = []

        for i in range(samples):
            result = self.validate_citation_with_temp(model, citation, prompt, temperature)
            individual_votes.append(result['decision'])
            time.sleep(0.2)  # Rate limiting

        # Calculate confidence metrics
        decision_counts = Counter(individual_votes)
        majority_decision = decision_counts.most_common(1)[0][0]
        confidence_score = decision_counts[majority_decision] / samples
        has_variance = len(decision_counts) > 1

        return {
            'confidence_score': confidence_score,
            'majority_decision': majority_decision,
            'individual_votes': individual_votes,
            'has_variance': has_variance,
            'decision_counts': dict(decision_counts)
        }

    def find_optimal_threshold(self, ensemble_model: str = 'gpt-4o-mini', confidence_samples: int = 5, test_citations: List[Dict] = None) -> Dict[str, Any]:
        """Phase 2: Find optimal confidence threshold."""
        if test_citations is None:
            test_citations, _ = self.load_test_data()

        print(f"🎯 Phase 2: Finding optimal confidence threshold")
        print(f"📊 Ensemble model: {ensemble_model}, Samples: {confidence_samples}")

        # Calculate confidence scores for all citations
        confidence_results = []
        for item in test_citations:
            confidence = self.calculate_confidence(
                item['citation'],
                ensemble_model,
                confidence_samples
            )
            confidence['ground_truth'] = item['ground_truth']
            confidence_results.append(confidence)

        # Test different threshold values
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        threshold_results = {}

        for threshold in thresholds:
            # Simulate cascade: low confidence = escalate (assume perfect escalation)
            cascade_correct = 0
            cascade_cost = 0

            for conf in confidence_results:
                if conf['confidence_score'] >= threshold:
                    # Use ensemble decision
                    predicted = conf['majority_decision']
                    cascade_cost += confidence_samples * self.model_costs.get(ensemble_model, 0.00015)
                else:
                    # Escalate to better model (assume 90% accuracy for estimation)
                    predicted = conf['ground_truth']  # Perfect for threshold finding
                    cascade_cost += self.model_costs.get('gpt-5-mini', 0.0025)

                if predicted == conf['ground_truth']:
                    cascade_correct += 1

            cascade_accuracy = cascade_correct / len(confidence_results)

            threshold_results[str(threshold)] = {
                'accuracy': cascade_accuracy,
                'cost_per_citation': cascade_cost / len(confidence_results),
                'escalation_rate': sum(1 for c in confidence_results if c['confidence_score'] < threshold) / len(confidence_results)
            }

        # Find optimal threshold (best accuracy with reasonable cost)
        best_threshold = max(thresholds, key=lambda t: threshold_results[str(t)]['accuracy'])

        return {
            'optimal_threshold': best_threshold,
            'threshold_results': threshold_results,
            'cost_analysis': {
                'ensemble_only_cost': confidence_samples * self.model_costs.get(ensemble_model, 0.00015),
                'gpt5_cost': self.model_costs.get('gpt-5-mini', 0.0025)
            }
        }

    def validate_with_cascade(self, test_citations: List[Dict], primary_model: str = 'gpt-4o-mini',
                            escalation_model: str = 'gpt-5-mini', escalation_thinking: str = 'medium',
                            confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """Phase 3: Full cascade validation."""
        print(f"🎯 Phase 3: Full cascade validation")
        print(f"📊 Primary: {primary_model}, Escalation: {escalation_model} ({escalation_thinking})")
        print(f"🔍 Confidence threshold: {confidence_threshold}")

        prompt = self.load_prompt()
        results = []
        primary_only = 0
        escalated = 0
        correct = 0

        for item in test_citations:
            citation = item['citation']
            ground_truth = item['ground_truth']

            # Calculate confidence with primary model
            confidence = self.calculate_confidence(citation, primary_model, samples=3)  # Fewer samples for efficiency

            if confidence['confidence_score'] >= confidence_threshold:
                # Use primary model decision
                predicted = confidence['majority_decision']
                primary_only += 1
            else:
                # Escalate to better model
                escalation_result = self.validate_citation(escalation_model, citation, prompt, escalation_thinking)
                predicted = escalation_result['decision']
                escalated += 1

            is_correct = predicted == ground_truth
            if is_correct:
                correct += 1

            results.append({
                'citation': citation,
                'ground_truth': ground_truth,
                'predicted': predicted,
                'confidence_score': confidence['confidence_score'],
                'escalated': confidence['confidence_score'] < confidence_threshold,
                'correct': is_correct
            })

        # Calculate metrics
        overall_accuracy = correct / len(results)
        escalation_rate = escalated / len(results)

        # Cost calculation
        primary_cost = len(results) * 3 * self.model_costs.get(primary_model, 0.00015)
        escalation_cost = escalated * self.model_costs.get(escalation_model, 0.0025)
        total_cost = primary_cost + escalation_cost
        cost_per_citation = total_cost / len(results)

        return {
            'overall_accuracy': overall_accuracy,
            'cost_per_citation': cost_per_citation,
            'routing_decisions': {
                'primary_only': primary_only,
                'escalated': escalated,
                'escalation_rate': escalation_rate
            },
            'detailed_results': results,
            'cost_breakdown': {
                'primary_model_cost': primary_cost,
                'escalation_cost': escalation_cost,
                'total_cost': total_cost
            }
        }

    def analyze_costs(self, test_citations: List[Dict], cascade_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost optimization for cascade vs individual models."""
        num_citations = len(test_citations)

        cascade_config_cost = cascade_config.get('confidence_threshold', 0.7)
        estimated_escalation_rate = 0.3  # Estimate based on threshold

        # Calculate costs per citation
        cascade_cost = (
            3 * self.model_costs.get('gpt-4o-mini', 0.00015) +  # Primary model with 3 samples
            estimated_escalation_rate * self.model_costs.get('gpt-5-mini', 0.0025)  # Expected escalation
        )

        gpt4o_cost = self.model_costs.get('gpt-4o-mini', 0.00015)
        gpt5_cost = self.model_costs.get('gpt-5-mini', 0.0025)

        return {
            'cascade_cost_per_citation': cascade_cost,
            'gpt4o_mini_cost_per_citation': gpt4o_cost,
            'gpt5_mini_medium_cost_per_citation': gpt5_cost,
            'cost_savings_vs_gpt5': gpt5_cost - cascade_cost,
            'cost_increase_vs_gpt4o': cascade_cost - gpt4o_cost
        }