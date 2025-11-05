You are the architect reviewing a blocked task and providing guidance.

{{shell: bash -c '
TASK_ID="{{arg:1}}"

if [ -z "$TASK_ID" ]; then
    # Get first blocked task
    TASK_ID=$(bd list --json 2>/dev/null | python3 -c "
import sys, json
try:
    issues = json.load(sys.stdin)
    blocked = [i for i in issues if i.get(\"status\") == \"blocked\"]
    if blocked:
        blocked.sort(key=lambda x: x.get(\"priority\", 2))
        print(blocked[0][\"id\"])
except:
    pass
" 2>/dev/null)

    if [ -z "$TASK_ID" ]; then
        echo "✅ No blocked tasks currently. All clear!"
        echo ""
        echo "To see all blocked tasks: bd list --json | jq \"[.[] | select(.status == \\\"blocked\\\")]\""
        exit 0
    fi
fi

echo "🏗️  Reviewing blocked task: $TASK_ID"
echo ""
bd show "$TASK_ID"
echo ""
echo "=== ARCHITECT GUIDANCE ==="
echo ""
echo "Review the blocking details above and provide guidance."
echo ""
echo "After providing your guidance:"
echo ""
echo "1. Update the task with your response:"
echo "   bd update $TASK_ID --notes \"ARCHITECT: [your guidance here]\""
echo ""
echo "2. Unblock the task:"
echo "   bd update $TASK_ID --status in_progress"
echo ""
echo "The developer will be notified and can continue work."
'}}
