#!/usr/bin/env python3
import json
import re

def parse_response_with_batch_mapping(response_text: str, start_idx: int, batch_size: int):
    """Parse response and map batch-local numbering to global citation numbers"""
    results = []
    citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
    matches = re.finditer(citation_pattern, response_text, re.DOTALL)

    batch_local_numbers = []

    for match in matches:
        batch_local_num = int(match.group(1))
        block_content = match.group(2)
        batch_local_numbers.append(batch_local_num)

        # Map batch-local number to global citation number
        global_citation_num = start_idx + (batch_local_num - 1)

        is_valid = False
        if '✓ No APA 7 formatting errors detected' in block_content or 'No APA 7 formatting errors' in block_content:
            is_valid = True

        results.append({
            "citation_number": global_citation_num,
            "batch_local_number": batch_local_num,
            "is_valid": is_valid,
            "raw_block": block_content[:200] + "..." if len(block_content) > 200 else block_content
        })

    return results, batch_local_numbers

def fix_and_analyze_results():
    """Fix the parsing and calculate accuracy"""

    print("🔧 FIXING SYSTEM INSTRUCTIONS RESULTS")
    print("=" * 50)

    # Load the results
    with open('Checker_Prompt_Optimization/gemini_system_instructions_121_results.json', 'r') as f:
        data = json.load(f)

    # Load ground truth
    ground_truth = {}
    with open('Checker_Prompt_Optimization/test_set_121_corrected.jsonl', 'r') as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                try:
                    item = json.loads(line)
                    ground_truth[i] = item['ground_truth']
                except:
                    continue

    print(f"📊 Loaded ground truth for {len(ground_truth)} citations")
    print(f"📄 Response length: {len(data['results']['response_text']):,} characters")
    print()

    # Parse the combined response text by reconstructing batch segments
    response_text = data['results']['response_text']

    # Alternative approach: parse the entire response and map batch numbers
    all_results = []
    batch_size = 5

    # Split response into batch chunks (this is approximate, but should work)
    # We'll use the fact that each batch typically processes 5 citations
    citation_blocks = response_text.split('═══════════════════════════════════════════════════════════════════════════')

    global_citation_num = 1

    for block in citation_blocks:
        if 'CITATION #' in block:
            # Extract all CITATION # instances in this block
            local_matches = re.findall(r'CITATION #(\d+)', block)

            # For each local citation, map to global number
            for local_num_str in local_matches:
                local_num = int(local_num_str)
                global_num = global_citation_num

                # Extract the specific citation block for this local citation
                local_pattern = rf'CITATION #{local_num}\s*═+(.+?)(?=CITATION #\d+|$)'
                local_match = re.search(local_pattern, block, re.DOTALL)

                if local_match:
                    block_content = local_match.group(1)

                    is_valid = False
                    if '✓ No APA 7 formatting errors detected' in block_content or 'No APA 7 formatting errors' in block_content:
                        is_valid = True

                    all_results.append({
                        "citation_number": global_num,
                        "batch_local_number": local_num,
                        "is_valid": is_valid,
                        "raw_block": block_content[:150] + "..." if len(block_content) > 150 else block_content
                    })

                global_citation_num += 1

    print(f"📋 Parsed {len(all_results)} citations from response")
    print()

    # Calculate accuracy
    correct_count = 0
    total_count = 0
    details = []

    for result in all_results:
        citation_num = result['citation_number']
        if citation_num in ground_truth:
            total_count += 1
            is_correct = result['is_valid'] == ground_truth[citation_num]
            if is_correct:
                correct_count += 1

            details.append({
                "citation_number": citation_num,
                "predicted": result['is_valid'],
                "ground_truth": ground_truth[citation_num],
                "correct": is_correct
            })

    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    coverage = (total_count / 121 * 100)

    print("📊 ACCURACY RESULTS")
    print("=" * 30)
    print(f"Total citations processed: {total_count}/121 ({coverage:.1f}% coverage)")
    print(f"Correct predictions: {correct_count}/{total_count}")
    print(f"Accuracy: {accuracy:.2f}%")
    print()

    # Show some examples
    print("🔍 SAMPLE RESULTS:")
    print("-" * 20)
    for i, detail in enumerate(details[:10]):
        status = "✅" if detail['correct'] else "❌"
        print(f"{status} Citation #{detail['citation_number']}: {detail['predicted']} (truth: {detail['ground_truth']})")

    # Thinking statistics
    thinking_stats = data['results']['thinking_stats']
    print()
    print("🧠 THINKING STATISTICS:")
    print("-" * 20)
    print(f"Total thinking tokens: {thinking_stats['total_thinking_tokens']:,}")
    print(f"Avg thinking per batch: {thinking_stats['avg_thinking_per_batch']:.0f}")
    print(f"Thinking overhead: {thinking_stats['thinking_overhead_percentage']:.1f}%")
    print(f"Batches with thinking: {thinking_stats['batches_with_thinking']}/25")

    # Performance
    print()
    print("⚡ PERFORMANCE:")
    print("-" * 12)
    print(f"Total time: {data['results']['total_time_minutes']:.1f} minutes")
    print(f"Avg time per citation: {data['results']['avg_time_per_citation']:.2f}s")
    print(f"Citations per hour: {data['results']['citations_per_hour']:.1f}")

    # Save fixed results
    fixed_results = {
        "metadata": data["metadata"],
        "results": {
            "parsed": all_results,
            "accuracy": accuracy,
            "coverage": coverage,
            "correct_count": correct_count,
            "total_processed": total_count,
            "details": details,
            "thinking_stats": thinking_stats,
            "performance": {
                "total_time_minutes": data['results']['total_time_minutes'],
                "avg_time_per_citation": data['results']['avg_time_per_citation'],
                "citations_per_hour": data['results']['citations_per_hour']
            }
        }
    }

    with open('Checker_Prompt_Optimization/gemini_system_instructions_121_fixed.json', 'w') as f:
        json.dump(fixed_results, f, indent=2)

    print()
    print(f"💾 Fixed results saved to gemini_system_instructions_121_fixed.json")

if __name__ == "__main__":
    fix_and_analyze_results()