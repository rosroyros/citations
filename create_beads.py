import subprocess
import json
import sys

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

# --- Descriptions ---

desc_epic = """## Context & Objective
We are implementing a 50/50 A/B test between our current LLM provider (OpenAI, `gpt-5-mini`) and a challenger (Gemini, `gemini-2.5-flash`). The goal is to evaluate Gemini's performance and cost-effectiveness in production without fully switching over.

## Core Architecture
- **Stickiness:** User-based stickiness via LocalStorage (persists across sessions).
- **Assignment:** Randomized 50/50 split on the client side (`model_a` vs `model_b`).
- **Data Flow:** No database schema changes. Provider info is stored in in-memory job objects and shipped via structured application logs (`app.log`) for downstream parsing.
- **Failover:** Hard requirement for graceful fallback to OpenAI if Gemini fails.

## Success Criteria
- 50% of new users are routed to Gemini.
- Users stick to their assigned provider.
- Dashboard accurately reflects which provider was used.
- Zero downtime/user-facing errors due to Gemini API issues (fallback works).
"""

desc_task1 = """## Context
We need to set up the infrastructure for Gemini validation before we can route traffic to it. This involves dependencies, configuration, and the core provider adapter.

## Requirements
1. **Dependencies:**
   - Add `google-genai` (or `google-generativeai`) to `requirements.txt`.
   - Ensure specific version compatibility if known (from tests).

2. **Configuration:**
   - Add `GEMINI_API_KEY` to `.env` (and ensure it's in production env vars).
   - Update `app.py` lifespan/startup check to verify `GEMINI_API_KEY` presence (prevent startup if missing, or log critical warning).

3. **GeminiProvider Class (`backend/providers/gemini_provider.py`):**
   - Create class implementing `CitationValidator` interface.
   - **Critical Prompt Strategy:** 
     - Use the "User Content" strategy (send prompt + citations as standard user message).
     - **DO NOT** use the `system_instruction` parameter (our tests showed ~20% accuracy vs ~79% for User Content strategy).
   - **Schema Compliance:** Ensure output matches `CitationResult` structure exactly (keys: `citation_number`, `original`, `source_type`, `errors`).
   - Implement text parsing logic (can mirror OpenAI provider's regex if applicable).

## Technical Notes
- Model: `gemini-2.5-flash`
- Reference: See `gemini_test_responses_api_parallel.py` for the working implementation pattern.
"""

desc_task2 = """## Context
Once the provider exists, the backend needs to route requests based on the client's preference and handle data storage/logging without altering the database schema.

## Requirements
1. **Routing Logic (`backend/app.py`):**
   - In `validate_citations`, extract `X-Model-Preference` header.
   - **Logic:**
     - `model_b` -> Attempt `GeminiProvider`.
     - `model_a` (or missing/invalid) -> Use `OpenAIProvider`.
   - **Fallback Mechanism (Critical):** 
     - Wrap Gemini call in try/catch. 
     - If it fails: Log error, switch to `OpenAIProvider` immediately, and mark provider as `model_a` (fallback) for that job.

2. **In-Memory Storage:**
   - When creating the `job` object in `jobs` dict, store the *actual* provider used (internal ID: `model_a` or `model_b`).
   - This ensures `/api/dashboard` (which reads `jobs`) serves the correct data immediately.

3. **Structured Logging:**
   - Emit a structured log line in `app.log` for future parsing/auditing.
   - Format: `logger.info(f"PROVIDER_SELECTION: job_id={job_id} model={internal_id} status=success fallback={bool}")`
"""

desc_task3 = """## Context
The frontend controls the assignment. We want a sticky 50/50 split that persists across sessions (LocalStorage) but uses opaque internal IDs to avoid exposing model names directly.

## Requirements
1. **Assignment Logic:**
   - Check `localStorage` for `model_preference`.
   - **If missing:**
     - Generate random assignment: `Math.random() < 0.5 ? 'model_b' : 'model_a'`.
     - `model_a` = OpenAI (Default)
     - `model_b` = Gemini (Challenger)
     - Store in `localStorage`.
   - **If present:** Use stored value.

2. **API Integration:**
   - In the API service/wrapper (validate call), append header:
   - `X-Model-Preference: <value>`

## Considerations
- We use internal IDs (`model_a`, `model_b`) so we can swap underlying models later without changing client logic/storage.
"""

desc_task4 = """## Context
The operational dashboard needs to display which provider processed a job so we can compare performance and verify the split.

## Requirements
1. **Dashboard Data Table:**
   - Add "Provider" column.
   - Map internal IDs to display names:
     - `model_a` -> "OpenAI"
     - `model_b` -> "Gemini"
     - Fallback/Unknown -> "Unknown"

2. **Job Detail Modal:**
   - Add a "Model Provider" row/field in the details view.

## Data Source
- The dashboard calls `/api/dashboard`, which returns job objects.
- Ensure the frontend reads the `provider` field added to the job object in Task 2.
"""

desc_task5 = """## Context
Before considering the task complete, we must verify the entire pipeline, especially the fallback mechanism which protects users from outages.

## Verification Steps
1. **Stickiness:** Reload page multiple times, ensure `X-Model-Preference` header remains constant.
2. **Routing:** 
   - Force header `model_a` -> Verify OpenAI used (logs).
   - Force header `model_b` -> Verify Gemini used (logs).
3. **Fallback Safety:**
   - Temporarily break Gemini config (e.g. invalid key).
   - Send `model_b` request.
   - **Expectation:** Request succeeds (via OpenAI), logs show "Fallback triggered".
4. **Dashboard:**
   - Run a job with `model_b`.
   - Verify Dashboard table shows "Gemini".
   - Verify Job Detail modal shows "Gemini".
"""

# --- Execution ---

# 1. Create Epic
epic_id = bd_create("Gemini A/B Test: Implement 50/50 Split (OpenAI vs Gemini)", desc_epic, type="epic", priority=0, labels=[])

if epic_id:
    # 2. Create Tasks
    task1_id = bd_create("Gemini A/B: Infrastructure & Provider Implementation", desc_task1, type="task", priority=1, labels=["backend"])
    task2_id = bd_create("Gemini A/B: Backend Routing, Fallback & Logging", desc_task2, type="task", priority=1, labels=["backend"])
    task3_id = bd_create("Gemini A/B: Frontend Assignment & Header Logic", desc_task3, type="task", priority=1, labels=["frontend"])
    task4_id = bd_create("Gemini A/B: Dashboard UI Updates", desc_task4, type="task", priority=1, labels=["frontend"])
    task5_id = bd_create("Gemini A/B: Verification & Testing", desc_task5, type="task", priority=1, labels=["qa"])

    # 3. Link Tasks to Epic (Epic is parent of tasks)
    # Note: bead tool specific relationship types. Assuming 'child-of' or similar if available, otherwise just organizing by logical dependency structure. 
    # Since I don't have explicit 'parent' command in the simplified tool usage I'll focus on dependencies between tasks.

    # 4. Link Dependencies (Blocks)
    # Infrastructure blocks Routing
    bd_link(task1_id, task2_id, type="blocks")
    
    # Routing and Frontend logic block Dashboard (need data to show)
    bd_link(task2_id, task4_id, type="blocks")
    
    # All impl tasks block Verification
    bd_link(task1_id, task5_id, type="blocks")
    bd_link(task2_id, task5_id, type="blocks")
    bd_link(task3_id, task5_id, type="blocks")
    bd_link(task4_id, task5_id, type="blocks")
    
    print("Beads generation complete.")
else:
    print("Failed to create Epic. Aborting.")
