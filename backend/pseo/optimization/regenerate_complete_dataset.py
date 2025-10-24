#!/usr/bin/env python3
"""
Regenerate complete scrpbee dataset with error injections
and create final HTML report
"""

import json
import random
import re
from datetime import datetime

class CompleteDatasetGenerator:
    def __init__(self):
        self.error_counter = 1

    def generate_errors_for_expanded_dataset(self):
        """Generate error injections for all valid citations"""

        # Load expanded valid citations
        valid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_final.jsonl"
        valid_citations = []

        with open(valid_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    valid_citations.append(json.loads(line))

        print(f"📚 Loaded {len(valid_citations)} valid citations for error injection")

        # Generate errors for all citations (1-2 errors per citation)
        all_invalid_citations = []

        for citation in valid_citations:
            # Generate 1-2 errors per citation
            num_errors = random.randint(1, 2)
            error_methods = [
                self.inject_title_case_error,
                self.inject_and_vs_ampersand_error,
                self.inject_missing_period_error,
                self.inject_missing_comma_error,
                self.inject_missing_parentheses_error,
                self.inject_italic_format_error,
                self.inject_space_error,
                self.inject_doi_format_error,
                self.inject_missing_volume_error,
                self.inject_incorrect_year_format
            ]

            # Shuffle methods for randomness
            random.shuffle(error_methods)

            for i, method in enumerate(error_methods[:num_errors]):
                try:
                    error = method(citation)
                    if error:
                        all_invalid_citations.append(error)
                        self.error_counter += 1
                except Exception as e:
                    continue

        print(f"🔧 Generated {len(all_invalid_citations)} invalid citations")

        return all_invalid_citations

    def inject_title_case_error(self, citation):
        """Convert article titles to title case"""
        text = citation['citation_text']

        # Find article title between year and journal
        match = re.search(r'\(\d{4}\)\.\s*([^._]+?)\.\s*[^,]+,', text)
        if match:
            title = match.group(1)
            if title and title[0].islower():  # Only if it's sentence case
                title_case = self.to_title_case(title)
                new_text = text.replace(title, title_case, 1)

                return self.create_invalid_citation(
                    new_text, citation['source_type'],
                    "title", "Using title case instead of sentence case",
                    f"Should be: {title}",
                    citation['citation_id'],
                    ["cap001"]
                )
        return None

    def inject_and_vs_ampersand_error(self, citation):
        """Replace '&' with 'and'"""
        text = citation['citation_text']

        if ' & ' in text:
            new_text = text.replace(' & ', ' and ')

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Using 'and' instead of '&' before final author",
                "Should use '&' in reference list",
                citation['citation_id'],
                ["auth001"]
            )
        return None

    def inject_missing_period_error(self, citation):
        """Remove period after author initial"""
        text = citation['citation_text']

        match = re.search(r'([A-Z])\.(\s*[^,]+)', text)
        if match and match.group(2).strip():
            initial = match.group(1)
            rest = match.group(2)
            new_text = text.replace(f"{initial}.{rest}", f"{initial}{rest}", 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Missing period after author initial",
                f"Should be: {initial}.",
                citation['citation_id'],
                ["punc001"]
            )
        return None

    def inject_missing_comma_error(self, citation):
        """Remove comma in author list"""
        text = citation['citation_text']

        match = re.search(r'([A-Z][a-z]+),\s*', text)
        if match:
            author = match.group(1)
            new_text = text.replace(f"{author}, ", f"{author} ", 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "authors", "Missing comma after author name",
                f"Should be: {author},",
                citation['citation_id'],
                ["punc002"]
            )
        return None

    def inject_missing_parentheses_error(self, citation):
        """Remove parentheses around year"""
        text = citation['citation_text']

        match = re.search(r'\((\d{4})\)', text)
        if match:
            year = match.group(1)
            new_text = text.replace(f"({year})", year, 1)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "publication_date", "Missing parentheses around publication year",
                f"Should be: ({year})",
                citation['citation_id'],
                ["date001"]
            )
        return None

    def inject_italic_format_error(self, citation):
        """Remove italics formatting"""
        text = citation['citation_text']

        if '_' in text:
            # Find first pair of underscores
            first_underscore = text.find('_')
            second_underscore = text.find('_', first_underscore + 1)

            if second_underscore > first_underscore:
                # Remove underscores but keep text
                new_text = text[:first_underscore] + text[first_underscore+1:second_underscore] + text[second_underscore+1:]

                return self.create_invalid_citation(
                    new_text, citation['source_type'],
                    "formatting", "Missing italics for journal/book title",
                    "Title should be italicized",
                    citation['citation_id'],
                    ["ital001"]
                )
        return None

    def inject_space_error(self, citation):
        """Add extra spaces"""
        text = citation['citation_text']

        # Add extra space after comma
        if ', ' in text:
            new_text = text.replace(', ', '  ', 1)
            if new_text != text:
                return self.create_invalid_citation(
                    new_text, citation['source_type'],
                    "spacing", "Extra spacing after comma",
                    "Remove extra space",
                    citation['citation_id'],
                    ["space001"]
                )
        return None

    def inject_doi_format_error(self, citation):
        """Convert to old DOI format"""
        text = citation['citation_text']

        match = re.search(r'https://doi\.org/([^.\s]+)', text)
        if match:
            doi = match.group(1)
            old_doi = f"http://dx.doi.org/{doi}"
            new_text = text.replace(match.group(0), old_doi)

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "doi", "Using old DOI format (dx.doi.org)",
                "Should use: https://doi.org/",
                citation['citation_id'],
                ["doi001"]
            )
        return None

    def inject_missing_volume_error(self, citation):
        """Remove volume number"""
        text = citation['citation_text']

        match = re.search(r'([^,]+),\s*(\d+)\(\d+\)', text)
        if match:
            journal = match.group(1)
            new_text = text.replace(f"{journal}, {match.group(2)}({match.group(3)})", f"{journal}({match.group(3)})")

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "publication_info", "Missing volume number",
                "Should include volume number",
                citation['citation_id'],
                ["vol001"]
            )
        return None

    def inject_incorrect_year_format(self, citation):
        """Change year format (e.g., 2020 to '20)"""
        text = citation['citation_text']

        match = re.search(r'\((\d{4})\)', text)
        if match:
            year = match.group(1)
            # Change to abbreviated format
            abbreviated = f"'{year[2:]}"
            new_text = text.replace(f"({year})", f"({abbreviated})")

            return self.create_invalid_citation(
                new_text, citation['source_type'],
                "publication_date", "Using abbreviated year format",
                f"Should be: ({year})",
                citation['citation_id'],
                ["year001"]
            )
        return None

    def to_title_case(self, text):
        """Convert to title case"""
        words = text.split()
        title_words = []
        for word in words:
            if len(word) > 1:
                title_words.append(word[0].upper() + word[1:].lower())
            else:
                title_words.append(word.upper())
        return ' '.join(title_words)

    def create_invalid_citation(self, citation_text, source_type, component, problem, correction, derived_from, error_types):
        """Create invalid citation entry"""

        return {
            "citation_text": citation_text,
            "source_type": source_type,
            "is_valid": False,
            "errors": [{
                "component": component,
                "problem": problem,
                "correction": correction
            }],
            "metadata": {
                "source": "ScrpBee Expanded Dataset",
                "section": "Error Injection",
                "date_collected": datetime.now().isoformat(),
                "verified_against_kb": False,
                "derived_from": derived_from,
                "error_injection_method": "programmatic",
                "error_types": error_types,
                "date_created": datetime.now().isoformat()
            },
            "citation_id": f"scrpbee_error_{self.error_counter:03d}"
        }

    def save_complete_dataset(self):
        """Save final complete dataset"""

        # Load valid citations
        valid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_final.jsonl"
        valid_citations = []

        with open(valid_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    valid_citations.append(json.loads(line))

        # Generate invalid citations
        invalid_citations = self.generate_errors_for_expanded_dataset()

        # Save final datasets
        final_valid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_final_valid.jsonl"
        final_invalid_file = "backend/pseo/optimization/datasets/scrpbee/scrpbee_final_invalid.jsonl"

        with open(final_valid_file, 'w', encoding='utf-8') as f:
            for citation in valid_citations:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

        with open(final_invalid_file, 'w', encoding='utf-8') as f:
            for citation in invalid_citations:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

        print(f"✅ Saved final valid citations: {final_valid_file}")
        print(f"✅ Saved final invalid citations: {final_invalid_file}")

        return valid_citations, invalid_citations

def create_final_html_report(valid_citations, invalid_citations):
    """Create final HTML report"""

    all_citations = valid_citations + invalid_citations

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrpBee Expanded Dataset - Final Report</title>
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
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .dataset-summary {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin: 30px 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
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
        .filter-buttons {{
            margin: 30px 0;
            text-align: center;
        }}
        .filter-btn {{
            background: #e74c3c;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: #c0392b;
            transform: translateY(-2px);
        }}
        .citation {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            transition: transform 0.2s;
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
        }}
        .meta-item {{
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 2px;
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
        .error-type {{
            display: inline-block;
            background: #f39c12;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 ScrpBee Expanded Dataset - Final Report</h1>

        <div class="dataset-summary">
            <h2>📊 Complete APA Citation Validation Dataset</h2>
            <p>Expanded ScrpBee dataset with multiple authoritative sources</p>
            <p><strong>Total Citations:</strong> {len(all_citations)} ({len(valid_citations)} valid + {len(invalid_citations)} invalid)</p>
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
            <div class="stat-card">
                <h3>{len(invalid_citations)}</h3>
                <p>Invalid Citations</p>
            </div>
            <div class="stat-card">
                <h3>{len(set(c['source_type'] for c in all_citations))}</h3>
                <p>Source Types</p>
            </div>
        </div>

        <h2>🔍 Search Citations</h2>
        <input type="text" class="search-box" id="searchBox" placeholder="Search by title, author, error type, or keyword...">

        <div class="filter-buttons">
            <button class="filter-btn active" onclick="filterCitations('all')">All Citations</button>
            <button class="filter-btn" onclick="filterCitations('valid')">Valid Only</button>
            <button class="filter-btn" onclick="filterCitations('invalid')">Invalid Only</button>
            <button class="filter-btn" onclick="filterCitations('journal article')">Journal Articles</button>
            <button class="filter-btn" onclick="filterCitations('book')">Books</button>
            <button class="filter-btn" onclick="filterCitations('webpage')">Webpages</button>
            <button class="filter-btn" onclick="filterCitations('other')">Other</button>
        </div>

        <h2>📚 All Citations</h2>
        <div id="citationsContainer">
            <!-- Citations will be populated by JavaScript -->
        </div>
    </div>

    <script>
        // Embed all citation data
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

            // Group by validity
            const valid = filteredCitations.filter(c => isValidCitation(c));
            const invalid = filteredCitations.filter(c => !isValidCitation(c));

            let html = '';

            if (valid.length > 0) {{
                html += '<h2 style="color: #27ae60; border-left: 4px solid #27ae60; padding-left: 15px;">✅ Valid Citations (' + valid.length + ')</h2>';
                valid.forEach(citation => {{
                    html += createCitationHTML(citation, true);
                }});
            }}

            if (invalid.length > 0) {{
                html += '<h2 style="color: #e74c3c; border-left: 4px solid #e74c3c; padding-left: 15px; margin-top: 30px;">❌ Invalid Citations (' + invalid.length + ')</h2>';
                invalid.forEach(citation => {{
                    html += createCitationHTML(citation, false);
                }});
            }}

            container.innerHTML = html;
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
                <div class="citation ${{validityClass}}">
                    <div class="citation-text">
                        ${{highlightSearchTerms(citation.citation_text)}}
                    </div>
                    <div class="citation-meta">
                        <span class="meta-item"><strong>ID:</strong> ${{citation.citation_id}}</span>
                        <span class="meta-item">${{citation.source_type}}</span>
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
            return text.replace(regex, '<span style="background-color: #fff3cd;">$1</span>');
        }}

        function filterCitations(type) {{
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            if (type === 'all') {{
                filteredCitations = [...allCitations];
            }} else if (type === 'valid') {{
                filteredCitations = allCitations.filter(c => isValidCitation(c));
            }} else if (type === 'invalid') {{
                filteredCitations = allCitations.filter(c => !isValidCitation(c));
            }} else {{
                filteredCitations = allCitations.filter(c => c.source_type === type);
            }}

            // Apply search filter
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
                filteredCitations = [...allCitations];
            }}

            displayCitations();
        }});

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            displayCitations();
        }});
    </script>
</body>
</html>'''

    with open('backend/pseo/optimization/scrpbee_final_dataset_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Created final HTML report: backend/pseo/optimization/scrpbee_final_dataset_report.html")

def main():
    """Main execution"""

    print("🔄 REGENERATING COMPLETE SCRPBEE DATASET")
    print("=" * 80)

    generator = CompleteDatasetGenerator()
    valid_citations, invalid_citations = generator.save_complete_dataset()

    print(f"\n{'='*80}")
    print("FINAL DATASET COMPLETE")
    print(f"{'='*80}")
    print(f"Valid citations: {len(valid_citations)}")
    print(f"Invalid citations: {len(invalid_citations)}")
    print(f"Total citations: {len(valid_citations) + len(invalid_citations)}")

    # Type breakdown for valid citations
    type_counts = {}
    for citation in valid_citations:
        source_type = citation['source_type']
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    print(f"\n📊 Valid citations by type:")
    for source_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {source_type:20s}: {count:2d}")

    # Error type breakdown
    error_counts = {}
    for citation in invalid_citations:
        if 'metadata' in citation and 'error_types' in citation['metadata']:
            for error_type in citation['metadata']['error_types']:
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

    print(f"\n🔧 Error types generated:")
    for error_type, count in sorted(error_counts.items()):
        print(f"   {error_type:15s}: {count:2d}")

    # Create HTML report
    create_final_html_report(valid_citations, invalid_citations)

    print(f"\n✅ FINAL SCRPBEE EXPANDED DATASET READY!")
    print(f"📁 Files created:")
    print(f"   • Valid: backend/pseo/optimization/datasets/scrpbee/scrpbee_final_valid.jsonl")
    print(f"   • Invalid: backend/pseo/optimization/datasets/scrpbee/scrpbee_final_invalid.jsonl")
    print(f"   • Report: backend/pseo/optimization/scrpbee_final_dataset_report.html")

if __name__ == "__main__":
    main()