"""
Generate comprehensive HTML report for competitive benchmark.

Creates a standalone HTML file with embedded CSS/JS showing:
- Model performance comparison
- Interactive confusion matrices
- Filterable citation results table
- Marketing insights and statistical analysis
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def load_data() -> Dict[str, Any]:
    """Load all required data files."""

    with open('metrics_summary.json', 'r') as f:
        metrics = json.load(f)

    with open('citation_analysis.json', 'r') as f:
        citation_analysis = json.load(f)

    with open('citation_appendix.json', 'r') as f:
        appendix = json.load(f)

    return {
        'metrics': metrics,
        'citation_analysis': citation_analysis,
        'appendix': appendix
    }


def generate_html_report(data: Dict[str, Any]) -> str:
    """Generate the complete HTML report."""

    metrics = data['metrics']
    citation_analysis = data['citation_analysis']
    appendix = data['appendix']

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Competitive Benchmark Report - Citation Validation Models</title>
    <style>
        /* Reset and Base Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .header .meta {{
            margin-top: 1rem;
            font-size: 0.9rem;
            opacity: 0.8;
        }}

        /* Cards */
        .card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f0f0f0;
        }}

        .card-icon {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            font-size: 1.2rem;
        }}

        .card-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #333;
        }}

        /* Tables */
        .table-container {{
            overflow-x: auto;
            margin: 1rem 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0;
        }}

        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}

        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th:first-child {{
            border-radius: 8px 0 0 0;
        }}

        th:last-child {{
            border-radius: 0 8px 0 0;
        }}

        /* Performance Table */
        .performance-table tbody tr:hover {{
            background: #f8f9fa;
        }}

        .model-name {{
            font-weight: 600;
            color: #333;
        }}

        .metric-cell {{
            text-align: center;
            font-weight: 500;
        }}

        .accuracy {{
            color: #28a745;
            font-weight: 600;
        }}

        .f1-score {{
            color: #007bff;
            font-weight: 600;
        }}

        /* Confusion Matrices */
        .confusion-matrix {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
            margin: 1rem 0;
        }}

        .matrix-container {{
            text-align: center;
        }}

        .matrix-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #333;
        }}

        .matrix {{
            display: grid;
            grid-template-columns: 80px 80px;
            gap: 2px;
            margin: 0 auto;
            background: #ddd;
            padding: 2px;
            border-radius: 8px;
        }}

        .matrix-cell {{
            background: white;
            padding: 0.5rem;
            text-align: center;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .matrix-cell.tp {{ background: #d4edda; color: #155724; }}
        .matrix-cell.fp {{ background: #f8d7da; color: #721c24; }}
        .matrix-cell.tn {{ background: #d1ecf1; color: #0c5460; }}
        .matrix-cell.fn {{ background: #fff3cd; color: #856404; }}

        /* Marketing Section */
        .marketing-highlight {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin: 2rem 0;
            text-align: center;
        }}

        .winner-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin: 0.5rem 0;
            font-weight: 600;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}

        .stat-card {{
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}

        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        /* Filter Controls */
        .filter-section {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        .filter-controls {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        select, input {{
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }}

        .search-box {{
            min-width: 200px;
        }}

        /* Results Table */
        .results-table {{
            font-size: 0.9rem;
        }}

        .results-table td {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .correct {{ background: #d4edda; }}
        .incorrect {{ background: #f8d7da; }}
        .partial {{ background: #fff3cd; }}

        .status-cell {{
            text-align: center;
            font-weight: 600;
        }}

        .status-cell.correct {{ color: #155724; }}
        .status-cell.incorrect {{ color: #721c24; }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            .header h1 {{
                font-size: 2rem;
            }}

            .confusion-matrix {{
                grid-template-columns: 1fr;
            }}

            .filter-controls {{
                flex-direction: column;
                align-items: stretch;
            }}

            .search-box {{
                min-width: auto;
            }}

            .table-container {{
                font-size: 0.8rem;
            }}

            th, td {{
                padding: 0.5rem;
            }}
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .card {{
            animation: fadeIn 0.6s ease-out;
        }}

        .card:nth-child(2) {{ animation-delay: 0.1s; }}
        .card:nth-child(3) {{ animation-delay: 0.2s; }}
        .card:nth-child(4) {{ animation-delay: 0.3s; }}
        .card:nth-child(5) {{ animation-delay: 0.4s; }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            margin-top: 2rem;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>🏆 Competitive Benchmark Report</h1>
            <div class="subtitle">Citation Validation Models Performance Analysis</div>
            <div class="meta">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                Dataset: {metrics['dataset_info']['total_citations']} citations |
                Models: {len(metrics['dataset_info']['models_tested'])} tested
            </div>
        </header>

        <!-- Marketing Summary -->
        <div class="marketing-highlight">
            <div class="winner-badge">🥇 WINNER: {metrics['insights']['best_model']}</div>
            <h2>Outstanding Performance in Citation Validation</h2>
            <p>Leading the benchmark with superior accuracy and precision in APA 7th edition citation validation</p>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{metrics['insights']['accuracy_range'][1]:.1%}</div>
                    <div class="stat-label">Highest Accuracy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{metrics['insights']['average_agreement']:.1%}</div>
                    <div class="stat-label">Average Model Agreement</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{metrics['citation_analysis']['universal_success_count']}</div>
                    <div class="stat-label">Universal Success Citations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{metrics['model_metrics'][metrics['insights']['best_model']]['f1']:.3f}</div>
                    <div class="stat-label">Best F1 Score</div>
                </div>
            </div>
        </div>

        <!-- Performance Comparison Table -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon" style="background: #e3f2fd; color: #1976d2;">📊</div>
                <h2 class="card-title">Model Performance Comparison</h2>
            </div>

            <div class="table-container">
                <table class="performance-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Model</th>
                            <th>Accuracy</th>
                            <th>F1 Score</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>True Positives</th>
                            <th>False Positives</th>
                            <th>True Negatives</th>
                            <th>False Negatives</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add model ranking rows
    for i, model_data in enumerate(metrics['model_ranking'], 1):
        model = model_data['model']
        acc = model_data['accuracy']
        f1 = model_data['f1']
        precision = model_data['precision']
        recall = model_data['recall']
        tp = model_data['tp']
        fp = model_data['fp']
        tn = model_data['tn']
        fn = model_data['fn']

        # Determine row color based on rank
        if i == 1:
            row_class = 'style="background: #d4edda;"'
        elif i == 2:
            row_class = 'style="background: #e3f2fd;"'
        elif i == len(metrics['model_ranking']):
            row_class = 'style="background: #f8d7da;"'
        else:
            row_class = ''

        html_content += f"""
                        <tr {row_class}>
                            <td><strong>#{i}</strong></td>
                            <td class="model-name">{model}</td>
                            <td class="metric-cell accuracy">{acc:.1%}</td>
                            <td class="metric-cell f1-score">{f1:.3f}</td>
                            <td class="metric-cell">{precision:.1%}</td>
                            <td class="metric-cell">{recall:.1%}</td>
                            <td>{tp}</td>
                            <td>{fp}</td>
                            <td>{tn}</td>
                            <td>{fn}</td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Confusion Matrices -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon" style="background: #fff3e0; color: #f57c00;">🎯</div>
                <h2 class="card-title">Confusion Matrices</h2>
            </div>

            <div class="confusion-matrix">
"""

    # Add confusion matrices for each model
    for model_data in metrics['model_ranking']:
        model = model_data['model']
        tp = model_data['tp']
        fp = model_data['fp']
        tn = model_data['tn']
        fn = model_data['fn']

        # Calculate percentages
        total = tp + fp + tn + fn
        tp_pct = (tp / total * 100) if total > 0 else 0
        fp_pct = (fp / total * 100) if total > 0 else 0
        tn_pct = (tn / total * 100) if total > 0 else 0
        fn_pct = (fn / total * 100) if total > 0 else 0

        html_content += f"""
                <div class="matrix-container">
                    <div class="matrix-title">{model}</div>
                    <div class="matrix">
                        <div class="matrix-cell tp">{tp}<br><small>{tp_pct:.1f}%</small></div>
                        <div class="matrix-cell fp">{fp}<br><small>{fp_pct:.1f}%</small></div>
                        <div class="matrix-cell fn">{fn}<br><small>{fn_pct:.1f}%</small></div>
                        <div class="matrix-cell tn">{tn}<br><small>{tn_pct:.1f}%</small></div>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
                        <div style="display: inline-block; width: 12px; height: 12px; background: #d4edda; margin-right: 4px;"></div>TP
                        <div style="display: inline-block; width: 12px; height: 12px; background: #f8d7da; margin-right: 4px;"></div>FP
                        <div style="display: inline-block; width: 12px; height: 12px; background: #fff3cd; margin-right: 4px;"></div>FN
                        <div style="display: inline-block; width: 12px; height: 12px; background: #d1ecf1; margin-right: 4px;"></div>TN
                    </div>
                </div>
"""

    html_content += """
            </div>
        </div>

        <!-- Detailed Results Table -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon" style="background: #f3e5f5; color: #7b1fa2;">📋</div>
                <h2 class="card-title">Detailed Citation Results</h2>
            </div>

            <div class="filter-section">
                <div class="filter-controls">
                    <div class="filter-group">
                        <label>Search:</label>
                        <input type="text" id="searchInput" class="search-box" placeholder="Search citations...">
                    </div>
                    <div class="filter-group">
                        <label>Ground Truth:</label>
                        <select id="groundTruthFilter">
                            <option value="">All</option>
                            <option value="valid">Valid</option>
                            <option value="invalid">Invalid</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Agreement Level:</label>
                        <select id="agreementFilter">
                            <option value="">All</option>
                            <option value="4/4">4/4 Correct</option>
                            <option value="3/4">3/4 Correct</option>
                            <option value="2/4">2/4 Correct</option>
                            <option value="1/4">1/4 Correct</option>
                            <option value="0/4">0/4 Correct</option>
                        </select>
                    </div>
                    <button onclick="resetFilters()" style="padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Reset</button>
                </div>
            </div>

            <div class="table-container">
                <table class="results-table" id="resultsTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)" style="cursor: pointer;"># ↕</th>
                            <th onclick="sortTable(1)" style="cursor: pointer;">Citation ↕</th>
                            <th onclick="sortTable(2)" style="cursor: pointer;">Ground Truth ↕</th>
"""

    # Add model columns
    models = metrics['dataset_info']['models_tested']
    for model in models:
        model_short = model.replace(" ", "_").replace(".", "").replace("-mini", "_mini")
        html_content += f'<th onclick="sortTable({models.index(model) + 3})" style="cursor: pointer;">{model_short} ↕</th>'

    html_content += """
                            <th onclick="sortTable()" style="cursor: pointer;">Correct/Total ↕</th>
                        </tr>
                    </thead>
                    <tbody id="resultsTableBody">
"""

    # Add citation rows
    citations = appendix['citations']
    for i, citation in enumerate(citations, 1):
        idx = citation['index']
        citation_text = citation['citation'][:100] + "..." if len(citation['citation']) > 100 else citation['citation']
        ground_truth = "✓ Valid" if citation['ground_truth'] else "✗ Invalid"
        correct_total = citation['summary']['agreement_level']

        # Determine row class based on performance
        if citation['summary']['all_correct']:
            row_class = 'correct'
        elif citation['summary']['all_wrong']:
            row_class = 'incorrect'
        else:
            row_class = 'partial'

        html_content += f'                        <tr class="{row_class}" data-ground-truth={"valid" if citation["ground_truth"] else "invalid"} data-agreement="{correct_total}">'
        html_content += f'                            <td>{idx}</td>'
        html_content += f'                            <td title="{citation["citation"]}">{citation_text}</td>'
        html_content += f'                            <td class="status-cell {"correct" if citation["ground_truth"] else "incorrect"}">{ground_truth}</td>'

        # Add model predictions
        for model in models:
            pred = citation['model_results'][model]['predicted']
            correct = citation['model_results'][model]['correct']

            if pred is None:
                cell = '<span style="color: #666;">?</span>'
            elif correct:
                cell = '<span class="status-cell correct">✓</span>'
            else:
                cell = '<span class="status-cell incorrect">✗</span>'

            explanation = citation['model_results'][model]['explanation']
            html_content += f'                            <td title="{explanation}">{cell}</td>'

        html_content += f'                            <td><strong>{correct_total}</strong></td>'
        html_content += '                        </tr>'

    html_content += f"""
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 1rem; text-align: center; color: #666; font-size: 0.9rem;">
                Showing {len(citations)} citations •
                <span style="background: #d4edda; padding: 2px 6px; border-radius: 3px;">All Correct</span> •
                <span style="background: #fff3cd; padding: 2px 6px; border-radius: 3px;">Partial</span> •
                <span style="background: #f8d7da; padding: 2px 6px; border-radius: 3px;">All Wrong</span>
            </div>
        </div>

        <!-- Model Agreement Analysis -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon" style="background: #e8f5e8; color: #2e7d32;">🤝</div>
                <h2 class="card-title">Model Agreement Analysis</h2>
            </div>

            <div style="margin-bottom: 1rem;">
                <h3>Agreement Distribution</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Correct/Total</th>
                                <th>Count</th>
                                <th>Percentage</th>
                                <th>Visual</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    # Add agreement distribution
    for level in sorted(metrics['citation_analysis']['agreement_distribution'].keys(), key=lambda x: int(x.split('/')[0]), reverse=True):
        count = metrics['citation_analysis']['agreement_distribution'][level]
        percentage = count / metrics['dataset_info']['total_citations'] * 100
        bar_width = percentage

        html_content += f"""
                            <tr>
                                <td><strong>{level}</strong></td>
                                <td>{count}</td>
                                <td>{percentage:.1f}%</td>
                                <td>
                                    <div style="background: #e0e0e0; border-radius: 4px; overflow: hidden; height: 20px;">
                                        <div style="background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: {bar_width}%; transition: width 0.3s ease;"></div>
                                    </div>
                                </td>
                            </tr>
"""

    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>

            <div>
                <h3>Model Agreement Matrix</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Model</th>
"""

    # Add agreement matrix headers
    for model in models:
        model_short = model.split()[-1]  # Just take the last part
        html_content += f'<th>{model_short}</th>'

    html_content += """
                            </tr>
                        </thead>
                        <tbody>
"""

    # Add agreement matrix rows
    for model1 in models:
        model1_short = model1.split()[-1]
        html_content += f'                            <tr><td><strong>{model1_short}</strong></td>'

        for model2 in models:
            agreement = metrics['citation_analysis']['model_agreement_matrix'][model1][model2]
            color = '#28a745' if agreement > 0.9 else '#ffc107' if agreement > 0.8 else '#dc3545'
            html_content += f'<td style="text-align: center; color: {color}; font-weight: 600;">{agreement:.1%}</td>'

        html_content += '</tr>'

    html_content += f"""
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 0.5rem; text-align: center; color: #666; font-size: 0.9rem;">
                    Agreement percentage between models (higher is better)
                </div>
            </div>
        </div>

        <!-- Key Insights -->
        <div class="card">
            <div class="card-header">
                <div class="card-icon" style="background: #fce4ec; color: #c2185b;">💡</div>
                <h2 class="card-title">Key Insights & Recommendations</h2>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                <div>
                    <h3 style="color: #28a745; margin-bottom: 0.5rem;">🏆 Top Performer</h3>
                    <p><strong>{metrics['insights']['best_model']}</strong> leads with {metrics['model_metrics'][metrics['insights']['best_model']]['accuracy']:.1%} accuracy and {metrics['model_metrics'][metrics['insights']['best_model']]['f1']:.3f} F1 score.</p>
                </div>

                <div>
                    <h3 style="color: #007bff; margin-bottom: 0.5rem;">📊 Performance Range</h3>
                    <p>Models show {metrics['insights']['accuracy_range'][0]:.1%} to {metrics['insights']['accuracy_range'][1]:.1%} accuracy range, indicating significant performance differences.</p>
                </div>

                <div>
                    <h3 style="color: #ffc107; margin-bottom: 0.5rem;">🎯 High Agreement</h3>
                    <p>Models agree on {metrics['insights']['average_agreement']:.1%} of citations, with {metrics['citation_analysis']['universal_success_count']} citations having unanimous correct predictions.</p>
                </div>

                <div>
                    <h3 style="color: #dc3545; margin-bottom: 0.5rem;">⚠️ Improvement Areas</h3>
                    <p>Model disagreement on {metrics['citation_analysis']['universal_failure_count'] + sum(1 for c in citations if not c['summary'].get('unanimous_prediction'))} citations suggests opportunities for ensemble approaches.</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <p>Competitive Benchmark Report - Citation Validation Models</p>
            <p>Generated with mock data for demonstration purposes</p>
            <p>© 2025 - All metrics and analyses are based on simulated results</p>
        </footer>
    </div>

    <script>
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', filterTable);
        document.getElementById('groundTruthFilter').addEventListener('change', filterTable);
        document.getElementById('agreementFilter').addEventListener('change', filterTable);

        function filterTable() {{
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const groundTruthFilter = document.getElementById('groundTruthFilter').value;
            const agreementFilter = document.getElementById('agreementFilter').value;
            const rows = document.getElementById('resultsTableBody').getElementsByTagName('tr');

            for (let row of rows) {{
                const citation = row.getElementsByTagName('td')[1].textContent.toLowerCase();
                const groundTruth = row.getAttribute('data-ground-truth');
                const agreement = row.getAttribute('data-agreement');

                const matchesSearch = citation.includes(searchInput);
                const matchesGroundTruth = !groundTruthFilter || groundTruth === groundTruthFilter;
                const matchesAgreement = !agreementFilter || agreement === agreementFilter;

                if (matchesSearch && matchesGroundTruth && matchesAgreement) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }}
        }}

        function resetFilters() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('groundTruthFilter').value = '';
            document.getElementById('agreementFilter').value = '';
            filterTable();
        }}

        // Sort table functionality
        let sortDirection = {{}};

        function sortTable(columnIndex) {{
            const table = document.getElementById('resultsTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));

            // Toggle sort direction
            sortDirection[columnIndex] = !sortDirection[columnIndex];

            rows.sort((a, b) => {{
                let aValue, bValue;

                if (columnIndex === undefined) {{
                    // Sort by Correct/Total column
                    aValue = a.getAttribute('data-agreement');
                    bValue = b.getAttribute('data-agreement');
                }} else {{
                    aValue = a.getElementsByTagName('td')[columnIndex].textContent;
                    bValue = b.getElementsByTagName('td')[columnIndex].textContent;
                }}

                // Handle numeric sorting
                if (!isNaN(aValue) && !isNaN(bValue)) {{
                    aValue = parseFloat(aValue);
                    bValue = parseFloat(bValue);
                }}

                if (sortDirection[columnIndex]) {{
                    return aValue > bValue ? 1 : -1;
                }} else {{
                    return aValue < bValue ? 1 : -1;
                }}
            }});

            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {{
            // Add smooth scrolling
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth' }});
                    }}
                }});
            }});

            // Add animation to cards on scroll
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }});

            document.querySelectorAll('.card').forEach(card => {{
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            }});
        }});
    </script>
</body>
</html>"""

    return html_content


def main():
    print("="*80)
    print("GENERATING STANDALONE HTML REPORT")
    print("="*80)

    # Load data
    print("📁 Loading benchmark data...")
    data = load_data()
    print(f"✅ Loaded data for {len(data['metrics']['dataset_info']['models_tested'])} models")

    # Generate HTML
    print("🎨 Generating HTML report...")
    html_content = generate_html_report(data)

    # Save report
    output_file = 'competitive_benchmark_report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML report generated: {output_file}")

    # Show file size
    file_size = os.path.getsize(output_file) / 1024  # KB
    print(f"📊 File size: {file_size:.1f} KB")

    print(f"\n🎯 Report features:")
    print(f"   • Interactive performance comparison table")
    print(f"   • Visual confusion matrices for all models")
    print(f"   • Filterable/sortable citation results table")
    print(f"   • Model agreement analysis and matrix")
    print(f"   • Marketing insights with key statistics")
    print(f"   • Responsive design for all devices")
    print(f"   • Embedded CSS/JS (works offline)")

    print(f"\n📈 Key metrics included:")
    metrics = data['metrics']
    print(f"   • Best performer: {metrics['insights']['best_model']}")
    print(f"   • Accuracy range: {metrics['insights']['accuracy_range'][0]:.1%} - {metrics['insights']['accuracy_range'][1]:.1%}")
    print(f"   • Average agreement: {metrics['insights']['average_agreement']:.1%}")
    print(f"   • Total citations: {metrics['dataset_info']['total_citations']}")

    print(f"\n✨ Report ready for presentation!")
    print(f"📁 Open {output_file} in your browser to view the complete analysis")


if __name__ == "__main__":
    main()