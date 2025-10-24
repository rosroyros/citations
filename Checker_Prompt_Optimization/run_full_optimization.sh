#!/bin/bash
# Master script to run full optimization pipeline

set -e  # Exit on error

echo "🚀 Starting APA Citation Validator Optimization Pipeline"
echo "=========================================================="

# Activate virtual environment
source ../venv/bin/activate

# Step 1: Synthetic Expansion
echo ""
echo "📝 Step 1/5: Synthetic Expansion (generating ~5x variants per seed)"
echo "This may take 15-30 minutes with 123 seeds..."
python3 synthetic_expansion.py
if [ $? -ne 0 ]; then
    echo "❌ Synthetic expansion failed!"
    exit 1
fi

# Step 2: Merge and Clean
echo ""
echo "🧹 Step 2/5: Merging seeds + synthetics and deduplicating"
python3 merge_and_clean_dataset.py
if [ $? -ne 0 ]; then
    echo "❌ Merge and clean failed!"
    exit 1
fi

# Step 3: GEPA Optimization
echo ""
echo "🔧 Step 3/5: Running GEPA optimization (30 iterations)"
echo "This may take 30-60 minutes depending on dataset size..."
python3 run_gepa_optimization.py
if [ $? -ne 0 ]; then
    echo "❌ GEPA optimization failed!"
    exit 1
fi

# Step 4: Generate Report
echo ""
echo "📊 Step 4/5: Generating HTML report with test predictions"
python3 generate_html_report.py
if [ $? -ne 0 ]; then
    echo "❌ Report generation failed!"
    exit 1
fi

# Step 5: Summary
echo ""
echo "✨ Step 5/5: Pipeline Complete!"
echo "=========================================================="
echo "📁 Output files:"
echo "  - expanded_citations_synthetic.jsonl"
echo "  - final_merged_dataset.jsonl"
echo "  - optimized_output/optimized_validator.json"
echo "  - optimized_output/optimization_metrics.json"
echo "  - optimized_output/optimization_report.html"
echo ""
echo "🎯 Open optimization_report.html to view results!"
