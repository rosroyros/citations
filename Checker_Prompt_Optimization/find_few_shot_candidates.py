import json
import re

DATASET_PATH = "Checker_Prompt_Optimization/expanded_citations_synthetic.jsonl"
TEST_SET_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"

def load_test_set_citations():
    """Load the test set citations to ensure we don't pick them."""
    test_citations = set()
    with open(TEST_SET_PATH, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    test_citations.add(data['citation'].strip())
                except:
                    pass
    return test_citations

def find_candidates():
    test_citations = load_test_set_citations()
    print(f"Loaded {len(test_citations)} test citations to avoid.")
    
    candidates = {
        "social_media": [],
        "illustrator_translator": [],
        "dsm": [],
        "dictionary": [],
        "editors": []
    }
    
    with open(DATASET_PATH, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    # Only look for VALID citations
                    if not data.get('is_valid', False): 
                        continue
                        
                    citation = data.get('citation', '').strip()
                    
                    # Skip if it's in the test set
                    if citation in test_citations:
                        continue
                        
                    # Categorize
                    if ('[Video]' in citation or 'YouTube' in citation or 'Instagram' in citation or 'Twitter' in citation or 'Tweet' in citation) and len(candidates['social_media']) < 3:
                        candidates['social_media'].append(citation)
                    
                    elif ('Illus.' in citation or 'Trans.' in citation) and len(candidates['illustrator_translator']) < 3:
                        candidates['illustrator_translator'].append(citation)
                        
                    elif 'Diagnostic and statistical manual' in citation and len(candidates['dsm']) < 3:
                        candidates['dsm'].append(citation)
                        
                    elif 'Dictionary' in citation or 'dictionary' in citation and len(candidates['dictionary']) < 3:
                        candidates['dictionary'].append(citation)
                        
                    elif '(Eds.)' in citation and len(candidates['editors']) < 3:
                        candidates['editors'].append(citation)
                        
                except Exception as e:
                    continue

    print("\n--- CANDIDATE FEW-SHOT EXAMPLES (Not in Test Set) ---")
    for category, items in candidates.items():
        print(f"\nCategory: {category.upper()}")
        for item in items:
            print(f"- {item}")

if __name__ == "__main__":
    find_candidates()
