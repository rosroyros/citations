You are deploying a reviewed and approved task to production.

{{shell: bash -c '
TASK_ID="{{arg:1}}"

if [ -z "$TASK_ID" ]; then
    # Get first approved task
    TASK_ID=$(bd list --json 2>/dev/null | python3 -c "
import sys, json
try:
    issues = json.load(sys.stdin)
    approved = [i for i in issues if \"approved\" in i.get(\"labels\", []) and i.get(\"status\") == \"in_progress\"]
    if approved:
        approved.sort(key=lambda x: x.get(\"priority\", 2))
        print(approved[0][\"id\"])
except:
    pass
" 2>/dev/null)

    if [ -z "$TASK_ID" ]; then
        echo "✅ No approved tasks ready for deployment."
        echo ""
        echo "To see approved tasks: bd list --label approved"
        exit 0
    fi
fi

echo "🚀 Deploying task: $TASK_ID"
echo ""
bd show "$TASK_ID"
echo ""
echo "=== DEPLOYMENT CHECKLIST ==="
echo ""
echo "Before deploying, verify:"
echo "  ☐ All tests passing locally"
echo "  ☐ Code changes committed"
echo "  ☐ .beads/issues.jsonl updated with latest task state"
echo ""
echo "=== DEPLOYMENT STEPS ==="
echo ""
echo "1. Ensure tests pass:"
echo "   python3 -m pytest"
echo ""
echo "2. Commit all changes (including .beads/issues.jsonl):"
echo "   git add ."
echo "   git commit -m \"feat: [description from task $TASK_ID]\""
echo ""
echo "3. Push to GitHub:"
echo "   git push origin main"
echo ""
echo "4. Deploy to production:"
echo "   ssh deploy@178.156.161.140"
echo "   cd /opt/citations && ./deployment/scripts/deploy.sh"
echo ""
echo "5. After successful deployment, close the task:"
echo "   bd label remove $TASK_ID approved"
echo "   bd close $TASK_ID --reason \"Deployed to production\""
echo ""
echo "=== VERIFICATION ==="
echo ""
echo "After deployment:"
echo "  ☐ Check backend service: systemctl status citations-backend"
echo "  ☐ Check frontend is updated"
echo "  ☐ Test the deployed feature"
echo "  ☐ Monitor logs for errors"
'}}
