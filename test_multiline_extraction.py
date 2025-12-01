#!/usr/bin/env python3
"""
Test script for the new multiline citation extraction
"""
import sys
import re
sys.path.append('/Users/roy/Documents/Projects/citations')

from dashboard.log_parser import extract_citations_to_validate_multiline

# Sample log data from production (actual format from logs)
test_log_lines = [
    "2025-11-28 11:56:27 - openai_provider - DEBUG - openai_provider.py:45 - Citations to validate: Chen, H., Yu, J., & Li, W.-X. (2023). Non-conventional peptides in plants: From gene regulation to crop improvement. _The Crop Journal_, _11_(2), 323–331. https://doi.org/10.1016/j.cj.2022.10.006",
    "Chowdhary, N. A., & Songachan, L. S. (2025). Plant Peptides Involved in ROS Signalling and Biotic and Abiotic Stress Responses. _International Journal of Peptide Research and Therapeutics_, _31_(3), 53. https://doi.org/10.1007/s10989-025-10711-4",
    "Couzigou, J.-M., Lauressergues, D., Bécard, G., & Combier, J.-P. (2015). miRNA-encoded peptides (miPEPs): A new tool to analyze the roles of miRNAs in plant biology. _RNA Biology_, _12_(11), 1178–1180. https://doi.org/10.1080/15476286.2015.1094601",
    "De Araújo, P. M., & Grativol, C. (2022). In silico identification of candidate miRNA-encoded Peptides in four Fabaceae species. _Computational Biology and Chemistry_, _97_, 107644. https://doi.org/10.1016/j.compbiolchem.2022.107644",
    "Erokhina, T. N., Ryazantsev, D. Y., Zavriev, S. K., & Morozov, S. Y. (2023). Regulatory miPEP Open Reading Frames Contained in the Primary Transcripts of microRNAs. _International Journal of Molecular Sciences_, _24_(3), 2114. https://doi.org/10.3390/ijms24032114",
    "2025-11-28 11:56:27 - prompt_manager - DEBUG - prompt_manager.py:126 - Building full prompt"
]

print("Testing multiline citation extraction...")
result = extract_citations_to_validate_multiline(test_log_lines, 0)

if result:
    citations_text, was_truncated = result
    print(f"✅ Successfully extracted {len(citations_text)} characters")
    print(f"Truncated: {was_truncated}")
    print("\nExtracted text preview:")
    print("=" * 50)
    print(citations_text[:500] + "..." if len(citations_text) > 500 else citations_text)
    print("=" * 50)

    # Count citations (each citation starts with Author, Y. format)
    lines = citations_text.split('\n')
    citation_count = 0
    for line in lines:
        line = line.strip()
        if line and re.match(r'^[A-Z][a-z]+, [A-Z]\.', line):  # Pattern like "Chen, H."
            citation_count += 1

    print(f"\nFound {citation_count} individual citations")
    print("\nFirst few lines:")
    for i, line in enumerate(lines[:8]):
        print(f"{i+1:2d}: {line}")
    if len(lines) > 8:
        print(f"... and {len(lines) - 8} more lines")
else:
    print("❌ Failed to extract citations")