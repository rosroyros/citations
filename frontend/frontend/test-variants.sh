#!/bin/bash

# Script to test different gated results design variants
# Usage: ./test-variants.sh [variant]

AVAILABLE_VARIANTS=("original" "glassmorphism" "gradient" "card")

if [ $# -eq 0 ]; then
    echo "Usage: $0 [variant]"
    echo "Available variants:"
    for variant in "${AVAILABLE_VARIANTS[@]}"; do
        echo "  - $variant"
    done
    echo ""
    echo "Example: $0 glassmorphism"
    exit 1
fi

VARIANT=$1

if [[ ! " ${AVAILABLE_VARIANTS[@]} " =~ " ${VARIANT} " ]]; then
    echo "Error: Invalid variant '$VARIANT'"
    echo "Available variants: ${AVAILABLE_VARIANTS[*]}"
    exit 1
fi

echo "🎨 Testing gated results variant: $VARIANT"
echo ""
echo "Setting VITE_GATED_RESULTS_VARIANT=$VARIANT"
export VITE_GATED_RESULTS_VARIANT=$VARIANT

# Ensure gated results are enabled
echo "Setting VITE_GATED_RESULTS_ENABLED=true"
export VITE_GATED_RESULTS_ENABLED=true

echo ""
echo "🚀 Starting development server with variant: $VARIANT"
echo ""
echo "📝 Testing instructions:"
echo "1. The server will start at http://localhost:5174"
echo "2. Submit some citations to see the gated results overlay"
echo "3. The variant '$VARIANT' should be displayed"
echo "4. Press Ctrl+C to stop the server"
echo ""
echo "💡 To test other variants:"
echo "   ./test-variants.sh glassmorphism"
echo "   ./test-variants.sh gradient"
echo "   ./test-variants.sh card"
echo "   ./test-variants.sh original"
echo ""

npm run dev