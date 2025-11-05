You are the code reviewer evaluating a completed task.

{{shell: bash -c '
TASK_ID="{{arg:1}}"

if [ -z "$TASK_ID" ]; then
    # Get first task with needs-review label
    TASK_ID=$(bd list --json 2>/dev/null | python3 -c "
import sys, json
try:
    issues = json.load(sys.stdin)
    needs_review = [i for i in issues if \"needs-review\" in i.get(\"labels\", []) and i.get(\"status\") == \"in_progress\"]
    if needs_review:
        needs_review.sort(key=lambda x: x.get(\"priority\", 2))
        print(needs_review[0][\"id\"])
except:
    pass
" 2>/dev/null)

    if [ -z "$TASK_ID" ]; then
        echo "✅ No tasks awaiting review currently."
        echo ""
        echo "To see tasks needing review: bd list --label needs-review"
        exit 0
    fi
fi

echo "🔍 Reviewing task: $TASK_ID"
echo ""
bd show "$TASK_ID"
echo ""
echo "=== CODE REVIEW CHECKLIST ==="
echo ""
echo "Security:"
echo "  ☐ No SQL injection vulnerabilities"
echo "  ☐ No XSS vulnerabilities"
echo "  ☐ No command injection"
echo "  ☐ Input validation present"
echo "  ☐ No hardcoded secrets"
echo ""
echo "Quality:"
echo "  ☐ Code follows project standards"
echo "  ☐ Clear variable/function names"
echo "  ☐ Appropriate error handling"
echo "  ☐ No unnecessary complexity"
echo ""
echo "Testing:"
echo "  ☐ Tests written and passing"
echo "  ☐ Edge cases covered"
echo "  ☐ Test coverage adequate"
echo ""
echo "Performance:"
echo "  ☐ No obvious performance issues"
echo "  ☐ Efficient algorithms used"
echo "  ☐ Database queries optimized (if applicable)"
echo ""
echo "Documentation:"
echo "  ☐ Code is self-documenting or commented"
echo "  ☐ Complex logic explained"
echo ""
echo "=== REVIEW DECISION ==="
echo ""
echo "If APPROVED (ready for deployment):"
echo "  bd label remove $TASK_ID needs-review"
echo "  bd label add $TASK_ID approved"
echo ""
echo "If CHANGES NEEDED:"
echo "  bd label remove $TASK_ID needs-review"
echo "  bd update $TASK_ID --notes \"REVIEW FEEDBACK: [specific changes needed]\""
echo ""
echo "The developer will see your feedback and make necessary changes."
'}}
