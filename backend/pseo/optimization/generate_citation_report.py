#!/usr/bin/env python3
"""
Generate comprehensive HTML report showing all citations organized by train/val/test sets.
"""
import json
import random
from pathlib import Path
from html import escape


def load_citations(books_journals_only=False, journals_only=False):
    """Load valid and invalid citations."""
    if journals_only:
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_journals_only.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_journals_only.jsonl')
    elif books_journals_only:
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_books_journals.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_books_journals.jsonl')
    else:
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')

    with open(valid_file) as f:
        valid_citations = [json.loads(line) for line in f]

    with open(invalid_file) as f:
        invalid_citations = [json.loads(line) for line in f]

    return valid_citations, invalid_citations


def create_examples(valid_citations, invalid_citations):
    """Create train/val/test splits matching the optimization run."""
    all_examples = []

    # Add valid citations
    for cit in valid_citations:
        all_examples.append({
            'citation': cit['citation_text'],
            'source_type': cit.get('source_type', 'unknown'),
            'is_valid': True,
            'errors': [],
            'metadata': cit.get('metadata', {})
        })

    # Add invalid citations
    for cit in invalid_citations:
        all_examples.append({
            'citation': cit['citation_text'],
            'source_type': cit.get('source_type', 'unknown'),
            'is_valid': False,
            'errors': cit.get('errors', []),
            'metadata': cit.get('metadata', {})
        })

    # Shuffle with same seed as optimization
    random.seed(42)
    random.shuffle(all_examples)

    # Split 60/25/15 (matches medium-mode optimization)
    train_size = int(len(all_examples) * 0.6)
    val_size = int(len(all_examples) * 0.25)

    train = all_examples[:train_size]
    val = all_examples[train_size:train_size+val_size]
    test = all_examples[train_size+val_size:]

    return train, val, test


def format_errors(errors):
    """Format error list as HTML."""
    if not errors:
        return '<span class="valid-badge">✓ Valid Citation</span>'

    html = '<div class="errors">'
    for error in errors:
        component = escape(error.get('component', 'unknown'))
        problem = escape(error.get('problem', 'unknown'))
        correction = escape(error.get('correction', 'N/A'))

        html += f'''
        <div class="error-item">
            <strong>Component:</strong> {component}<br>
            <strong>Problem:</strong> {problem}<br>
            <strong>Correction:</strong> {correction}
        </div>
        '''
    html += '</div>'
    return html


def load_test_predictions():
    """Load test predictions from JSON file."""
    predictions_file = Path('backend/pseo/optimization/test_predictions.json')
    if predictions_file.exists():
        with open(predictions_file) as f:
            predictions = json.load(f)
        # Convert to list - we'll match by index instead of citation text
        # (citation text matching is fragile due to whitespace/formatting)
        return predictions
    return []


def generate_html(train, val, test, test_predictions):
    """Generate HTML report."""

    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Citation Dataset Report - MIPROv2 Optimization</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }

        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .stat-box {
            background: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #3498db;
        }

        .stat-box h3 {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 5px;
        }

        .stat-box .number {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }

        .stat-box .detail {
            font-size: 12px;
            color: #95a5a6;
            margin-top: 5px;
        }

        .dataset-section {
            margin: 40px 0;
        }

        .dataset-section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding: 10px;
            background: #ecf0f1;
            border-left: 5px solid #3498db;
        }

        .train-section h2 { border-left-color: #3498db; }
        .val-section h2 { border-left-color: #f39c12; }
        .test-section h2 { border-left-color: #e74c3c; }

        .citation-card {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .citation-card.invalid {
            border-left: 5px solid #e74c3c;
        }

        .citation-card.valid {
            border-left: 5px solid #2ecc71;
        }

        .citation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ecf0f1;
        }

        .citation-index {
            font-weight: bold;
            color: #7f8c8d;
            font-size: 14px;
        }

        .source-type {
            background: #3498db;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
        }

        .source-link {
            color: #3498db;
            text-decoration: none;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 5px;
            margin-bottom: 10px;
        }

        .source-link:hover {
            text-decoration: underline;
        }

        .citation-text {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: "Courier New", monospace;
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 15px;
            border: 1px solid #e9ecef;
        }

        .valid-badge {
            background: #2ecc71;
            color: white;
            padding: 8px 16px;
            border-radius: 5px;
            font-weight: bold;
            display: inline-block;
        }

        .errors {
            margin-top: 15px;
        }

        .error-item {
            background: #fff5f5;
            border: 1px solid #feb2b2;
            border-radius: 5px;
            padding: 12px;
            margin-bottom: 10px;
        }

        .error-item strong {
            color: #c53030;
        }

        .test-result {
            background: #f0f9ff;
            border: 2px solid #3b82f6;
            border-radius: 5px;
            padding: 15px;
            margin-top: 15px;
        }

        .test-result h4 {
            color: #1e40af;
            margin-bottom: 10px;
        }

        .prediction {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }

        .prediction-item {
            padding: 8px;
            background: white;
            border-radius: 3px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #ecf0f1;
        }

        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 16px;
            font-weight: 500;
            color: #7f8c8d;
            transition: all 0.3s;
        }

        .tab:hover {
            color: #3498db;
        }

        .tab.active {
            color: #3498db;
            border-bottom: 3px solid #3498db;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .filter-bar {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .filter-bar label {
            font-weight: 500;
        }

        .filter-bar select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Citation Dataset Report - MIPROv2 Optimization</h1>

        <div class="summary">
            <h3>Dataset Overview</h3>
            <div class="summary-stats">
                <div class="stat-box">
                    <h3>Total Citations</h3>
                    <div class="number">''' + str(len(train) + len(val) + len(test)) + '''</div>
                    <div class="detail">58 valid + 92 invalid</div>
                </div>
                <div class="stat-box">
                    <h3>Training Set</h3>
                    <div class="number">''' + str(len(train)) + '''</div>
                    <div class="detail">''' + str(sum(1 for c in train if c['is_valid'])) + ''' valid, ''' + str(sum(1 for c in train if not c['is_valid'])) + ''' invalid</div>
                </div>
                <div class="stat-box">
                    <h3>Validation Set</h3>
                    <div class="number">''' + str(len(val)) + '''</div>
                    <div class="detail">''' + str(sum(1 for c in val if c['is_valid'])) + ''' valid, ''' + str(sum(1 for c in val if not c['is_valid'])) + ''' invalid</div>
                </div>
                <div class="stat-box">
                    <h3>Test Set</h3>
                    <div class="number">''' + str(len(test)) + '''</div>
                    <div class="detail">''' + str(sum(1 for c in test if c['is_valid'])) + ''' valid, ''' + str(sum(1 for c in test if not c['is_valid'])) + ''' invalid</div>
                </div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('train')">Training Set (''' + str(len(train)) + ''')</button>
            <button class="tab" onclick="showTab('val')">Validation Set (''' + str(len(val)) + ''')</button>
            <button class="tab" onclick="showTab('test')">Test Set (''' + str(len(test)) + ''')</button>
        </div>
'''

    # Training set
    html += '<div id="train" class="tab-content active dataset-section train-section">'
    html += '<h2>🎓 Training Set</h2>'
    for i, citation in enumerate(train, 1):
        html += generate_citation_card(i, citation, False)
    html += '</div>'

    # Validation set
    html += '<div id="val" class="tab-content dataset-section val-section">'
    html += '<h2>🔍 Validation Set</h2>'
    for i, citation in enumerate(val, 1):
        html += generate_citation_card(i, citation, False)
    html += '</div>'

    # Test set
    html += '<div id="test" class="tab-content dataset-section test-section">'
    html += '<h2>🧪 Test Set (with Optimization Results)</h2>'
    for i, citation in enumerate(test, 1):
        # Match prediction by test index (i-1 since enumerate starts at 1)
        pred_for_citation = test_predictions[i-1] if test_predictions and i-1 < len(test_predictions) else None
        html += generate_citation_card(i, citation, True, pred_for_citation)
    html += '</div>'

    html += '''
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Remove active class from all tab buttons
            document.querySelectorAll('.tab').forEach(button => {
                button.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName).classList.add('active');

            // Add active class to clicked button
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
'''

    return html


def generate_citation_card(index, citation, include_test_result, prediction=None):
    """Generate HTML for a single citation card."""
    valid_class = 'valid' if citation['is_valid'] else 'invalid'

    # Extract source link if available
    metadata = citation.get('metadata', {})
    source_url = metadata.get('url', '')
    source_section = metadata.get('section', '')
    source_name = metadata.get('source', 'Purdue OWL')
    source_link_html = ''
    if source_url:
        display_text = f"{source_name}"
        if source_section:
            display_text += f" - {source_section}"
        source_link_html = f'<a href="{escape(source_url)}" target="_blank" class="source-link">📖 View source: {escape(display_text)}</a>'

    html = f'''
    <div class="citation-card {valid_class}">
        <div class="citation-header">
            <span class="citation-index">Citation #{index}</span>
            <span class="source-type">{escape(citation['source_type'])}</span>
        </div>

        {source_link_html}

        <div class="citation-text">
            {escape(citation['citation'])}
        </div>

        {format_errors(citation['errors'])}

        {generate_test_result_section(citation, prediction) if include_test_result else ''}
    </div>
    '''

    return html


def generate_test_result_section(citation, prediction):
    """Generate test result section with prediction details."""
    if not prediction:
        return '''
        <div class="test-result">
            <h4>⚡ Optimization Test Result</h4>
            <p style="color: #6b7280; font-size: 14px;">
                <em>Note: Test predictions not yet generated. Run get_test_predictions.py first.</em>
            </p>
        </div>
        '''

    pred_data = prediction.get('prediction', {})
    ground_truth = prediction.get('ground_truth', {})

    # Check if there was an error
    if 'error' in pred_data:
        return f'''
        <div class="test-result">
            <h4>⚡ Optimization Test Result</h4>
            <p style="color: #dc2626; font-size: 14px;">
                <strong>Error:</strong> {escape(pred_data['error'])}
            </p>
        </div>
        '''

    # Check if prediction matches ground truth
    is_correct = pred_data.get('is_valid') == ground_truth.get('is_valid')
    status_color = '#16a34a' if is_correct else '#dc2626'
    status_icon = '✓' if is_correct else '✗'
    status_text = 'CORRECT' if is_correct else 'INCORRECT'

    html = f'''
    <div class="test-result" style="border-color: {status_color};">
        <h4 style="color: {status_color};">⚡ Test Result: {status_icon} {status_text}</h4>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
            <div style="background: #f9fafb; padding: 10px; border-radius: 5px;">
                <strong style="color: #374151;">Ground Truth:</strong><br>
                <span style="color: {'#16a34a' if ground_truth.get('is_valid') else '#dc2626'};">
                    {'✓ Valid' if ground_truth.get('is_valid') else '✗ Invalid'}
                </span>
                {format_prediction_errors(ground_truth.get('errors', []))}
            </div>

            <div style="background: #f9fafb; padding: 10px; border-radius: 5px;">
                <strong style="color: #374151;">Prediction:</strong><br>
                <span style="color: {'#16a34a' if pred_data.get('is_valid') else '#dc2626'};">
                    {'✓ Valid' if pred_data.get('is_valid') else '✗ Invalid'}
                </span>
                {format_prediction_errors(pred_data.get('errors', []))}
            </div>
        </div>
    </div>
    '''

    return html


def format_prediction_errors(errors):
    """Format error list for prediction display."""
    if not errors:
        return '<div style="margin-top: 8px; color: #6b7280; font-size: 13px;"><em>No errors detected</em></div>'

    html = '<div style="margin-top: 8px; font-size: 13px;">'
    # Show ALL errors (removed the [:3] limit)
    for error in errors:
        if isinstance(error, str):
            html += f'<div style="color: #dc2626;">• {escape(error)}</div>'
        elif isinstance(error, dict):
            component = error.get('component', 'unknown')
            problem = error.get('problem', error.get('issue', 'unknown'))
            html += f'<div style="color: #dc2626;">• {escape(component)}: {escape(problem)}</div>'
    html += '</div>'
    return html


def main():
    import sys

    # Check for command-line arguments
    journals_only = '--journals-only' in sys.argv
    books_journals_only = '--books-journals-only' in sys.argv

    print("Loading citations...")
    if journals_only:
        print("Using JOURNALS ONLY dataset")
    elif books_journals_only:
        print("Using BOOKS AND JOURNALS ONLY dataset")

    valid_citations, invalid_citations = load_citations(books_journals_only, journals_only)

    print(f"Loaded {len(valid_citations)} valid citations")
    print(f"Loaded {len(invalid_citations)} invalid citations")

    print("Creating train/val/test splits...")
    train, val, test = create_examples(valid_citations, invalid_citations)

    print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    print("Loading test predictions...")
    test_predictions = load_test_predictions()
    if test_predictions:
        print(f"Loaded {len(test_predictions)} test predictions")
    else:
        print("No test predictions found - test results will show placeholder")

    print("Generating HTML report...")
    html = generate_html(train, val, test, test_predictions)

    # Use different filename based on dataset
    if journals_only:
        output_file = Path('backend/pseo/optimization/citation_dataset_report_journals_only.html')
    elif books_journals_only:
        output_file = Path('backend/pseo/optimization/citation_dataset_report_books_journals.html')
    else:
        output_file = Path('backend/pseo/optimization/citation_dataset_report.html')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Report generated: {output_file}")
    print(f"\nOpen in browser: file://{output_file.absolute()}")


if __name__ == '__main__':
    main()
