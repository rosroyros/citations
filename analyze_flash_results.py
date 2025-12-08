
import json
import statistics

# Batch times from gemini_system_instructions_121_results.json
batch_times = [
    9.930374145507812, 10.206525087356567, 9.319518327713013, 10.654696941375732, 
    8.901821851730347, 10.067246913909912, 8.29365587234497, 9.140470027923584, 
    9.34098482131958, 9.449853897094727, 9.430094718933105, 9.790827989578247, 
    10.166550159454346, 9.30371880531311, 9.690768241882324, 9.47302794456482, 
    9.319462060928345, 8.910125017166138, 9.187959671020508, 8.714468717575073, 
    9.222092151641846, 9.939848899841309, 9.533154964447021, 10.02590298652649, 
    2.3291587829589844
]

median_time = statistics.median(batch_times)
avg_time = statistics.mean(batch_times)

print(f"Median Batch Time (5 citations): {median_time:.2f}s")
print(f"Average Batch Time: {avg_time:.2f}s")

# Analyze results
try:
    with open('Checker_Prompt_Optimization/gemini_responses_api_parallel_results.json.bak', 'r') as f:
        data = json.load(f)
        
    flash_results = data.get('gemini-2.5-flash', {})
    details = flash_results.get('details', [])
    
    total = len(details)
    correct = sum(1 for d in details if d.get('correct'))
    
    false_positives = sum(1 for d in details if d.get('predicted') is True and d.get('ground_truth') is False)
    false_negatives = sum(1 for d in details if d.get('predicted') is False and d.get('ground_truth') is True)
    
    print(f"\nModel: gemini-2.5-flash")
    print(f"Total: {total}")
    print(f"Correct: {correct} ({correct/total*100:.2f}%)")
    print(f"False Positives (Called Valid, actually Invalid): {false_positives}")
    print(f"False Negatives (Called Invalid, actually Valid): {false_negatives}")
    
except Exception as e:
    print(f"Error reading JSON: {e}")

