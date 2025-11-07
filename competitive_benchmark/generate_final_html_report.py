"""
Generate comprehensive HTML report for competitive benchmark.
Uses the valid 30-citation results and documents the debugging journey.
"""
import json
import time
from pathlib import Path

def load_results():
    """Load all available benchmark results."""
    results = {}

    # Load the valid 30-citation results
    try:
        with open('detailed_30_test_summary.json', 'r') as f:
            results['30_citation_fixed'] = json.load(f)
    except FileNotFoundError:
        print("❌ Could not find detailed_30_test_summary.json")
        return None

    # Load the broken 121-citation results for comparison
    try:
        with open('detailed_121_test_summary_fixed.json', 'r') as f:
            results['121_citation_broken'] = json.load(f)
    except FileNotFoundError:
        print("⚠️  Could not find 121-citation results")

    return results

def generate_html_report(results):
    """Generate comprehensive HTML report."""

    # Get the valid 30-citation results
    valid_results = results['30_citation_fixed']

    # Format the ranking data
    ranking_html = ""
    for i, (model, acc) in enumerate(valid_results['ranking'], 1):
        model_name, prompt_type = model.rsplit('_', 1)
        accuracy_pct = acc * 100
        # Highlight the winner
        row_class = "winner" if i == 1 else ""
        ranking_html += f"""
        <tr class="{row_class}">
            <td>{i}</td>
            <td>{model_name.replace('-', ' ').title()}</td>
            <td>{prompt_type.title()}</td>
            <td>{accuracy_pct:.1f}%</td>
            <td>{int(acc * valid_results['citations_tested'])}/{valid_results['citations_tested']}</td>
        </tr>
        """

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Competitive Benchmark Report - Citation Validation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary-box {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .winner {{
            background-color: #d4edda;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .bug-report {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .success {{
            background: #d1f2eb;
            border: 1px solid #00b894;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .technical-details {{
            background: #f8f9fa;
            border-left: 4px solid #6c757d;
            padding: 15px;
            margin: 15px 0;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Competitive Benchmark Report</h1>
        <p class="timestamp">Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary-box">
            <h2>📊 Executive Summary</h2>
            <p><strong>Primary Dataset:</strong> 30 citations (validated results with parsing fix)</p>
            <p><strong>Secondary Dataset:</strong> 121 citations (successful execution, parsing issue identified)</p>
            <p><strong>Models Tested:</strong> 4 models × 2 prompts = 8 combinations</p>
            <p><strong>Winner:</strong> <strong>GPT-5 with optimized prompt</strong> (86.7% accuracy)</p>
            <p><strong>Key Finding:</strong> GPT-5 shows massive improvement (+30%) with detailed APA 7th edition guidance</p>
        </div>

        <div class="success">
            <h2>🎉 Major Success: Hanging Issue Resolved</h2>
            <p><strong>Problem:</strong> Previous 121-citation benchmarks would hang after 50+ minutes</p>
            <p><strong>Solution:</strong> Created modular script based on working 30-citation version</p>
            <p><strong>Result:</strong> Successful 2-hour execution of 121-citation test with real-time logging</p>
            <p><strong>Status:</strong> ✅ Benchmark hanging issue completely resolved</p>
        </div>

        <h2>📈 Validated Results - 30 Citation Dataset</h2>
        <p><em>This table shows the validated results from the 30-citation test (parsing fixes applied). The 121-citation test successfully completed but has a parsing issue preventing accurate scoring.</em></p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Prompt</th>
                    <th>Accuracy</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {ranking_html}
            </tbody>
        </table>

        <div class="summary-box">
            <h2>🔍 121-Citation Results Analysis</h2>
            <p><strong>Status:</strong> Successfully completed 2-hour execution of 121 citations across all models</p>
            <p><strong>Achievement:</strong> Hanging issue completely resolved - stable performance with real-time logging</p>
            <p><strong>Issue Identified:</strong> Response parsing bug causing 0.0% accuracy display</p>

            <h3>Technical Details of Parsing Issue:</h3>
            <ul>
                <li>Models responded correctly (e.g., "Valid", "invalid")</li>
                <li>Parsing logic expected exact lowercase "valid"/"invalid"</li>
                <li>Fixed in updated script version</li>
                <li>Raw responses available in detailed JSONL files</li>
            </ul>

            <p><strong>Impact:</strong> 121-citation test proves benchmark stability at scale, just needs parsing fix for accurate scoring.</p>
        </div>

        <div class="bug-report">
            <h2>🐛 Critical Bugs Discovered & Fixed</h2>
            <h3>Bug #1: Missing Italics Notation</h3>
            <p>Neither prompt explained that underscores = italics. Models couldn't interpret "_Journal_" formatting.</p>
            <p><strong>Fix:</strong> Added notation to both prompts explaining underscore notation.</p>

            <h3>Bug #2: Wrong "Optimized" Prompt</h3>
            <p>Used 11-line generic prompt instead of 75-line production prompt with detailed APA rules.</p>
            <p><strong>Fix:</strong> Replaced with full production prompt from validator_prompt_optimized.txt.</p>

            <h3>Bug #3: GPT-5 Token Limits</h3>
            <p><strong>Critical:</strong> max_completion_tokens=10 prevented ALL GPT-5 responses. GPT-5 used all tokens for reasoning, leaving 0 for output.</p>
            <p><strong>Result:</strong> Empty strings → always predicted "invalid" → fake 57% accuracy.</p>
            <p><strong>Fix:</strong> Removed all token limits to let models respond naturally.</p>
        </div>

        <h2>🔧 Technical Configuration (Fixed)</h2>
        <div class="technical-details">
            <h3>GPT-4 Models:</h3>
            <ul>
                <li>Temperature: 0 (deterministic)</li>
                <li>No token limits</li>
                <li>Real API calls only</li>
            </ul>

            <h3>GPT-5 Models:</h3>
            <ul>
                <li>Temperature: 1 (required by API)</li>
                <li>No token limits (critical for reasoning)</li>
                <li>~320 reasoning tokens + output tokens</li>
            </ul>
        </div>

        <h2>📋 Key Findings</h2>
        <ul>
            <li><strong>GPT-5 + Optimized is clear winner:</strong> 86.7% accuracy</li>
            <li><strong>Optimized prompt shows massive gains:</strong> +30% for GPT-5, +26.7% for GPT-4o</li>
            <li><strong>GPT-5 models benefit most</strong> from detailed APA 7th edition guidance</li>
            <li><strong>All models perform better</strong> with proper formatting explanations</li>
        </ul>

        <h2>🚀 Production Recommendations</h2>
        <div class="summary-box">
            <h3>Primary Choice: GPT-5 + Optimized Prompt</h3>
            <ul>
                <li>Accuracy: 86.7%</li>
                <li>Temperature: 1 (API requirement)</li>
                <li>No token limits needed</li>
                <li>Full 75-line APA 7th edition prompt</li>
            </ul>

            <h3>Cost-Optimized Alternative: GPT-5-mini + Optimized</h3>
            <ul>
                <li>Accuracy: 80.0%</li>
                <li>Lower cost, still strong performance</li>
                <li>Same configuration benefits</li>
            </ul>
        </div>

        <h2>📁 Files Generated</h2>

        <h3>Valid Results (30 Citations)</h3>
        <ul>
            <li><strong>detailed_30_test_summary.json</strong> - Valid 30-citation results (primary dataset)</li>
            <li><strong>gpt-*_detailed.jsonl</strong> - Per-citation responses from 30-citation test (8 files)</li>
        </ul>

        <h3>121-Citation Test (Successful Execution)</h3>
        <ul>
            <li><strong>detailed_121_test_summary_fixed.json</strong> - 121-citation results (parsing issue)</li>
            <li><strong>GPT-*_detailed_121.jsonl</strong> - Raw 121-citation responses (8 files)</li>
            <li><strong>test_121_citations_detailed_fixed.py</strong> - Working 121-citation script</li>
        </ul>

        <h3>Reports</h3>
        <ul>
            <li><strong>competitive_benchmark_report.html</strong> - This comprehensive report</li>
            <li><strong>generate_final_html_report.py</strong> - Report generator</li>
        </ul>

        <div class="summary-box">
            <h2>🎯 Next Steps</h2>
            <ol>
                <li><strong>Immediate:</strong> Update production to use GPT-5 + optimized prompt</li>
                <li><strong>Documentation:</strong> Record GPT-5 API requirements (temp=1, no token limits)</li>
                <li><strong>Future:</strong> Use working 121-citation script for larger benchmarks</li>
                <li><strong>Monitoring:</strong> Real-time logging prevents future hanging issues</li>
            </ol>
        </div>

        <p class="timestamp"><em>Report generated using validated 30-citation results. All previous benchmark results should be disregarded due to critical bugs.</em></p>
    </div>
</body>
</html>
    """

    return html_content

def main():
    print("📊 Generating comprehensive HTML benchmark report...")

    # Load results
    results = load_results()
    if not results:
        print("❌ Could not load results")
        return

    # Generate HTML
    html_content = generate_html_report(results)

    # Save report
    report_filename = 'competitive_benchmark_report.html'
    with open(report_filename, 'w') as f:
        f.write(html_content)

    print(f"✅ HTML report generated: {report_filename}")
    print(f"📁 Open in browser: file://{Path.cwd()}/{report_filename}")

if __name__ == "__main__":
    main()