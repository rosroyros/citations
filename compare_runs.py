import json

file1 = 'Checker_Prompt_Optimization/gemini_responses_api_parallel_results.json.bak'
file2 = 'Checker_Prompt_Optimization/gemini_system_instructions_121_results.json'

with open(file1, 'r') as f:
    data1 = json.load(f)

with open(file2, 'r') as f:
    data2 = json.load(f)

results1 = data1.get('gemini-2.5-flash', {})
results2 = data2.get('results', {}) # The structure differs slightly

print(f"File 1 (Parallel) Accuracy: {results1.get('accuracy')}")
print(f"File 2 (System) Accuracy: {results2.get('accuracy')}")

# Compare details
details1 = results1.get('details', [])
details2 = results2.get('details', [])

diffs = []
for d1, d2 in zip(details1, details2):
    if d1['citation_number'] != d2['citation_number']:
        print("Mismatch in citation ordering!")
        break
    if d1['correct'] != d2['correct']:
        diffs.append(d1['citation_number'])

print(f"Number of differences in predictions: {len(diffs)}")
if diffs:
    print(f"Differing citations: {diffs}")
    
# Check metadata
print(f"\nMetadata 1: {data1.get('metadata', {}).get('test_type')}")
print(f"Metadata 2: {data2.get('metadata', {}).get('test_type')}")
