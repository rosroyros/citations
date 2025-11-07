"""
Calculate performance metrics for competitive benchmark models.

Computes accuracy, precision, recall, F1 score, and confusion matrices for each model.
Also performs citation-level analysis to identify patterns and compare models.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter


def load_model_results(filename: str) -> List[Dict]:
    """Load model results from JSONL file."""
    results = []
    with open(filename, 'r') as f:
        for line in f:
            results.append(json.loads(line.strip()))
    return results


def calculate_confusion_matrix(predictions: List[bool], ground_truth: List[bool]) -> Dict[str, int]:
    """
    Calculate confusion matrix for binary classification.

    Args:
        predictions: List of predicted values (True/False)
        ground_truth: List of ground truth values (True/False)

    Returns:
        Dictionary with TP, FP, TN, FN counts
    """
    tp = fp = tn = fn = 0

    for pred, truth in zip(predictions, ground_truth):
        if pred and truth:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif not pred and not truth:
            tn += 1
        else:  # not pred and truth
            fn += 1

    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def calculate_metrics(confusion_matrix: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate precision, recall, F1 score from confusion matrix.

    Focuses on the "invalid" class (positive class = invalid/False)
    """
    tp = confusion_matrix["tp"]  # Correctly identified as invalid
    fp = confusion_matrix["fp"]  # Incorrectly marked as invalid
    tn = confusion_matrix["tn"]  # Correctly identified as valid
    fn = confusion_matrix["fn"]  # Incorrectly marked as valid

    # For invalid class detection:
    # TP = correctly identified invalid citations
    # FP = valid citations incorrectly marked as invalid
    # TN = correctly identified valid citations
    # FN = invalid citations incorrectly marked as valid

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn
    }


def analyze_citation_patterns(all_results: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    Analyze patterns across models and citations.

    Args:
        all_results: Dictionary mapping model names to their results

    Returns:
        Analysis including common failures, agreements, and citation-level insights
    """
    models = list(all_results.keys())
    citations_count = len(all_results[models[0]])

    # Citation-level analysis
    citation_analysis = []
    agreement_counts = Counter()

    for i in range(citations_count):
        citation_data = {
            "index": i,
            "citation": all_results[models[0]][i]["citation"],
            "ground_truth": all_results[models[0]][i]["ground_truth"],
            "model_predictions": {},
            "correct_count": 0,
            "total_models": len(models)
        }

        # Collect predictions from all models
        for model in models:
            result = all_results[model][i]
            pred = result.get("predicted_valid")
            citation_data["model_predictions"][model] = {
                "predicted": pred,
                "explanation": result.get("explanation", ""),
                "correct": pred == citation_data["ground_truth"] if pred is not None else False
            }
            if citation_data["model_predictions"][model]["correct"]:
                citation_data["correct_count"] += 1

        # Count agreement level
        correct_models = [m for m in models if citation_data["model_predictions"][m]["correct"]]
        agreement_key = f"{len(correct_models)}/{len(models)} correct"
        agreement_counts[agreement_key] += 1

        # Check if all models agree
        all_predictions = [citation_data["model_predictions"][m]["predicted"] for m in models if citation_data["model_predictions"][m]["predicted"] is not None]
        if all_predictions and len(set(all_predictions)) == 1:
            citation_data["all_models_agree"] = True
            citation_data["agreement_prediction"] = all_predictions[0]
            citation_data["agreement_correct"] = all_predictions[0] == citation_data["ground_truth"]
        else:
            citation_data["all_models_agree"] = False
            citation_data["agreement_prediction"] = None
            citation_data["agreement_correct"] = False

        citation_analysis.append(citation_data)

    # Model comparison matrix
    model_comparison = {}
    for i, model1 in enumerate(models):
        model_comparison[model1] = {}
        for j, model2 in enumerate(models):
            if i == j:
                model_comparison[model1][model2] = 1.0  # Perfect agreement with self
            else:
                # Calculate agreement rate between two models
                agreement = 0
                total = 0
                for k in range(citations_count):
                    pred1 = all_results[model1][k].get("predicted_valid")
                    pred2 = all_results[model2][k].get("predicted_valid")
                    if pred1 is not None and pred2 is not None:
                        total += 1
                        if pred1 == pred2:
                            agreement += 1

                model_comparison[model1][model2] = agreement / total if total > 0 else 0.0

    # Error pattern analysis
    error_patterns = {}
    for model in models:
        errors = []
        for i, result in enumerate(all_results[model]):
            if not result.get("predicted_valid") == result.get("ground_truth"):
                errors.append({
                    "citation_index": i,
                    "citation": result["citation"][:100] + "...",
                    "ground_truth": result["ground_truth"],
                    "predicted": result.get("predicted_valid"),
                    "explanation": result.get("explanation", "")
                })
        error_patterns[model] = errors

    return {
        "citation_analysis": citation_analysis,
        "agreement_distribution": dict(agreement_counts),
        "model_comparison_matrix": model_comparison,
        "error_patterns": error_patterns,
        "total_citations": citations_count,
        "models_tested": models
    }


def main():
    print("="*80)
    print("CALCULATING METRICS FOR COMPETITIVE BENCHMARK")
    print("="*80)

    # Define model files
    model_files = {
        "DSPy Optimized": "dspy_optimized_results.jsonl",
        "Claude Sonnet 4.5": "claude_sonnet_4.5_results.jsonl",
        "GPT-4o": "gpt-4o_results.jsonl",
        "GPT-5": "gpt-5_results.jsonl",
        "GPT-5-mini": "gpt-5-mini_results.jsonl"
    }

    # Load all model results
    all_results = {}
    available_models = []

    for model_name, filename in model_files.items():
        if Path(filename).exists():
            print(f"📁 Loading {model_name} results from {filename}")
            all_results[model_name] = load_model_results(filename)
            available_models.append(model_name)
        else:
            print(f"⚠️  File not found: {filename}")

    if not all_results:
        print("❌ No result files found!")
        return

    print(f"✅ Loaded results for {len(available_models)} models")

    # Calculate metrics for each model
    model_metrics = {}

    print(f"\n📊 Calculating performance metrics...")

    for model_name, results in all_results.items():
        print(f"\n🔍 Analyzing {model_name}...")

        # Extract predictions and ground truth
        predictions = []
        ground_truth = []

        for result in results:
            pred = result.get("predicted_valid")
            if pred is not None:  # Only include valid predictions
                predictions.append(pred)
                ground_truth.append(result["ground_truth"])

        if not predictions:
            print(f"   ⚠️  No valid predictions found for {model_name}")
            continue

        # Calculate confusion matrix and metrics
        confusion_matrix = calculate_confusion_matrix(predictions, ground_truth)
        metrics = calculate_metrics(confusion_matrix)

        # Store metrics
        model_metrics[model_name] = {
            **metrics,
            "total_predictions": len(predictions),
            "invalid_citations": sum(1 for t in ground_truth if not t),
            "valid_citations": sum(1 for t in ground_truth if t)
        }

        # Print summary
        print(f"   Accuracy: {metrics['accuracy']:.1%}")
        print(f"   Precision (invalid): {metrics['precision']:.1%}")
        print(f"   Recall (invalid): {metrics['recall']:.1%}")
        print(f"   F1 Score (invalid): {metrics['f1']:.3f}")
        print(f"   Confusion Matrix: TP={metrics['tp']}, FP={metrics['fp']}, TN={metrics['tn']}, FN={metrics['fn']}")

    # Citation-level analysis
    print(f"\n🔍 Performing citation-level analysis...")
    citation_analysis = analyze_citation_patterns(all_results)

    # Find best and worst performing citations
    all_citations = citation_analysis["citation_analysis"]

    # Citations all models got right
    universal_success = [c for c in all_citations if c["correct_count"] == len(available_models)]
    # Citations all models got wrong
    universal_failure = [c for c in all_citations if c["correct_count"] == 0]

    print(f"   Citations all models got right: {len(universal_success)}")
    print(f"   Citations all models got wrong: {len(universal_failure)}")

    # Model ranking
    print(f"\n🏆 Model Ranking (by F1 Score):")
    sorted_models = sorted(
        model_metrics.items(),
        key=lambda x: x[1]["f1"],
        reverse=True
    )

    for i, (model, metrics) in enumerate(sorted_models, 1):
        print(f"   {i}. {model}: F1={metrics['f1']:.3f}, Acc={metrics['accuracy']:.1%}")

    # Create comprehensive summary
    summary = {
        "timestamp": "2025-11-06 20:50:00",
        "dataset_info": {
            "total_citations": len(all_citations),
            "valid_citations": all_citations[0]["ground_truth"] == True if all_citations else 0,
            "invalid_citations": all_citations[0]["ground_truth"] == False if all_citations else 0,
            "models_tested": available_models
        },
        "model_metrics": model_metrics,
        "model_ranking": [
            {"rank": i+1, "model": model, **metrics}
            for i, (model, metrics) in enumerate(sorted_models)
        ],
        "citation_analysis": {
            "universal_success_count": len(universal_success),
            "universal_failure_count": len(universal_failure),
            "agreement_distribution": citation_analysis["agreement_distribution"],
            "model_agreement_matrix": citation_analysis["model_comparison_matrix"]
        },
        "error_analysis": {
            model: len(errors) for model, errors in citation_analysis["error_patterns"].items()
        },
        "insights": {
            "best_model": sorted_models[0][0] if sorted_models else None,
            "accuracy_range": [
                min(m["accuracy"] for m in model_metrics.values()),
                max(m["accuracy"] for m in model_metrics.values())
            ] if model_metrics else [0, 0],
            "average_agreement": sum(
                citation_analysis["model_comparison_matrix"][m1][m2]
                for i, m1 in enumerate(available_models)
                for j, m2 in enumerate(available_models)
                if i != j
            ) / (len(available_models) * (len(available_models) - 1)) if len(available_models) > 1 else 1.0
        }
    }

    # Save comprehensive results
    with open('metrics_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    # Save citation-level analysis
    with open('citation_analysis.json', 'w') as f:
        json.dump(citation_analysis, f, indent=2)

    print(f"\n✅ Metrics calculation complete!")
    print(f"📊 Summary saved to metrics_summary.json")
    print(f"📋 Citation analysis saved to citation_analysis.json")
    print(f"📝 Detailed citation appendix available (see citation_appendix.md)")

    # Show key insights
    print(f"\n🎯 Key Insights:")
    if sorted_models:
        best_model = sorted_models[0][0]
        best_f1 = sorted_models[0][1]["f1"]
        worst_model = sorted_models[-1][0]
        worst_f1 = sorted_models[-1][1]["f1"]

        print(f"   • Best performer: {best_model} (F1: {best_f1:.3f})")
        print(f"   • Performance gap: {best_f1 - worst_f1:.3f} F1 points")
        print(f"   • Average model agreement: {summary['insights']['average_agreement']:.1%}")
        print(f"   • Citations with universal agreement: {len([c for c in all_citations if c['all_models_agree']])}/{len(all_citations)}")


if __name__ == "__main__":
    main()