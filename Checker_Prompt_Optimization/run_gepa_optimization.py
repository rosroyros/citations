#!/usr/bin/env python3
"""
GEPA Optimization for APA Citation Validator
Uses F1_invalid metric to optimize prompt for detecting invalid citations
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import dspy
from dspy import Signature, InputField, OutputField
from dspy.teleprompt import GEPA
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APAValidator(Signature):
    """Validates APA 7th edition citation formatting"""
    citation = InputField(desc="Citation string with Markdown italics (_text_)")
    is_valid = OutputField(desc="true if citation follows APA 7th edition rules, false otherwise")
    explanation = OutputField(desc="Brief explanation of why the citation is valid or invalid")


class APAValidatorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(APAValidator)

    def forward(self, citation):
        result = self.predictor(citation=citation)
        return result


def load_dataset(filepath: Path) -> List[dspy.Example]:
    """Load expanded dataset from JSONL"""
    logger.info(f"Loading dataset from {filepath}")
    examples = []

    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                example = dspy.Example(
                    citation=data['citation'],
                    is_valid=str(data['is_valid']).lower(),  # Convert to string for DSPy
                    explanation=data.get('explanation', '')
                ).with_inputs('citation')
                examples.append(example)

    logger.info(f"Loaded {len(examples)} examples")
    return examples


def per_class_f1(predictions: List[str], gold_labels: List[str], target_class: str = "false") -> float:
    """
    Calculate F1 score for a specific class (default: invalid citations = "false")
    """
    tp = sum((p == target_class) and (g == target_class) for p, g in zip(predictions, gold_labels))
    fp = sum((p == target_class) and (g != target_class) for p, g in zip(predictions, gold_labels))
    fn = sum((p != target_class) and (g == target_class) for p, g in zip(predictions, gold_labels))

    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)

    return f1


def f1_invalid_metric(gold, pred, trace=None, pred_name=None, pred_trace=None) -> float:
    """
    Metric function for GEPA: F1 score for the invalid class
    GEPA requires signature: (gold, pred, trace, pred_name, pred_trace)
    """
    # Normalize predictions and gold labels
    pred_is_valid = str(pred.is_valid).lower().strip()
    gold_is_valid = str(gold.is_valid).lower().strip()

    # For single example, return 1.0 if correct, 0.0 if wrong
    # This allows GEPA to aggregate across batches
    return 1.0 if pred_is_valid == gold_is_valid else 0.0


def evaluate_model(model: dspy.Module, examples: List[dspy.Example]) -> Dict:
    """Evaluate model on examples and compute detailed metrics"""
    predictions = []
    gold_labels = []

    for example in examples:
        try:
            pred = model(citation=example.citation)
            pred_label = str(pred.is_valid).lower().strip()
            predictions.append(pred_label)
            gold_labels.append(example.is_valid)
        except Exception as e:
            logger.warning(f"Prediction failed: {e}")
            predictions.append("unknown")
            gold_labels.append(example.is_valid)

    # Overall accuracy
    accuracy = sum(p == g for p, g in zip(predictions, gold_labels)) / len(predictions)

    # Per-class metrics
    f1_invalid = per_class_f1(predictions, gold_labels, target_class="false")
    f1_valid = per_class_f1(predictions, gold_labels, target_class="true")

    # Confusion matrix
    tp_invalid = sum((p == "false") and (g == "false") for p, g in zip(predictions, gold_labels))
    fp_invalid = sum((p == "false") and (g == "true") for p, g in zip(predictions, gold_labels))
    tn_invalid = sum((p == "true") and (g == "true") for p, g in zip(predictions, gold_labels))
    fn_invalid = sum((p == "true") and (g == "false") for p, g in zip(predictions, gold_labels))

    return {
        'accuracy': accuracy,
        'f1_invalid': f1_invalid,
        'f1_valid': f1_valid,
        'tp_invalid': tp_invalid,
        'fp_invalid': fp_invalid,
        'tn_invalid': tn_invalid,
        'fn_invalid': fn_invalid,
        'total': len(predictions)
    }


def split_dataset(examples: List[dspy.Example],
                  train_ratio: float = 0.8,
                  seed: int = 42) -> Tuple[List[dspy.Example], List[dspy.Example]]:
    """Split dataset into train/validation"""
    random.seed(seed)
    shuffled = examples.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * train_ratio)
    train = shuffled[:split_idx]
    val = shuffled[split_idx:]

    logger.info(f"Split: {len(train)} train, {len(val)} validation")
    return train, val


def optimize_prompt(
    train_examples: List[dspy.Example],
    val_examples: List[dspy.Example],
    output_dir: Path,
    num_iterations: int = 30,
    beam_width: int = 4
):
    """Run MIPRO optimization"""

    logger.info("Initializing DSPy with models:")
    logger.info("  Task model: gpt-4o-mini (for candidate evaluation)")
    logger.info("  Reflection model: gpt-4o (for prompt optimization)")

    # Configure DSPy models
    # Task model: used for validation predictions during optimization
    task_lm = dspy.LM(model='openai/gpt-4o-mini', max_tokens=500, temperature=0.0)

    # Reflection model: used by GEPA for generating prompt improvements
    reflection_lm = dspy.LM(model='openai/gpt-4o', max_tokens=1000, temperature=1.0)

    # Set task model as default
    dspy.configure(lm=task_lm)

    # Initialize module
    validator = APAValidatorModule()

    logger.info(f"Starting GEPA optimization:")
    logger.info(f"  Depth (iterations): {num_iterations}")
    logger.info(f"  Breadth (beam width): {beam_width}")
    logger.info(f"  Train examples: {len(train_examples)}")
    logger.info(f"  Val examples: {len(val_examples)}")

    # Run GEPA
    # auto='medium' balances exploration vs compute cost
    optimizer = GEPA(
        metric=f1_invalid_metric,
        reflection_lm=reflection_lm,  # Use gpt-4o for optimization reasoning
        auto='medium'  # GEPA automation level: light/medium/heavy
    )

    try:
        optimized_module = optimizer.compile(
            student=validator,
            trainset=train_examples,
            valset=val_examples
        )

        logger.info("✅ Optimization complete!")

        # Evaluate optimized model
        logger.info("Evaluating optimized model on validation set...")
        val_metrics = evaluate_model(optimized_module, val_examples)

        logger.info(f"📊 Validation Metrics:")
        logger.info(f"  Accuracy: {val_metrics['accuracy']:.3f}")
        logger.info(f"  F1 (invalid): {val_metrics['f1_invalid']:.3f}")
        logger.info(f"  F1 (valid): {val_metrics['f1_valid']:.3f}")

        # Save optimized module
        output_dir.mkdir(parents=True, exist_ok=True)
        optimized_module.save(str(output_dir / "optimized_validator.json"))
        logger.info(f"💾 Saved optimized module to {output_dir / 'optimized_validator.json'}")

        # Save metrics
        with open(output_dir / "optimization_metrics.json", 'w') as f:
            json.dump(val_metrics, f, indent=2)

        return optimized_module, val_metrics

    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent
    data_file = base_dir / "final_merged_dataset.jsonl"
    output_dir = base_dir / "optimized_output"

    # Check files
    if not data_file.exists():
        logger.error(f"Dataset not found: {data_file}")
        logger.error("Run synthetic_expansion.py first!")
        sys.exit(1)

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Load and split dataset
    examples = load_dataset(data_file)
    train, val = split_dataset(examples, train_ratio=0.8, seed=42)

    # Run optimization
    optimize_prompt(
        train_examples=train,
        val_examples=val,
        output_dir=output_dir,
        num_iterations=30,
        beam_width=4
    )

    logger.info("✨ Done!")
