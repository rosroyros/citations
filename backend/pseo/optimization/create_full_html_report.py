#!/usr/bin/env python3
"""
Create standalone HTML report with ALL 65 citations embedded
"""

import json

def create_full_html_report():
    """Generate HTML with complete citation dataset"""

    # Load all citations
    citations = []
    with open('backend/pseo/optimization/datasets/valid_citations_fixed.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                citations.append(json.loads(line))

    print(f"Loading {len(citations)} citations into HTML...")

    # Convert citations to JavaScript format
    citations_js = json.dumps(citations, indent=2, ensure_ascii=False)

    # Create HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APA Citation Dataset Report - Complete (65 Citations)</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}
        .filter-buttons {{
            margin: 20px 0;
            text-align: center;
        }}
        .filter-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #2980b9;
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
        .citation-text {{
            font-size: 1.1em;
            line-height: 1.8;
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}
        .citation-meta {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            font-size: 0.9em;
            color: #6c757d;
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
        .search-box {{
            width: 100%;
            padding: 12px;
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
        .new-citation {{
            border-left: 4px solid #28a745;
        }}
        .existing-citation {{
            border-left: 4px solid #17a2b8;
        }}
        .file-info {{
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .dataset-info {{
            background: #f0f8ff;
            border: 1px solid #b0d4f1;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }}
        .dataset-info strong {{
            color: #1976d2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 APA Citation Dataset Report - Complete</h1>

        <div class="dataset-info">
            <strong>📈 Dataset Summary:</strong> 65 Total Citations | 47 from Purdue OWL | 18 Manual Entries | 7 Newly Scraped
        </div>

        <div class="file-info">
            <strong>📁 Data Source:</strong> backend/pseo/optimization/datasets/valid_citations_fixed.jsonl
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3 id="total-citations">{len(citations)}</h3>
                <p>Total Citations</p>
            </div>
            <div class="summary-card">
                <h3 id="source-count">2</h3>
                <p>Data Sources</p>
            </div>
            <div class="summary-card">
                <h3 id="type-count">6</h3>
                <p>Citation Types</p>
            </div>
            <div class="summary-card">
                <h3 id="new-count">7</h3>
                <p>Newly Scraped</p>
            </div>
        </div>

        <h2>🔍 Search & Filter</h2>
        <input type="text" class="search-box" id="searchBox" placeholder="Search citations by title, author, or keyword...">

        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterCitations('all')">All Citations</button>
            <button class="filter-btn" onclick="filterCitations('journal article')">Journal Articles</button>
            <button class="filter-btn" onclick="filterCitations('book')">Books</button>
            <button class="filter-btn" onclick="filterCitations('book chapter')">Book Chapters</button>
            <button class="filter-btn" onclick="filterCitations('webpage')">Webpages</button>
            <button class="filter-btn" onclick="filterCitations('other')">Other Sources</button>
            <button class="filter-btn" onclick="filterCitations('social media')">Social Media</button>
        </div>

        <h2>📈 Statistics</h2>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>Source Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody id="statsTableBody">
                <!-- Stats will be populated by JavaScript -->
            </tbody>
        </table>

        <h2>📚 Citations by Category</h2>
        <div id="citationsContainer">
            <p style="text-align: center; color: #6c757d;">Loading citation data...</p>
        </div>
    </div>

    <script>
        // Complete citation dataset embedded directly
        const allCitations = {citations_js};

        let filteredCitations = [...allCitations];

        function isNewCitation(citationId) {{
            return citationId.startsWith('purdue_owl_') &&
                   parseInt(citationId.split('_')[2]) >= 59;
        }}

        function displayCitations() {{
            const container = document.getElementById('citationsContainer');
            container.innerHTML = '';

            if (filteredCitations.length === 0) {{
                container.innerHTML = '<p style="text-align: center; color: #6c757d;">No citations found matching your criteria.</p>';
                return;
            }}

            // Group by source type
            const grouped = {{}};
            filteredCitations.forEach(citation => {{
                const type = citation.source_type;
                if (!grouped[type]) {{
                    grouped[type] = [];
                }}
                grouped[type].push(citation);
            }});

            // Display each group
            Object.keys(grouped).sort().forEach(type => {{
                const typeSection = document.createElement('div');
                typeSection.innerHTML = `
                    <h2>📖 ${{type.charAt(0).toUpperCase() + type.slice(1)}} (${{grouped[type].length}})</h2>
                    <div class="citations-group" data-type="${{type}}">
                        ${{grouped[type].map(citation => createCitationHTML(citation)).join('')}}
                    </div>
                `;
                container.appendChild(typeSection);
            }});
        }}

        function createCitationHTML(citation) {{
            const isNew = isNewCitation(citation.citation_id);
            const newClass = isNew ? 'new-citation' : 'existing-citation';
            const newBadge = isNew ? '<span class="meta-item" style="background: #d4edda; color: #155724;">🆕 New</span>' : '';

            return `
                <div class="citation ${{newClass}}" data-type="${{citation.source_type}}">
                    <div class="citation-text">
                        ${{highlightSearchTerms(citation.citation_text)}}
                    </div>
                    <div class="citation-meta">
                        <span class="meta-item"><strong>ID:</strong> ${{citation.citation_id}}</span>
                        <span class="meta-item source-type">${{citation.source_type}}</span>
                        <span class="meta-item">${{citation.metadata.source}}</span>
                        ${{newBadge}}
                    </div>
                </div>
            `;
        }}

        function highlightSearchTerms(text) {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            if (!searchTerm) return text;

            const regex = new RegExp(`(${{searchTerm}})`, 'gi');
            return text.replace(regex, '<span class="highlight">$1</span>');
        }}

        function filterCitations(type) {{
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Filter citations
            if (type === 'all') {{
                filteredCitations = [...allCitations];
            }} else {{
                filteredCitations = allCitations.filter(c => c.source_type === type);
            }}

            // Apply search filter if exists
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            if (searchTerm) {{
                filteredCitations = filteredCitations.filter(citation =>
                    citation.citation_text.toLowerCase().includes(searchTerm) ||
                    citation.citation_id.toLowerCase().includes(searchTerm)
                );
            }}

            displayCitations();
        }}

        function updateStatistics() {{
            // Update summary cards
            document.getElementById('total-citations').textContent = allCitations.length;

            const sources = new Set(allCitations.map(c => c.metadata.source));
            document.getElementById('source-count').textContent = sources.size;

            const types = new Set(allCitations.map(c => c.source_type));
            document.getElementById('type-count').textContent = types.size;

            const newCount = allCitations.filter(c => isNewCitation(c.citation_id)).length;
            document.getElementById('new-count').textContent = newCount;

            // Update statistics table
            const stats = {{}};
            allCitations.forEach(citation => {{
                stats[citation.source_type] = (stats[citation.source_type] || 0) + 1;
            }});

            const tbody = document.getElementById('statsTableBody');
            tbody.innerHTML = '';

            Object.keys(stats).sort().forEach(type => {{
                const count = stats[type];
                const percentage = ((count / allCitations.length) * 100).toFixed(1);

                tbody.innerHTML += `
                    <tr>
                        <td><strong>${{type.charAt(0).toUpperCase() + type.slice(1)}}</strong></td>
                        <td>${{count}}</td>
                        <td>${{percentage}}%</td>
                    </tr>
                `;
            }});
        }}

        // Search functionality
        document.getElementById('searchBox').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();

            if (searchTerm) {{
                filteredCitations = allCitations.filter(citation =>
                    citation.citation_text.toLowerCase().includes(searchTerm) ||
                    citation.citation_id.toLowerCase().includes(searchTerm) ||
                    citation.source_type.toLowerCase().includes(searchTerm)
                );
            }} else {{
                // Re-apply current filter
                const activeBtn = document.querySelector('.filter-btn.active');
                if (activeBtn && activeBtn.textContent !== 'All Citations') {{
                    filterCitations(activeBtn.textContent.toLowerCase());
                    return;
                }} else {{
                    filteredCitations = [...allCitations];
                }}
            }}

            displayCitations();
        }});

        // Load data when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            updateStatistics();
            displayCitations();
        }});
    </script>
</body>
</html>'''

    # Write complete HTML file
    with open('backend/pseo/optimization/citation_dataset_report_complete.html', 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ Created complete HTML report with {len(citations)} citations")
    print("📁 File: backend/pseo/optimization/citation_dataset_report_complete.html")

if __name__ == "__main__":
    create_full_html_report()