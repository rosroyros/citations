You are starting development work on a task from the bd issue tracker.

{{shell: bash -c '
TASK_ID="{{arg:1}}"

if [ -z "$TASK_ID" ]; then
    # Get first open task
    TASK_ID=$(bd list --json 2>/dev/null | python3 -c '\''import sys, json; issues = json.load(sys.stdin); open_issues = [i for i in issues if i.get("status") == "open"]; print(sorted(open_issues, key=lambda x: x.get("priority", 2))[0]["id"]) if open_issues else ""'\'' 2>/dev/null)

    if [ -z "$TASK_ID" ]; then
        echo "❌ No open tasks available. Check \"bd list\" for current work."
        exit 1
    fi
fi

# Update to in_progress
bd update "$TASK_ID" --status in_progress >/dev/null 2>&1

# Show the task
echo "📋 Starting work on: $TASK_ID"
echo ""
bd show "$TASK_ID"
echo ""
echo "=== IMPLEMENTATION WORKFLOW ==="
echo ""
echo "1. Write tests first (TDD)"
echo "2. Implement until tests pass"
echo "3. Verify in logs/output"
echo ""
echo "=== IF YOU GET STUCK ==="
echo ""
echo "STOP immediately and mark as blocked:"
echo ""
echo "  bd update $TASK_ID --status blocked --notes \"BLOCKER:"
echo "  - ATTEMPTED: [what you tried]"
echo "  - QUESTION: [specific question]"
echo "  - CONTEXT: [file:line references]\""
echo ""
echo "Then run: /architect"
echo ""
echo "DO NOT continue without architect guidance."
echo ""
echo "=== WHEN COMPLETE ==="
echo ""
echo "Before marking for review, ensure:"
echo ""
echo "✓ All tests passing (python3 -m pytest)"
echo "✓ Implementation working as expected"
echo "✓ Code follows project standards"
echo ""
echo "Document your changes in notes:"
echo ""
echo "  bd update $TASK_ID --notes \"CHANGES: [files modified, what was implemented, design decisions]"
echo ""
echo "  TESTING: [tests written/run, results/logs]"
echo ""
echo "  CONCERNS: [areas needing scrutiny, trade-offs, performance/security]\""
echo ""
echo "Mark for review:"
echo ""
echo "  bd label add $TASK_ID needs-review"
echo ""
echo "The reviewer will be notified automatically."
'}}
