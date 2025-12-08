import subprocess
import json

def bd_create(title, description, type="task", priority=1, labels=None):
    cmd = ["bd", "create", title, "-d", description, "-t", type, "-p", str(priority), "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error creating issue '{title}': {result.stderr}")
        return None
    try:
        data = json.loads(result.stdout)
        issue_id = data.get("id")
        print(f"Created {type} {issue_id}: {title}")
        
        if labels:
            for label in labels:
                subprocess.run(["bd", "label", "add", issue_id, label], capture_output=True)
                
        return issue_id
    except json.JSONDecodeError:
        print(f"Failed to parse JSON for '{title}': {result.stdout}")
        return None

def bd_link(source_id, target_id, type="blocks"):
    cmd = ["bd", "dep", "add", source_id, target_id, "--type", type]
    subprocess.run(cmd, capture_output=True)
    print(f"Linked {source_id} {type} {target_id}")

desc_task_tests = """## Context
Automated tests are crucial to ensure the reliability of the new Gemini provider and the safety of the fallback mechanism.

## Requirements
1. **Unit Tests for GeminiProvider:**
   - Test `validate_citations` with mock responses (success case).
   - Test parsing logic with various Gemini output formats.
   - Test error handling (ensure it raises exceptions that the app can catch).

2. **Integration Tests for Routing/Fallback:**
   - Test the `validate_citations` endpoint with `X-Model-Preference: model_b`.
   - **Critical:** Mock a Gemini failure and verify that the response is still successful (served by OpenAI fallback) and the fallback event is logged.
   - Verify `X-Model-Preference: model_a` forces OpenAI.

3. **Frontend Tests (Optional/If feasible):**
   - Unit test for the `Math.random()` split logic (mocking localStorage).
"""

# Create the new test task
task_test_id = bd_create("Gemini A/B: Automated Unit & Integration Tests", desc_task_tests, type="task", priority=1, labels=["qa", "backend"])

if task_test_id:
    # Link it: Implementation tasks block testing, testing blocks final verification
    # Assuming previous IDs are known or we just link to the main epic if we can't look them up easily here.
    # For this script, I'll rely on the user knowing to link this to the relevant implementation tasks manually 
    # or I can fetch the recent IDs if I was running in the same session, but since I am running a new script:
    
    # I will search for the relevant tasks to link them
    def get_id_by_title_fragment(fragment):
        cmd = ["bd", "list", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            issues = json.loads(result.stdout)
            for issue in issues:
                if fragment in issue["title"]:
                    return issue["id"]
        except:
            return None
        return None

    task1_id = get_id_by_title_fragment("Infrastructure & Provider")
    task2_id = get_id_by_title_fragment("Backend Routing")
    task_verify_id = get_id_by_title_fragment("Verification & Testing")

    if task1_id:
        bd_link(task1_id, task_test_id, type="blocks")
    if task2_id:
        bd_link(task2_id, task_test_id, type="blocks")
    if task_verify_id:
        bd_link(task_test_id, task_verify_id, type="blocks")

