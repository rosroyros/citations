"""
Create comprehensive citation appendix showing ground truth and all model results.

Generates a detailed table with all 121 citations and their evaluation by each model.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


def load_model_results(filename: str) -> List[Dict]:
    """Load model results from JSONL file."""
    results = []
    with open(filename, 'r') as f:
        for line in f:
            results.append(json.loads(line.strip()))
    return results


def create_citation_appendix():
    """Create comprehensive citation appendix."""

    # Load all model results
    model_files = {
        "DSPy Optimized": "dspy_optimized_results.jsonl",
        "Claude Sonnet 4.5": "claude_sonnet_4.5_results.jsonl",
        "GPT-4o": "gpt-4o_results.jsonl",
        "GPT-5": "gpt-5_results.jsonl",
        "GPT-5-mini": "gpt-5-mini_results.jsonl"
    }

    all_results = {}
    for model_name, filename in model_files.items():
        if Path(filename).exists():
            all_results[model_name] = load_model_results(filename)

    if not all_results:
        print("❌ No result files found!")
        return

    models = list(all_results.keys())
    citations_count = len(all_results[models[0]])

    print("="*80)
    print("CREATING COMPREHENSIVE CITATION APPENDIX")
    print("="*80)
    print(f"📋 Processing {citations_count} citations from {len(models)} models...")

    # Create appendix data
    appendix_data = []

    for i in range(citations_count):
        citation_entry = {
            "index": i + 1,
            "citation": all_results[models[0]][i]["citation"],
            "ground_truth": all_results[models[0]][i]["ground_truth"],
            "model_results": {},
            "summary": {
                "correct_predictions": 0,
                "total_models": len(models),
                "agreement_level": None,
                "all_correct": False,
                "all_wrong": False
            }
        }

        # Collect results from all models
        correct_count = 0
        predictions = []

        for model in models:
            result = all_results[model][i]
            predicted = result.get("predicted_valid")
            explanation = result.get("explanation", "")

            is_correct = predicted == citation_entry["ground_truth"] if predicted is not None else False

            citation_entry["model_results"][model] = {
                "predicted": predicted,
                "explanation": explanation,
                "correct": is_correct
            }

            if is_correct:
                correct_count += 1

            if predicted is not None:
                predictions.append(predicted)

        # Update summary
        citation_entry["summary"]["correct_predictions"] = correct_count
        citation_entry["summary"]["agreement_level"] = f"{correct_count}/{len(models)}"
        citation_entry["summary"]["all_correct"] = correct_count == len(models)
        citation_entry["summary"]["all_wrong"] = correct_count == 0

        # Check if all predictions agree
        if predictions and len(set(predictions)) == 1:
            citation_entry["summary"]["unanimous_prediction"] = predictions[0]
            citation_entry["summary"]["unanimous_correct"] = predictions[0] == citation_entry["ground_truth"]
        else:
            citation_entry["summary"]["unanimous_prediction"] = None
            citation_entry["summary"]["unanimous_correct"] = False

        appendix_data.append(citation_entry)

    # Generate statistics
    stats = {
        "total_citations": citations_count,
        "models": models,
        "unanimous_correct": sum(1 for c in appendix_data if c["summary"].get("unanimous_correct", False)),
        "unanimous_wrong": sum(1 for c in appendix_data if c["summary"].get("unanimous_prediction") is not None and not c["summary"].get("unanimous_correct", False) and not any(r["correct"] for r in c["model_results"].values())),
        "disagreements": sum(1 for c in appendix_data if not c["summary"].get("unanimous_prediction")),
        "agreement_distribution": {}
    }

    # Calculate agreement distribution
    for c in appendix_data:
        level = c["summary"]["agreement_level"]
        stats["agreement_distribution"][level] = stats["agreement_distribution"].get(level, 0) + 1

    # Save appendix data
    appendix = {
        "metadata": {
            "title": "Competitive Benchmark Citation Appendix",
            "description": "Complete results showing ground truth and all model predictions for each citation",
            "generated_at": "2025-11-06 21:00:00",
            "total_citations": citations_count,
            "models_tested": models
        },
        "statistics": stats,
        "citations": appendix_data
    }

    with open('citation_appendix.json', 'w') as f:
        json.dump(appendix, f, indent=2)

    # Create markdown version for readability
    create_markdown_appendix(appendix)

    print(f"✅ Citation appendix created!")
    print(f"📊 Statistics:")
    print(f"   • Total citations: {stats['total_citations']}")
    print(f"   • Unanimous correct: {stats['unanimous_correct']} ({stats['unanimous_correct']/stats['total_citations']*100:.1f}%)")
    print(f"   • Unanimous wrong: {stats['unanimous_wrong']} ({stats['unanimous_wrong']/stats['total_citations']*100:.1f}%)")
    print(f"   • Disagreements: {stats['disagreements']} ({stats['disagreements']/stats['total_citations']*100:.1f}%)")

    print(f"\n📋 Agreement Distribution:")
    for level, count in sorted(stats["agreement_distribution"].items()):
        percentage = count / stats['total_citations'] * 100
        print(f"   • {level} correct: {count} ({percentage:.1f}%)")

    print(f"\n📁 Files created:")
    print(f"   • citation_appendix.json - Complete structured data")
    print(f"   • citation_appendix.md - Human-readable table")


def create_markdown_appendix(appendix: Dict):
    """Create markdown version of the appendix."""

    metadata = appendix["metadata"]
    citations = appendix["citations"]
    models = metadata["models_tested"]

    with open('citation_appendix.md', 'w') as f:
        f.write("# Competitive Benchmark Citation Appendix\n\n")
        f.write(f"**Generated:** {metadata['generated_at']}  \n")
        f.write(f"**Total Citations:** {metadata['total_citations']}  \n")
        f.write(f"**Models Tested:** {', '.join(models)}  \n\n")

        # Statistics
        stats = appendix["statistics"]
        f.write("## Statistics\n\n")
        f.write(f"- **Unanimous Correct:** {stats['unanimous_correct']} ({stats['unanimous_correct']/stats['total_citations']*100:.1f}%)\n")
        f.write(f"- **Unanimous Wrong:** {stats['unanimous_wrong']} ({stats['unanimous_wrong']/stats['total_citations']*100:.1f}%)\n")
        f.write(f"- **Disagreements:** {stats['disagreements']} ({stats['disagreements']/stats['total_citations']*100:.1f}%)\n\n")

        # Agreement distribution
        f.write("### Agreement Distribution\n\n")
        f.write("| Correct/Total | Count | Percentage |\n")
        f.write("|---------------|-------|------------|\n")

        for level in sorted(stats["agreement_distribution"].keys(), key=lambda x: int(x.split('/')[0]), reverse=True):
            count = stats["agreement_distribution"][level]
            percentage = count / stats['total_citations'] * 100
            f.write(f"| {level} | {count} | {percentage:.1f}% |\n")

        f.write("\n")

        # Detailed table
        f.write("## Detailed Results\n\n")
        f.write("| # | Citation (truncated) | Ground Truth |")

        for model in models:
            model_short = model.replace(" ", "_").replace(".", "")
            f.write(f" {model_short} |")

        f.write(" Correct/Total |\n")
        f.write("|---|-------------------|--------------|")

        for model in models:
            f.write("--------|")

        f.write("-------------|\n")

        for citation in citations:
            idx = citation["index"]
            citation_text = citation["citation"][:60] + "..." if len(citation["citation"]) > 60 else citation["citation"]
            ground_truth = "✓" if citation["ground_truth"] else "✗"
            correct_total = citation["summary"]["agreement_level"]

            # Escape markdown special characters in citation
            citation_text = citation_text.replace("|", "\\|").replace("\n", " ")

            f.write(f"| {idx} | {citation_text} | {ground_truth} |")

            for model in models:
                pred = citation["model_results"][model]["predicted"]
                correct = citation["model_results"][model]["correct"]

                if pred is None:
                    cell = "?"
                elif correct:
                    cell = "✓"
                else:
                    cell = "✗"

                f.write(f" {cell} |")

            f.write(f" {correct_total} |\n")

        # Detailed explanations section
        f.write("\n## Detailed Explanations\n\n")
        f.write("### Citations with Model Disagreements\n\n")

        disagreements = [c for c in citations if not c["summary"].get("unanimous_prediction")]

        for citation in disagreements[:10]:  # Show first 10 disagreements
            idx = citation["index"]
            citation_text = citation["citation"]
            ground_truth = citation["ground_truth"]

            f.write(f"#### {idx}. {citation_text}\n\n")
            f.write(f"**Ground Truth:** {'Valid' if ground_truth else 'Invalid'}\n\n")

            for model in models:
                result = citation["model_results"][model]
                pred = result["predicted"]
                explanation = result["explanation"]
                correct = result["correct"]

                pred_text = "Valid" if pred else "Invalid" if pred is not None else "Error"
                status = "✅" if correct else "❌"

                f.write(f"**{model}:** {status} {pred_text}\n")
                f.write(f"> {explanation}\n\n")

            f.write("---\n\n")

        # Model errors section
        f.write("### Model Error Analysis\n\n")

        for model in models:
            errors = [c for c in citations if not c["model_results"][model]["correct"]]

            f.write(f"#### {model} Errors ({len(errors)} total)\n\n")

            for error in errors[:5]:  # Show first 5 errors
                idx = error["index"]
                citation_text = error["citation"][:80] + "..." if len(error["citation"]) > 80 else error["citation"]
                ground_truth = "Valid" if error["ground_truth"] else "Invalid"
                predicted = error["model_results"][model]["predicted"]
                predicted_text = "Valid" if predicted else "Invalid" if predicted is not None else "Error"
                explanation = error["model_results"][model]["explanation"]

                f.write(f"**{idx}.** {citation_text}\n")
                f.write(f"- Ground Truth: {ground_truth}\n")
                f.write(f"- Predicted: {predicted_text}\n")
                f.write(f"- Explanation: {explanation}\n\n")

            f.write("---\n\n")


if __name__ == "__main__":
    create_citation_appendix()