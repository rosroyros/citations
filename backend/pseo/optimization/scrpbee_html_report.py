#!/usr/bin/env python3
"""
Create comprehensive HTML report for scrpbee dataset
"""

import json
from datetime import datetime

def create_scrpbee_html_report():
    """Generate HTML report for scrpbee dataset"""

    # Load valid and invalid citations
    valid_citations = []
    invalid_citations = []

    with open('backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_clean.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                valid_citations.append(json.loads(line))

    with open('backend/pseo/optimization/datasets/scrpbee/scrpbee_invalid_citations.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                invalid_citations.append(json.loads(line))

    all_citations = valid_citations + invalid_citations

    print(f"Creating HTML report with {len(all_citations)} total citations...")
    print(f"  Valid: {len(valid_citations)}")
    print(f"  Invalid: {len(invalid_citations)}")

    # Create HTML content
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrpBee APA Citation Dataset Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #e67e22;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #e67e22;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .dataset-summary {{
            background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin: 30px 0;
        }}
        .dataset-summary h2 {{
            color: white;
            border-left: none;
            padding-left: 0;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .valid-card {{
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        }}
        .invalid-card {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }}
        .filter-buttons {{
            margin: 30px 0;
            text-align: center;
        }}
        .filter-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #2980b9;
            transform: translateY(-2px);
        }}
        .filter-btn.valid-filter {{
            background: #27ae60;
        }}
        .filter-btn.valid-filter:hover, .filter-btn.valid-filter.active {{
            background: #229954;
        }}
        .filter-btn.invalid-filter {{
            background: #e74c3c;
        }}
        .filter-btn.invalid-filter:hover, .filter-btn.invalid-filter.active {{
            background: #c0392b;
        }}
        .citation {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .citation:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .citation.valid {{
            border-left: 4px solid #27ae60;
        }}
        .citation.invalid {{
            border-left: 4px solid #e74c3c;
        }}
        .citation-text {{
            font-size: 1.1em;
            line-height: 1.8;
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }}
        .citation-meta {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 10px;
        }}
        .meta-item {{
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 2px;
        }}
        .source-type {{
            font-weight: bold;
            color: #495057;
        }}
        .validity-badge {{
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            color: white;
        }}
        .valid-badge {{
            background: #27ae60;
        }}
        .invalid-badge {{
            background: #e74c3c;
        }}
        .error-info {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
        }}
        .error-info strong {{
            color: #721c24;
        }}
        .search-box {{
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
            box-sizing: border-box;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .stats-table th, .stats-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .stats-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .stats-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        .file-info {{
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .error-breakdown {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .error-type {{
            display: inline-block;
            background: #f39c12;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 ScrpBee APA Citation Dataset Report</h1>

        <div class="dataset-summary">
            <h2>📊 Clean Dataset from ScrapingBee</h2>
            <p>Complete citation validation dataset created from Purdue OWL using ScrapingBee scraping technology</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="file-info">
            <strong>📁 Dataset Files:</strong><br>
            • Valid Citations: backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_clean.jsonl<br>
            • Invalid Citations: backend/pseo/optimization/datasets/scrpbee/scrpbee_invalid_citations.jsonl
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>{len(all_citations)}</h3>
                <p>Total Citations</p>
            </div>
            <div class="stat-card valid-card">
                <h3>{len(valid_citations)}</h3>
                <p>Valid Citations</p>
            </div>
            <div class="stat-card invalid-card">
                <h3>{len(invalid_citations)}</h3>
                <p>Invalid Citations</p>
            </div>
            <div class="stat-card">
                <h3>{len(set(c['source_type'] for c in all_citations))}</h3>
                <p>Source Types</p>
            </div>
        </div>

        <div class="error-breakdown">
            <h3>🔧 Error Types Generated:</h3>
            {generate_error_type_breakdown(invalid_citations)}
        </div>

        <h2>🔍 Search & Filter</h2>
        <input type="text" class="search-box" id="searchBox" placeholder="Search citations by title, author, error type, or keyword...">

        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterCitations('all')">All Citations</button>
            <button class="filter-btn valid-filter" onclick="filterCitations('valid')">Valid Only</button>
            <button class="filter-btn invalid-filter" onclick="filterCitations('invalid')">Invalid Only</button>
            <button class="filter-btn" onclick="filterCitations('journal article')">Journal Articles</button>
            <button class="filter-btn" onclick="filterCitations('book')">Books</button>
            <button class="filter-btn" onclick="filterCitations('webpage')">Webpages</button>
            <button class="filter-btn" onclick="filterCitations('other')">Other Sources</button>
        </div>

        <h2>📈 Statistics</h2>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>Source Type</th>
                    <th>Valid</th>
                    <th>Invalid</th>
                    <th>Total</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody id="statsTableBody">
                <!-- Stats will be populated by JavaScript -->
            </tbody>
        </table>

        <h2>📚 Citations</h2>
        <div id="citationsContainer">
            <p style="text-align: center; color: #6c757d;">Loading citation data...</p>
        </div>
    </div>

    <script>
        // Citation data embedded directly
        const allCitations = {json.dumps(all_citations, ensure_ascii=False)};

        let filteredCitations = [...allCitations];

        function isValidCitation(citation) {{
            return citation.is_valid !== false;
        }}

        function displayCitations() {{
            const container = document.getElementById('citationsContainer');
            container.innerHTML = '';

            if (filteredCitations.length === 0) {{
                container.innerHTML = '<p style="text-align: center; color: #6c757d;">No citations found matching your criteria.</p>';
                return;
            }}

            // Group by validity and then by source type
            const grouped = {{
                valid: {{}},
                invalid: {{}}
            }};

            filteredCitations.forEach(citation => {{
                const isValid = isValidCitation(citation);
                const category = isValid ? 'valid' : 'invalid';
                const type = citation.source_type;

                if (!grouped[category][type]) {{
                    grouped[category][type] = [];
                }}
                grouped[category][type].push(citation);
            }});

            // Display valid citations first
            if (Object.keys(grouped.valid).length > 0) {{
                const validSection = document.createElement('div');
                validSection.innerHTML = '<h2 style="color: #27ae60; border-left-color: #27ae60;">✅ Valid Citations</h2>';

                Object.keys(grouped.valid).sort().forEach(type => {{
                    const typeDiv = document.createElement('div');
                    typeDiv.innerHTML = `
                        <h3>📖 ${{type.charAt(0).toUpperCase() + type.slice(1)}} (${{grouped.valid[type].length}})</h3>
                        <div class="citations-group" data-type="${{type}}" data-validity="valid">
                            ${{grouped.valid[type].map(citation => createCitationHTML(citation, true)).join('')}}
                        </div>
                    `;
                    validSection.appendChild(typeDiv);
                }});

                container.appendChild(validSection);
            }}

            // Display invalid citations
            if (Object.keys(grouped.invalid).length > 0) {{
                const invalidSection = document.createElement('div');
                invalidSection.innerHTML = '<h2 style="color: #e74c3c; border-left-color: #e74c3c;">❌ Invalid Citations (with Errors)</h2>';

                Object.keys(grouped.invalid).sort().forEach(type => {{
                    const typeDiv = document.createElement('div');
                    typeDiv.innerHTML = `
                        <h3>📖 ${{type.charAt(0).toUpperCase() + type.slice(1)}} (${{grouped.invalid[type].length}})</h3>
                        <div class="citations-group" data-type="${{type}}" data-validity="invalid">
                            ${{grouped.invalid[type].map(citation => createCitationHTML(citation, false)).join('')}}
                        </div>
                    `;
                    invalidSection.appendChild(typeDiv);
                }});

                container.appendChild(invalidSection);
            }}
        }}

        function createCitationHTML(citation, isValid) {{
            const validityClass = isValid ? 'valid' : 'invalid';
            const validityBadge = isValid ?
                '<span class="validity-badge valid-badge">✅ Valid</span>' :
                '<span class="validity-badge invalid-badge">❌ Invalid</span>';

            let errorInfo = '';
            if (!isValid && citation.errors && citation.errors.length > 0) {{
                const error = citation.errors[0];
                const errorTypes = citation.metadata.error_types || [];
                const errorTypeTags = errorTypes.map(type =>
                    `<span class="error-type">${{type}}</span>`
                ).join(' ');

                errorInfo = `
                    <div class="error-info">
                        <strong>🔧 Error:</strong> ${{error.problem}}<br>
                        <strong>💡 Correction:</strong> ${{error.correction}}<br>
                        <strong>🏷️ Type:</strong> ${{error.component}} | ${{errorTypeTags}}
                    </div>
                `;
            }}

            return `
                <div class="citation ${{validityClass}}" data-type="${{citation.source_type}}" data-validity="${{isValid ? 'valid' : 'invalid'}}">
                    <div class="citation-text">
                        ${{highlightSearchTerms(citation.citation_text)}}
                    </div>
                    <div class="citation-meta">
                        <span class="meta-item"><strong>ID:</strong> ${{citation.citation_id}}</span>
                        <span class="meta-item source-type">${{citation.source_type}}</span>
                        <span class="meta-item">${{citation.metadata.source}}</span>
                        ${{validityBadge}}
                    </div>
                    ${{errorInfo}}
                </div>
            `;
        }}

        function highlightSearchTerms(text) {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            if (!searchTerm) return text;

            const regex = new RegExp(`(${{searchTerm}})`, 'gi');
            return text.replace(regex, '<span class="highlight">$1</span>');
        }}

        function filterCitations(filter) {{
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Filter citations
            if (filter === 'all') {{
                filteredCitations = [...allCitations];
            }} else if (filter === 'valid') {{
                filteredCitations = allCitations.filter(c => isValidCitation(c));
            }} else if (filter === 'invalid') {{
                filteredCitations = allCitations.filter(c => !isValidCitation(c));
            }} else {{
                filteredCitations = allCitations.filter(c => c.source_type === filter);
            }}

            // Apply search filter if exists
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            if (searchTerm) {{
                filteredCitations = filteredCitations.filter(citation => {{
                    const searchText = (citation.citation_text + ' ' +
                                     citation.citation_id + ' ' +
                                     citation.source_type + ' ' +
                                     (citation.errors ? citation.errors.map(e => e.problem).join(' ') : '')).toLowerCase();
                    return searchText.includes(searchTerm);
                }});
            }}

            displayCitations();
        }}

        function updateStatistics() {{
            const stats = {{}};

            allCitations.forEach(citation => {{
                const type = citation.source_type;
                if (!stats[type]) {{
                    stats[type] = {{ valid: 0, invalid: 0 }};
                }}

                if (isValidCitation(citation)) {{
                    stats[type].valid++;
                }} else {{
                    stats[type].invalid++;
                }}
            }});

            const tbody = document.getElementById('statsTableBody');
            tbody.innerHTML = '';

            Object.keys(stats).sort().forEach(type => {{
                const valid = stats[type].valid;
                const invalid = stats[type].invalid;
                const total = valid + invalid;
                const percentage = ((total / allCitations.length) * 100).toFixed(1);

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${{type.charAt(0).toUpperCase() + type.slice(1)}}</strong></td>
                        <td style="color: #27ae60; font-weight: bold;">${{valid}}</td>
                        <td style="color: #e74c3c; font-weight: bold;">${{invalid}}</td>
                        <td>${{total}}</td>
                        <td>${{percentage}}%</td>
                    </tr>
                `;
            }});

            // Add total row
            const totalValid = allCitations.filter(c => isValidCitation(c)).length;
            const totalInvalid = allCitations.filter(c => !isValidCitation(c)).length;

            tbody.innerHTML += `
                <tr style="background-color: #f8f9fa; font-weight: bold;">
                    <td><strong>TOTAL</strong></td>
                    <td style="color: #27ae60;">${{totalValid}}</td>
                    <td style="color: #e74c3c;">${{totalInvalid}}</td>
                    <td>${{allCitations.length}}</td>
                    <td>100.0%</td>
                </tr>
            `;
        }}

        // Search functionality
        document.getElementById('searchBox').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();

            if (searchTerm) {{
                filteredCitations = allCitations.filter(citation => {{
                    const searchText = (citation.citation_text + ' ' +
                                     citation.citation_id + ' ' +
                                     citation.source_type + ' ' +
                                     (citation.errors ? citation.errors.map(e => e.problem).join(' ') : '')).toLowerCase();
                    return searchText.includes(searchTerm);
                }});
            }} else {{
                // Re-apply current filter
                const activeBtn = document.querySelector('.filter-btn.active');
                if (activeBtn) {{
                    const filterText = activeBtn.textContent.toLowerCase().replace(' only', '');
                    if (filterText === 'all citations') {{
                        filteredCitations = [...allCitations];
                    }} else if (filterText === 'valid') {{
                        filteredCitations = allCitations.filter(c => isValidCitation(c));
                    }} else if (filterText === 'invalid') {{
                        filteredCitations = allCitations.filter(c => !isValidCitation(c));
                    }} else {{
                        filteredCitations = allCitations.filter(c => c.source_type === filterText);
                    }}
                }} else {{
                    filteredCitations = [...allCitations];
                }}
            }}

            displayCitations();
        }});

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            updateStatistics();
            displayCitations();
        }});
    </script>
</body>
</html>'''

    # Write HTML file
    with open('backend/pseo/optimization/scrpbee_dataset_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Created ScrpBee HTML report")
    print(f"📁 File: backend/pseo/optimization/scrpbee_dataset_report.html")
    print(f"📊 Total citations: {len(all_citations)} ({len(valid_citations)} valid, {len(invalid_citations)} invalid)")

def generate_error_type_breakdown(invalid_citations):
    """Generate HTML for error type breakdown"""
    error_counts = {}

    for citation in invalid_citations:
        if 'metadata' in citation and 'error_types' in citation['metadata']:
            for error_type in citation['metadata']['error_types']:
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

    if not error_counts:
        return '<p>No errors generated</p>'

    html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
    for error_type, count in sorted(error_counts.items()):
        html += f'<span style="background: #f39c12; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.9em;">{error_type}: {count}</span>'
    html += '</div>'

    return html

if __name__ == "__main__":
    create_scrpbee_html_report()