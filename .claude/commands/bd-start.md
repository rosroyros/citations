You are starting work on a beads issue following the beads-first workflow.

{{shell: bash -c '
TASK_ID="{{arg:1}}"

if [ -z "$TASK_ID" ]; then
    echo "❌ No task ID provided"
    echo ""
    echo "Usage: /bd-start <issue-id>"
    echo ""
    echo "Find ready work:"
    echo "  bd ready"
    echo "  bd list --status open -p 0"
    exit 1
fi

echo "=== 📋 ISSUE CONTEXT ==="
echo ""
bd show "$TASK_ID"
echo ""

echo "=== 🔗 DEPENDENCIES ==="
echo ""
bd dep tree "$TASK_ID" 2>/dev/null || echo "No dependencies"
echo ""

# Update to in_progress
bd update "$TASK_ID" --status in_progress >/dev/null 2>&1
echo "✓ Status updated to in_progress"
echo ""

echo "=== ✅ MANDATORY NEXT STEPS ==="
echo ""
echo "1. Create TodoWrite todos from requirements above"
echo "2. Identify which superpowers skills apply:"
echo "   - test-driven-development (if implementing features)"
echo "   - systematic-debugging (if fixing bugs)"
echo "   - testing-anti-patterns (when writing tests)"
echo "   - verification-before-completion (before finishing)"
echo ""

echo "=== 📝 DURING WORK ==="
echo ""
echo "Update description with progress:"
echo "  bd update $TASK_ID -d \"\$(bd show $TASK_ID --format description)"
echo ""
echo "  ## Progress - \$(date +%Y-%m-%d)"
echo "  - Implemented X"
echo "  - Discovered Y"
echo ""
echo "  ## Key Decisions"
echo "  - Chose A over B because [reasoning]"
echo "  \""
echo ""
echo "Found new bug/issue during work?"
echo "  NEW_ID=\$(bd create \"Bug: [title]\" -t bug -p 0 --json | jq -r .id)"
echo "  bd dep add \$NEW_ID $TASK_ID --type discovered-from"
echo ""

echo "=== 🏁 COMPLETING WORK ==="
echo ""
echo "1. Update description with final summary"
echo "2. Run: bd label add $TASK_ID needs-review"
echo "3. Use superpowers:requesting-code-review skill"
echo "4. After approval: bd close $TASK_ID --reason \"[summary]\""
echo "5. Run: bd sync"
echo ""
'}}
