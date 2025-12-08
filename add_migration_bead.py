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

desc_migration = """## Context
To display the provider information in the dashboard, the `validations` table in `validations.db` must store the provider used for each job. Although the backend (`app.py`) only logs this info, the `CitationLogParser` will parse it and needs a place to store it.

## Requirements
1. **Schema Update:**
   - Add a `provider` column (TEXT) to the `validations` table in `validations.db`.
   - Ensure the `init_db` or migration script handles existing databases (idempotent `ALTER TABLE` or check-then-add).

2. **Migration Script:**
   - Create a standalone script `scripts/migrate_provider_column.py` to apply this change to production databases.

3. **Execution Instructions:**
   - Run this script on production **before** deploying the parser changes.
   - Command: `python3 scripts/migrate_provider_column.py`

## Dependencies
- This blocks the **Dashboard UI Updates** (since they depend on the data being available).
"""

# Create the migration task
migration_id = bd_create("Gemini A/B: Database Migration (Provider Column)", desc_migration, type="task", priority=1, labels=["backend", "db"])

if migration_id:
    # Link dependencies
    # Search for dashboard task
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

    task_dashboard_id = get_id_by_title_fragment("Dashboard UI Updates")
    task_parser_id = get_id_by_title_fragment("Backend Routing") # Parser updates likely here or needs its own linkage

    if task_dashboard_id:
        bd_link(migration_id, task_dashboard_id, type="blocks")
    
    # It also logically blocks the Parser implementation part of Task 2, but Task 2 is already created.
    # We can link it to Task 2 to be safe, or just treat it as a prerequisite for the whole system working.
    if task_parser_id:
        bd_link(migration_id, task_parser_id, type="blocks")

