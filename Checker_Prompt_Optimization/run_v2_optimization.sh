#!/bin/bash
# V2 Optimization Pipeline

set -e

echo "🚀 V2 Optimization Pipeline"
echo "Changes from V1:"
echo "  1. Proper per_class_f1 metric (from plan)"
echo "  2. Markdown italics note in signature"
echo "  3. Stratified random split for diversity"
echo "=========================================="

source ../venv/bin/activate

# Step 1: Merge with stratified split
echo ""
echo "📝 Step 1/3: Merging dataset with stratified random split"
python3 merge_and_clean_dataset_v2.py
if [ $? -ne 0 ]; then
    echo "❌ Merge failed!"
    exit 1
fi

# Step 2: GEPA Optimization
echo ""
echo "🔧 Step 2/3: Running GEPA optimization (~25 minutes)"
python3 run_gepa_optimization_v2.py 2>&1 | tee optimization_v2.log
if [ $? -ne 0 ]; then
    echo "❌ GEPA optimization failed!"
    exit 1
fi

# Step 3: Generate Report
echo ""
echo "📊 Step 3/3: Generating comparison report"
echo "(Using existing generate_html_report.py with V2 model)"

echo ""
echo "✨ V2 Pipeline Complete!"
echo "=========================================="
echo "📁 Output files:"
echo "  - optimized_output_v2/optimized_validator_v2.json"
echo "  - optimized_output_v2/optimization_metrics_v2.json"
echo "  - optimization_v2.log"
echo ""
echo "Compare with V1 results in optimized_output/"
