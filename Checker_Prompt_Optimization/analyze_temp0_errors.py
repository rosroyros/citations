import json

def analyze_consistent_errors():
    with open("Checker_Prompt_Optimization/gemini_consistency_results_part2.json", "r") as f:
        data = json.load(f)
    
    consistent_errors = []
    
    for item in data["citation_analysis"]:
        # We only care if it was consistent (meaning it made the SAME mistake every time)
        if item["consistent"]:
            # Check if the verdict matches the ground truth
            # We can check any run since they are consistent
            verdict = item["runs"]["run_1"]
            ground_truth = item["ground_truth"]
            
            if verdict != ground_truth:
                consistent_errors.append({
                    "citation_number": item["citation_number"],
                    "ground_truth": ground_truth,
                    "model_verdict": verdict
                })
    
    print(f"Found {len(consistent_errors)} consistent errors.")
    
    # Sort by citation number
    consistent_errors.sort(key=lambda x: x["citation_number"])
    
    print("\n--- CONSISTENT ERRORS (Systematic Failure Cases) ---")
    for err in consistent_errors:
        type_str = "FALSE POSITIVE (Missed Error)" if err["model_verdict"] else "FALSE NEGATIVE (Hallucinated Error)"
        print(f"#{err['citation_number']}: {type_str} | Truth: {err['ground_truth']} | Model: {err['model_verdict']}")

if __name__ == "__main__":
    analyze_consistent_errors()
