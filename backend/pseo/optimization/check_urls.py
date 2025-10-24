#!/usr/bin/env python3
import json
from pathlib import Path

valid_file = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')
with open(valid_file) as f:
    valid_citations = [json.loads(line) for line in f]

without_url = [c for c in valid_citations if not c.get('metadata', {}).get('url')]
print(f'Valid citations - Total: {len(valid_citations)}, Without URL: {len(without_url)}')
for c in without_url[:5]:
    print(f"  ID: {c.get('citation_id')}, source_type: {c.get('source_type')}")

invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')
with open(invalid_file) as f:
    invalid_citations = [json.loads(line) for line in f]

without_url_inv = [c for c in invalid_citations if not c.get('metadata', {}).get('url')]
print(f'\nInvalid citations - Total: {len(invalid_citations)}, Without URL: {len(without_url_inv)}')
for c in without_url_inv[:5]:
    print(f"  ID: {c.get('citation_id')}, source_type: {c.get('source_type')}")
