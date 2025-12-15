import subprocess
import json
import sys

def run_bd(args):
    """Run a bd command and return the JSON output if available."""
    cmd = ["bd"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return None
    return result.stdout.strip()

def create_task(title, priority=1):
    output = run_bd(["create", title, "-t", "task", "-p", str(priority), "--json"])
    if output:
        try:
            return json.loads(output)["id"]
        except json.JSONDecodeError:
            print("Failed to parse JSON")
            return None
    return None

def update_issue(issue_id, description):
    run_bd(["update", issue_id, "-d", description])

def add_dependency(from_id, to_id, dep_type="child"):
    # Usage: bd dep add FROM TO --type TYPE
    # If type is 'child', FROM is child of TO (parent).
    # If type is 'blocks', FROM blocks TO.
    run_bd(["dep", "add", from_id, to_id, "--type", dep_type])

def main():
    epic_id = "citations-fyhu"
    
    print(f"Updating Epic {epic_id}...")
    epic_desc = """## Goal
Consolidate all user status information (Pass validity, Credit balance, Free tier status) into a single, unified 'CreditDisplay' component in the header, and remove the redundant 'UserStatus' component.

## Background & Reasoning
- **Current State**: We have two components: 'CreditDisplay' (Purple text) and 'UserStatus' (Green/Grey badge). This creates duplication (e.g., both showing pass info) and visual clutter.
- **Decision**: The UserStatus component (Green badge) is redundant. The 'Free tier' badge is not critical enough to warrant a separate component.
- **Intention**: Simplify the UI by handling all states (Pass, Credits, Free) within a refined 'CreditDisplay' component. This aligns with a 'cleaner, premium' aesthetic.

## Scope
1. Refine CreditDisplay to support multi-line info (Status + Remaining).
2. Remove UserStatus component entirely.
3. Update all tests to reflect this architecture change.

## Considerations
- 'Free Tier' users will see no specific badge in the header (just standard header). This is an intentional design choice to reduce noise.
- Pass users will see 'X days left' or 'X hours left' (if < 24h) for better granularity."""
    update_issue(epic_id, epic_desc)

    print("Creating Task 1: Refine CreditDisplay...")
    task1_id = create_task("Refine CreditDisplay Component (Multi-line Support)")
    if task1_id:
        add_dependency(task1_id, epic_id, "child")
        task1_desc = """## Objective
Update 'CreditDisplay.jsx' to support a rich, multi-line layout that can display status for both Pass and Credit users.

## Requirements
- **Layout**: 'flex-col', 'items-end' (Right aligned in header).
- **Pass Users**:
  - Line 1 (Purple, Bold): '{X}-Day Pass Active'
  - Line 2 (Grey, Small): '{X} days left' (or '{X} hours left' if < 24h).
  - Logic: Use 'Math.ceil' for hours/days.
- **Credit Users**:
  - Line 1 (Purple, Bold): 'Citation Credits'
  - Line 2 (Grey, Small): '{credits} remaining'
- **Free Users**:
  - Should render nothing (or minimal) if we stick to 'hide for free'. Current plan is to return null if no token, which effectively hides it for free users.

## Implementation Details
- Use 'App.css' for '.header-status' alignment if needed.
- Ensure 'useCredits' hook provides necessary data (hours_remaining)."""
        update_issue(task1_id, task1_desc)
    else:
        print("Failed to create Task 1")
        return

    print("Creating Task 2: Remove UserStatus...")
    task2_id = create_task("Remove UserStatus Component & Cleanup")
    if task2_id:
        add_dependency(task2_id, epic_id, "child")
        
        # CORRECTED: Task 1 blocks Task 2
        print(f"Adding dependency: {task1_id} blocks {task2_id}")
        add_dependency(task1_id, task2_id, "blocks")
        
        task2_desc = """## Objective
Remove the now-redundant 'UserStatus.jsx' component and clean up references.

## Steps
1. **Delete**: 'frontend/src/components/UserStatus.jsx'.
2. **Update**: 'frontend/src/App.jsx'.
   - Remove import of UserStatus.
   - Remove usage of '<UserStatus />'.
   - Verify usage of 'userStatus' prop is no longer needed for component rendering.

## Context
UserStatus was previously used to show 'X/10 free validations' or 'Pass Active' badge. Since usage counting is internal/backend-driven and Pass info is now in CreditDisplay, this component serves no unique purpose."""
        update_issue(task2_id, task2_desc)
    else:
        print("Failed to create Task 2")
        return

    print("Creating Task 3: Update Tests...")
    task3_id = create_task("Update E2E and Unit Tests for UI Refinement")
    if task3_id:
        add_dependency(task3_id, epic_id, "child")
        
        # CORRECTED: Task 2 blocks Task 3
        print(f"Adding dependency: {task2_id} blocks {task3_id}")
        add_dependency(task2_id, task3_id, "blocks")
        
        task3_desc = """## Objective
Ensure all tests reflect the UI changes (removal of UserStatus, update of CreditDisplay text).

## Target Files
1. **'frontend/src/components/CreditDisplay.test.jsx'**:
   - Update to test new multi-line text output (e.g., 'Day Pass Active' + 'days left').
   - Test '< 24h' logic.
2. **'tests/e2e/pricing-integration.spec.js'**:
   - Update assertions to look for text in '.credit-display' only.
   - Remove any '.user-status' checks.
3. **'tests/e2e/user-access.spec.js'**:
   - Remove 'expect(.user-status).toBeVisible()' assertions.
   - Verify Credit/Pass info appears in '.credit-display'.
4. **'tests/e2e/user-status.spec.js'**:
   - **Delete file**. It was dedicated to the UserStatus component which is being verified.

## Reasoning
We must ensure no 'ghost' assertions for the deleted component remain, which would cause false negatives."""
        update_issue(task3_id, task3_desc)
    else:
        print("Failed to create Task 3")
        return

    print(f"\nSUCCESS! Created Beads structure under Epic {epic_id}:")
    print(f"- Task 1: {task1_id} (Impl)")
    print(f"- Task 2: {task2_id} (Cleanup)")
    print(f"- Task 3: {task3_id} (Tests)")
    
if __name__ == "__main__":
    main()
