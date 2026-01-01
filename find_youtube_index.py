import json

with open('backend/pseo/configs/source_type_guides.json', 'r') as f:
    data = json.load(f)

for i, source in enumerate(data):
    if "YouTube" in source['title']:
        print(f"Index: {i}, Title: {source['title']}")
