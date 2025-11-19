#!/bin/bash
# Monitor consistency test progress

while true; do
    clear
    echo "========================================="
    echo "Consistency Test Progress Monitor"
    echo "========================================="
    echo ""

    for model in "gpt-5-mini" "gpt-4o-mini"; do
        echo "Model: $model"
        for run in 1 2 3; do
            file="Checker_Prompt_Optimization/consistency_test_${model}_run_${run}.jsonl"
            if [ -f "$file" ]; then
                count=$(wc -l < "$file")
                echo "  Run $run: $count/121 citations"
            else
                echo "  Run $run: Not started"
            fi
        done
        echo ""
    done

    echo "Summary file:"
    if [ -f "Checker_Prompt_Optimization/consistency_test_summary.json" ]; then
        echo "  ✅ Complete!"
    else
        echo "  ⏳ In progress..."
    fi

    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo ""

    sleep 10
done
